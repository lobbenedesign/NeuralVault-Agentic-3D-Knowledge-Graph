"""
neuralvault.utils.loaders
──────────────────────────
Ingegneri di ingestione dei dati (Connectors).
Implementa caricamento intelligente di PDF, Markdown e Word, 
mantenendo la gerarchia semantica.
"""

from __future__ import annotations
from typing import Any, Iterator, Callable, Protocol, Optional
import os
import uuid
import re
from pathlib import Path

# Schema per il caricamento
from index.node import VaultNode

class DocumentLoader(Protocol):
    """Protocollo per i caricatori di documenti."""
    def load(self, file_path: str | Path) -> str:
        """Legge il file e restituisce il testo grezzo."""
        ...

class PDFLoader:
    """Implementa caricamento PDF con pypdf."""
    def load(self, file_path: str | Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("Installa pypdf: pip install pypdf")

        reader = PdfReader(file_path)
        text   = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text

class DocxLoader:
    """Implementa caricamento Word con python-docx."""
    def load(self, file_path: str | Path) -> str:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("Installa python-docx: pip install python-docx")

        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

class MarkdownLoader:
    """Implementa caricamento Markdown (testo semplice)."""
    def load(self, file_path: str | Path) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

class SemanticChunker:
    """
    Divide un documento in chunk intelligenti basati su paragrafi e simboli
    mantenendo un overlap configurabile.
    """
    def __init__(
        self, 
        chunk_size: int = 1000, 
        overlap:    int = 200,
        separator:  str = "\n\n"
    ):
        self.chunk_size = chunk_size
        self.overlap    = overlap
        self.separator  = separator

    def split_text(self, text: str) -> list[str]:
        # Pulizia base
        text = re.sub(r' +', ' ', text)
        
        # Divisione per separatore primario
        paragraphs = text.split(self.separator)
        chunks     = []
        current    = ""

        for p in paragraphs:
            if len(current) + len(p) < self.chunk_size:
                current += p + self.separator
            else:
                if current:
                    chunks.append(current.strip())
                # Sliding window overlap
                words   = current.split()
                current = " ".join(words[-max(1, self.overlap // 8):]) + " " + p + self.separator
        
        if current:
            chunks.append(current.strip())
        return chunks

class IngestionManager:
    """
    Gestore dell'ingestione massiva. Coordina loader e chunker per alimentare NeuralVault.
    """
    def __init__(self, embedder_fn: Callable):
        self.embedder_fn = embedder_fn
        self.chunker     = SemanticChunker()
        self.loaders: dict[str, DocumentLoader] = {
            ".pdf":  PDFLoader(),
            ".docx": DocxLoader(),
            ".md":   MarkdownLoader(),
            ".txt":  MarkdownLoader(),
        }

    def process_file(self, file_path: str | Path) -> list[VaultNode]:
        """Carica un singolo file, lo chunk-izza e restituisce i nodi."""
        p    = Path(file_path)
        ext  = p.suffix.lower()
        
        if ext not in self.loaders:
            print(f"Skipping unsupported file: {p.name}")
            return []

        loader = self.loaders[ext]
        text   = loader.load(p)
        chunks = self.chunker.split_text(text)

        nodes = []
        for i, chunk_text in enumerate(chunks):
            # Inseriamo nel metadata il riferimento al file sorgente
            meta = {
                "source":      p.name,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "extension":   ext
            }
            
            # Creiamo il nodo — l'engine si occuperà dell'embedding
            # Se vogliamo pre-calcolarli:
            vec = self.embedder_fn(chunk_text)
            
            node = VaultNode(
                id=f"{p.stem}_chunk_{i}",
                text=chunk_text,
                vector=vec,
                metadata=meta,
                collection="default_ingested"
            )
            nodes.append(node)
        
        return nodes

    def process_directory(self, directory: str | Path) -> list[VaultNode]:
        """Ingestione ricorsiva di un'intera cartella."""
        all_nodes = []
        for root, _, files in os.walk(directory):
            for file in files:
                fpath = Path(root) / file
                all_nodes.extend(self.process_file(fpath))
        return all_nodes
