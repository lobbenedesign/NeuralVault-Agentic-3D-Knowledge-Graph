#!/bin/bash

# NeuralVault Production Deployment Script
# Compila il core Rust e installa tutte le dipendenze in un ambiente isolato.

echo "🔱 NEURALVAULT — AVVIO DEPLOY PRODUZIONE (ICLR 2026 EDITION)"
echo "------------------------------------------------------------"

# 1. Verifica Python 3.9+
python3 --version | grep -q "Python 3.[9-12]" || { echo "❌ Errore: Richiesto Python 3.9+"; exit 1; }

# 2. Crea ambiente virtuale (consigliato per evitare conflitti)
if [ ! -d "venv" ]; then
    echo "📦 Creazione ambiente virtuale..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Upgrade pip & build tools
echo "⚙️ Upgrade pip, setuptools and build tools..."
pip install --upgrade pip setuptools wheel maturin

# 4. Installa le dipendenze complete (testo, immagini, SQL, distribuito)
echo "📚 Installazione dipendenze AI & Performance..."
pip install -r REQUIREMENTS_FULL.txt

# 5. Compila il core performante in Rust
echo "🦀 Compilazione Core Rust Performance (neuralvault_rs)..."
cd neuralvault_rs/
maturin develop --release # Installa il modulo direttamente nel venv
if [ $? -eq 0 ]; then
    echo "✅ Core Rust compilato con successo (Release Mode: On)"
else
    echo "❌ Errore nella compilazione Rust. Verifica di avere 'cargo' installato."
    exit 1
fi
cd ..

# 6. Verifica finale
echo "🔱 NeuralVault Engine boot check..."
python3 -c "import neuralvault; print('NeuralVault Engine: ONLINE (Ver. 0.1.2)')"

echo "------------------------------------------------------------"
echo "🚀 DEPLOY COMPLETATO."
echo "Usa 'python3 dashboard.py' per vedere il sistema in azione."
