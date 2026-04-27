"""
retrieval/web_forager.py — [v1.0.0 Sovereign Web Forager]
──────────────────────────────────────────────────────────
Modulo di Web Foraging completo per NeuralVault.

Capacità:
1. Fetch HTTP con fallback Playwright per pagine JS-rendered.
2. HTML Parsing e pulizia del testo con BeautifulSoup.
3. Crawling ricorsivo di sottopagine con depth controllata.
4. OCR su immagini (<img>) e PDF tramite pytesseract + pdfminer.
5. Estrazione strutturata: titolo, meta-description, headings, testo, link.
6. Rate limiting e deduplicazione URL.
7. Output pronto per ingestione in NeuralVault (lista di Dict con text+metadata).
"""

from __future__ import annotations

import re
import time
import hashlib
import asyncio
from urllib.parse import urljoin, urlparse, urldefrag
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from utils.backpressure import backpressure

# ── Dipendenze core ───────────────────────────────────────────────
import httpx

# ── Dipendenze opzionali (graceful degradation) ───────────────────
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️ [Forager] beautifulsoup4 non installata. HTML parsing limitato.")

try:
    import playwright.async_api as pw
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    import pytesseract
    from PIL import Image
    import io
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    import io as _io
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


@dataclass
class ForagedPage:
    """Rappresenta una pagina web estratta e pulita."""
    url: str
    title: str
    text: str
    headings: List[str] = field(default_factory=list)
    description: str = ""
    links: List[str] = field(default_factory=list)
    depth: int = 0
    fetch_time: float = field(default_factory=time.time)
    status_code: int = 200
    content_type: str = "text/html"
    images: List[str] = field(default_factory=list) # Raw image URLs
    images_ocr: List[str] = field(default_factory=list)

    def to_chunks(self) -> List[Dict]:
        """
        Trasforma la pagina in chunk pronti per upsert_text().
        Crea chunk separati per heading/sezione quando il testo è lungo.
        """
        chunks = []
        base_meta = {
            "source": self.url,
            "origin": "web_forager",
            "title": self.title,
            "description": self.description,
            "depth": self.depth,
            "fetch_time": self.fetch_time,
        }

        # Chunk principale (testo completo se breve, altrimenti headline + intro)
        if len(self.text) <= 1500:
            chunks.append({"text": f"{self.title}\n\n{self.text}", "metadata": {**base_meta, "chunk": "full"}})
        else:
            # Spezziamo su paragrafi doppi
            paragraphs = [p.strip() for p in self.text.split("\n\n") if len(p.strip()) > 40]
            for i, para in enumerate(paragraphs[:50]):  # Max 50 chunk per pagina
                chunks.append({
                    "text": para,
                    "metadata": {**base_meta, "chunk": f"p{i}"}
                })

        # Chunk OCR da immagini (se presenti)
        for j, ocr_text in enumerate(self.images_ocr):
            if len(ocr_text.strip()) > 30:
                chunks.append({
                    "text": f"[OCR da immagine] {ocr_text}",
                    "metadata": {**base_meta, "chunk": f"ocr_{j}", "type": "ocr"}
                })

        return chunks


