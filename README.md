# Anonymization Platform

Piattaforma di Anonimizzazione Documenti tramite IA Generativa Locale
SUPSI — Anno Accademico 2025/2026

---

## Prerequisiti

- [Docker](https://www.docker.com/get-started) installato e funzionante
- Python 3.9 o superiore
- pip

---

## 1. Avviare Ollama con Docker

```bash
# Scarica l'immagine e avvia il container (prima volta)
docker run -d -v ollama_data:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

Per avviarlo nelle sessioni successive (container già esistente):

```bash
docker start ollama
```

Verifica che sia attivo:

```bash
docker ps   # deve mostrare il container "ollama"
```

---

## 2. Scaricare il modello LLM

```bash
docker exec -it ollama ollama pull llama3.1:8b
```

> Il download richiede ~5 GB. Viene eseguito una sola volta; il modello viene salvato nel volume `ollama_data`.

Per verificare i modelli disponibili:

```bash
docker exec -it ollama ollama list
```

---

## 3. Installare le dipendenze Python

### Opzione A — solo `requests` (nessuna dipendenza extra)

```bash
pip install requests
```

### Opzione B — client ufficiale Ollama (consigliata)

```bash
pip install requests ollama
```

### Opzione C — virtual environment (best practice)

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# oppure: .venv\Scripts\activate  # Windows

pip install requests ollama
```

---

## 4. Eseguire il backend di test

```bash
python backend/main.py
```

Lo script esegue tre test:

| Test | Descrizione |
|------|-------------|
| `test_with_requests` | Chiamata REST diretta all'API `/api/generate` |
| `test_chat_format` | Chiamata con ruoli `system`/`user` all'API `/api/chat` |
| `test_with_ollama_client` | Utilizzo del client Python ufficiale `ollama` |

Output atteso:

```
Piattaforma Anonimizzazione - Test connessione LLM locale
Modello: llama3.1:8b
Endpoint: http://localhost:11434

============================================================
TEST 1: Chiamata con requests
============================================================
Ollama raggiungibile. Modelli disponibili:
  - llama3.1:8b (...)
...
```

---

## 5. Frontend

Apri `frontend/index.html` direttamente nel browser (nessun server richiesto).

---

## Configurazione

| Parametro | Valore predefinito | File |
|-----------|--------------------|------|
| URL Ollama | `http://localhost:11434` | `backend/main.py` |
| Modello | `llama3.1:8b` | `backend/main.py` |

Per cambiare modello, modifica la variabile `MODEL_NAME` in `backend/main.py` con uno dei modelli disponibili (es. `llama3.2:3b`, `mistral:7b`).

---

## Risoluzione problemi

**Ollama non raggiungibile (`ConnectionError`)**
```bash
docker start ollama          # avvia il container se è fermo
docker logs ollama           # controlla i log per errori
```

**Modello non trovato**
```bash
docker exec -it ollama ollama list          # verifica i modelli installati
docker exec -it ollama ollama pull llama3.1:8b   # riscarica se mancante
```

**Risposta lenta**
I modelli su CPU sono più lenti. `llama3.1:8b` richiede ~8 GB di RAM. In alternativa usa un modello più leggero:
```bash
docker exec -it ollama ollama pull llama3.2:3b
```
e aggiorna `MODEL_NAME = "llama3.2:3b"` in `backend/main.py`.
