// Aura Bridge | Service Worker — v2.0 (Fixed)
const VAULT_KEY = "vault_secret_aura_2026";

chrome.runtime.onInstalled.addListener(() => {
    // Menu 1: Synapse testo selezionato
    chrome.contextMenus.create({
        id: "synapse-to-vault",
        title: "🧬 Synapse selection to NeuralVault",
        contexts: ["selection"]
    });
    // Menu 2: Forage intera pagina (crawling completo)
    chrome.contextMenus.create({
        id: "forage-url",
        title: "🕸️ Forage entire page to NeuralVault",
        contexts: ["page"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "synapse-to-vault") {
        const text = info.selectionText || tab.title;
        synapseText(text, tab.url);
    } else if (info.menuItemId === "forage-url") {
        forageUrl(tab.url);
    }
});

// Invia testo selezionato come nodo rapido
async function synapseText(text, url) {
    try {
        const response = await fetch("http://localhost:8001/api/upload_text", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-KEY": VAULT_KEY
            },
            body: JSON.stringify({
                text: text,
                metadata: {
                    source: url,
                    origin: "browser_extension",
                    type: "selection",
                    timestamp: new Date().toISOString()
                }
            })
        });
        const result = await response.json();
        console.log("Synapse successful:", result);
        // Feedback visivo sull'icona
        chrome.action.setBadgeText({ text: "✓" });
        chrome.action.setBadgeBackgroundColor({ color: "#4ade80" });
        setTimeout(() => chrome.action.setBadgeText({ text: "" }), 2000);
    } catch (err) {
        console.error("Synapse failed. Is NeuralVault running on port 8001?", err);
        chrome.action.setBadgeText({ text: "!" });
        chrome.action.setBadgeBackgroundColor({ color: "#ef4444" });
        setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
    }
}

// Avvia crawling completo dell'URL corrente
async function forageUrl(url) {
    try {
        const response = await fetch("http://localhost:8001/api/forage", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-KEY": VAULT_KEY
            },
            body: JSON.stringify({
                url: url,
                max_depth: 1,
                max_pages: 10,
                same_domain_only: true
            })
        });
        const result = await response.json();
        console.log("Forage started:", result);
        chrome.action.setBadgeText({ text: "↓" });
        chrome.action.setBadgeBackgroundColor({ color: "#a855f7" });
        setTimeout(() => chrome.action.setBadgeText({ text: "" }), 4000);
    } catch (err) {
        console.error("Forage failed. Is NeuralVault running on port 8001?", err);
    }
}