class SovereignWebForager:
    """
    Motore di Web Foraging Sovrano per NeuralVault.
    Trasforma qualsiasi URL in conoscenza strutturata pronta per l'ingestione.
    """

    def __init__(
        self,
        max_depth: int = 12,
        max_pages: int = 25000,
        rate_limit_sec: float = 0.2,
        same_domain_only: bool = True,
        timeout_sec: float = 20.0,
        use_playwright: bool = False,
    ):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.rate_limit = rate_limit_sec
        self.same_domain_only = same_domain_only
        self.timeout = timeout_sec
        self.use_playwright = use_playwright and HAS_PLAYWRIGHT

        self._visited: Set[str] = set()
        self.proposals: List[Dict] = [] # Argomenti per approfondimento esterno
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_sec),
            headers={"User-Agent": "NeuralVault-Forager/1.0 (compatible; Sovereign Knowledge Engine)"},
            follow_redirects=True,
        )

    def _normalize_url(self, url: str) -> str:
        url, _ = urldefrag(url)
        return url.rstrip("/")

    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Filtro Sovrano: Valida URL e previene l'ingestione di 'Useless Info' (Indici, Archivi, Search)."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            
            # 1. Check Dominio
            if self.same_domain_only:
                target = parsed.netloc.lower()
                base = base_domain.lower()
                base_clean = base.replace("www.", "")
                if not (target == base or target.endswith(f".{base_clean}") or target == base_clean):
                    return False
            
            # 2. Blacklist 'Useless Info' (v1.0.5)
            # Evitiamo indici alfabetici, pagine di ricerca, tag clouds e archivi piatti
            blacklist = ["/genindex", "/search", "/tag/", "/archive", "/category/", "/contents.html", "google-search", "?s=", "&s="]
            if any(p in url.lower() for p in blacklist):
                return False

            # 3. Check Estensioni spazzatura
            if any(url.lower().endswith(ext) for ext in [".zip", ".pdf", ".docx", ".exe", ".bin"]):
                return False
            
            return True
        except Exception:
            return False

    async def _parse_html(self, html: str, url: str) -> ForagedPage:
        if not HAS_BS4:
            return ForagedPage(url=url, title="Unknown (BS4 Missing)", text=html[:5000])

        soup = BeautifulSoup(html, "html.parser")
        
        # 🔗 Estrazione link PRIMA della decomposizione (v1.0.2 Fix Stall)
        links = []
        for a in soup.find_all("a", href=True):
            links.append(urljoin(url, a["href"]))

        # Selettori CSS da ignorare (Pubblicità, Navigazione, Legal, etc.)
        ad_selectors = ["footer", "nav", "aside", ".ads", ".banner", ".sidebar", ".cookie", ".social", ".menu", ".breadcrumb", "script", "style", "iframe", "header"]
        for selector in ad_selectors:
            for element in soup.select(selector):
                element.decompose()

        main_content = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.find(class_="body") or soup.body
        if main_content:
            # Preserva struttura paragrafo ed elenchi
            for tag in main_content.find_all(["p", "li", "h1", "h2", "h3", "h4", "blockquote", "td", "th"]):
                tag.string = "\n" + tag.get_text(separator=" ", strip=True) + "\n"
            raw_text = main_content.get_text(separator="\n")
        else:
            raw_text = soup.get_text(separator="\n")

        # Pulizia aggressiva del testo e rimozione frammenti troppo brevi (noise)
        lines = [line.strip() for line in raw_text.splitlines()]
        lines = [line for line in lines if len(line) > 15]
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        # Estrazione metadati
        title = (soup.title.string if soup.title else "Untitled Page").strip()
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "").strip()
        
        headings = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3"])]

        # Creazione pagina foraggiata con limiti sovrani (50k char)
        return ForagedPage(
            url=url,
            title=title,
            text=text[:50000],
            headings=headings,
            description=description,
            links=links,
            images=[urljoin(url, img["src"]) for img in soup.find_all("img", src=True)]
        )

    async def _ocr_images(self, soup: "BeautifulSoup", base_url: str) -> List[str]:
        """Esegue OCR sulle immagini reali della pagina, filtrando icone e loghi."""
        if not HAS_OCR:
            return []

        ocr_results = []
        # Cerchiamo solo immagini coerenti (almeno 100px di larghezza potenziale)
        images = soup.find_all("img", src=True)
        valid_images = []
        for img in images:
            src = img["src"].lower()
            # Heuristic per evitare pubblicità/icone
            if any(x in src for x in ["icon", "logo", "banner", "adserver", "pixel", "tracker", "sprite"]):
                continue
            valid_images.append(img)

        for img in valid_images[:15]: # Limite per efficienza
            img_url = urljoin(base_url, img["src"])
            try:
                # Tentativo di recupero metadati (alt text) come fallback prima di OCR pesante
                alt_text = img.get("alt", "").strip()
                if len(alt_text) > 40:
                    ocr_results.append(f"[ALT-TAG]: {alt_text}")
                    continue

                resp = await self._client.get(img_url, timeout=5.0)
                if "image" in resp.headers.get("content-type", ""):
                    pil_img = Image.open(io.BytesIO(resp.content))
                    # Check dimensioni minime per evitare noise
                    if pil_img.width < 100 or pil_img.height < 100:
                        continue
                    text = pytesseract.image_to_string(pil_img, lang="ita+eng")
                    if len(text.strip()) > 20:
                        ocr_results.append(text.strip())
            except Exception:
                pass

        return ocr_results

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTTP con fallback Playwright per SPA/JS-rendered."""
        try:
            # 🛡️ Browser-like headers to avoid being blocked by WAFs
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.google.com/",
                "Cache-Control": "max-age=0",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
            }
            
            # Use a fresh client with verify=False to ignore SSL errors which are common on some domains
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout, follow_redirects=True, verify=False) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    ct = resp.headers.get("content-type", "").lower()
                    if "html" in ct:
                        return resp.text
                    elif "pdf" in ct and HAS_PDF:
                        return self._extract_pdf(resp.content)
                else:
                    print(f"⚠️ [Forager] HTTP {resp.status_code} per {url}. Tentativo fallback...")
            
            # Fallback immediato a Playwright se il primo tentativo fallisce o non è 200
            if HAS_PLAYWRIGHT:
                print(f"🎭 [Forager] Avvio Fallback Playwright per {url[:50]}...")
                return await self._fetch_with_playwright(url)
            return None

        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            err_msg = f"{type(e).__name__}: {str(e)}"
            print(f"⚠️ [Forager] Fetch HTTP fallito per {url}: {err_msg}. Provo Playwright...")
            
            # Fallback: Playwright per pagine JS-rendered o protette
            if HAS_PLAYWRIGHT:
                return await self._fetch_with_playwright(url)
            return None

    def _extract_pdf(self, content: bytes) -> str:
        """Estrae testo da PDF."""
        if not HAS_PDF:
            return ""
        try:
            text = pdf_extract_text(_io.BytesIO(content))
            return text[:50000] if text else ""
        except Exception:
            return ""

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fallback con Playwright per contenuti JS-rendered (React, Vue, etc.)."""
        if not HAS_PLAYWRIGHT:
            return None
        try:
            async with pw.async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=int(self.timeout * 1000))
                await page.wait_for_load_state("networkidle", timeout=10000)
                html = await page.content()
                await browser.close()
                return html
        except Exception as e:
            print(f"⚠️ [Forager] Playwright fallito per {url}: {e}")
            return None

    async def forage(self, start_url: str):
        """
        Punto di ingresso principale.
        Crawla l'URL di partenza e le sue sottopagine fino a max_depth.
        Yields ForagedPage real-time.
        """
        start_url = self._normalize_url(start_url)
        base_domain = urlparse(start_url).netloc

        self.queue: List[tuple[str, int]] = [(start_url, 0)]  # (url, depth)
        self._visited.clear()

        print(f"🕸️ [Forager] Avvio forage: {start_url} (max_depth={self.max_depth}, max_pages={self.max_pages})")
        
        pages_count = 0
        try:
            while self.queue and pages_count < self.max_pages:
                url, depth = self.queue.pop(0)
                norm_url = self._normalize_url(url)

                if norm_url in self._visited:
                    continue
                
                # --- BACKPRESSURE PROTOCOL (Gap #2) ---
                throttle = backpressure.get_throttle_factor()
                if throttle < 0.2:
                    await backpressure.async_wait_if_clogged()
                elif throttle < 0.5:
                    print(f"⏳ [Backpressure] Throttling forager (factor: {throttle:.2f})...")
                    await asyncio.sleep(2.0 * (1.1 - throttle))
                
                self._visited.add(norm_url)

                # Telemetria in tempo reale: Calcolo progresso
                current_idx = pages_count + 1
                progress_pct = (current_idx / self.max_pages) * 100 if self.max_pages > 0 else 0
                
                print(f"📄 [Forager] [{current_idx}/{self.max_pages}] {progress_pct:.1f}% | Memoria Synaptica: {url[:60]}...")

                html = await self._fetch_page(url)
                if not html:
                    continue

                page = await self._parse_html(html, url)
                page.depth = depth

                pages_count += 1
                yield page

                # Aggiungi link validi alla coda (solo se non al massimo depth)
                if depth < self.max_depth:
                    for link in page.links:
                        norm_link = self._normalize_url(link)
                        if (norm_link not in self._visited
                                and self._is_valid_url(link, base_domain)
                                and len(self.queue) < self.max_pages * 3):
                            self.queue.append((link, depth + 1))

                # Rate limiting cortese
                await asyncio.sleep(self.rate_limit)
        finally:
            await self._client.aclose()
            print(f"✅ [Forager] Completato: {pages_count} pagine estratte da {base_domain}")

    def forage_sync(self, start_url: str) -> List[ForagedPage]:
        """Versione sincrona per utilizzo da script Python."""
        async def _collect():
            return [p async for p in self.forage(start_url)]
        return asyncio.run(_collect())


def forage_to_chunks(
    start_url: str,
    max_depth: int = 2,
    max_pages: int = 20,
    same_domain_only: bool = True,
    use_playwright: bool = False,
) -> List[Dict]:
    """
    Funzione di alto livello: dato un URL restituisce tutti i chunk
    pronti per vault.upsert_text().

    Esempio:
        chunks = forage_to_chunks("https://docs.mysite.com", max_depth=2)
        for c in chunks:
            vault.upsert_text(c["text"], metadata=c["metadata"])
    """
    forager = SovereignWebForager(
        max_depth=max_depth,
        max_pages=max_pages,
        same_domain_only=same_domain_only,
        use_playwright=use_playwright,
    )
    pages = forager.forage_sync(start_url)
    all_chunks = []
    for page in pages:
        all_chunks.extend(page.to_chunks())
    return all_chunks
