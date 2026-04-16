document.getElementById('send-btn').addEventListener('click', async () => {
    const text = document.getElementById('quick-note').value;
    if (!text) return;

    try {
        const response = await fetch("http://localhost:8001/api/upload_text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: text,
                metadata: { origin: "quick_note", timestamp: new Date().toISOString() }
            })
        });
        
        if (response.ok) {
            document.getElementById('quick-note').value = "";
            alert("Synapsed successfully!");
        }
    } catch (err) {
        alert("Failed to connect to NeuralVault. Is the API running?");
    }
});
