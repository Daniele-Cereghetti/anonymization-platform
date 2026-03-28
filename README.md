# Anonymization Platform

Piattaforma di Anonimizzazione Documenti tramite IA Generativa Locale
SUPSI — Anno Accademico 2025/2026

---

## Prerequisiti

- [Docker](https://www.docker.com/get-started) installato e funzionante
- Python 3.10 o superiore

---

## 1. Avviare Ollama con Docker

```bash
# Prima volta — scarica l'immagine e avvia il container
docker run -d -v ollama_data:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

Nelle sessioni successive (container già esistente):

```bash
docker start ollama
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

Il venv va creato **dentro `backend/`**. Il file `backend/.venv/` è già nel `.gitignore`.

```bash
cd backend/
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# oppure: .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

Dopo l'installazione, scarica il modello NLP per il Modulo Identificazione (Presidio/spaCy):

```bash
python -m spacy download en_core_web_sm
```

Opzionale — aggiunge supporto NER nativo per l'italiano:

```bash
python -m spacy download it_core_news_sm
```

> Se i modelli spaCy non sono installati, il sistema funziona comunque in modalità
> **LLM-only**: Presidio verrà disabilitato automaticamente e tutta la rilevazione
> delle entità verrà gestita dall'LLM.

---

## 4. Avviare il backend

```bash
cd backend/
source .venv/bin/activate
uvicorn main:app --reload
```

Il server sarà disponibile su `http://localhost:8000`.
La documentazione interattiva (Swagger UI) è accessibile su `http://localhost:8000/docs`.

### Endpoint API

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/health` | Stato del servizio e configurazione LLM |
| `POST` | `/api/convert` | Upload file (`.md`, `.txt`) → testo Markdown |
| `POST` | `/api/extract` | Pipeline di estrazione: NER ibrido + ruoli semantici |
| `POST` | `/api/anonymize` | Sostituzione entità validate con label semantiche |

---

## 5. Eseguire i test sul dataset

Sono disponibili due runner:

| Runner            | Descrizione                                                                    |
|-------------------|--------------------------------------------------------------------------------|
| `runner`          | Pipeline completa: Presidio/spaCy + LLM + ruoli semantici + anonimizzazione    |
| `runner_ner_only` | Solo Presidio/spaCy - utile per valutare la copertura del layer NER senza LLM  |

### Pipeline completa

```bash
cd backend/
source .venv/bin/activate
python -m tests.dataset_tests.runner
```

### Solo NER (Presidio/spaCy, senza LLM)

```bash
python -m tests.dataset_tests.runner_ner_only
```

### Filtrare per gruppo di documenti

Entrambi i runner accettano l'opzione `--group` (o `-g`) per eseguire solo i documenti
il cui nome inizia con il prefisso specificato:

```bash
# Solo i documenti del gruppo 01
python -m tests.dataset_tests.runner --group 01
python -m tests.dataset_tests.runner_ner_only -g 01

# Funziona con qualsiasi prefisso
python -m tests.dataset_tests.runner -g CV
```

### Output e opzioni

```bash
# Sopprime le tabelle intermedie per documento (mostra solo il riepilogo finale)
ANON_VERBOSE=0 python -m tests.dataset_tests.runner
```

I risultati del runner completo vengono salvati in `backend/tests/dataset_tests/results/`:

```
results/
├── 20260327T120000Z_01_CV_IT.json        # risultato per documento
├── 20260327T120000Z_02_CV_EN.json
├── ...
└── 20260327T120000Z_SUMMARY.json         # riepilogo dell'intera run
```

Ogni file JSON contiene: timestamp, modello usato, sorgente delle entità (`ner` / `llm` / `merged`),
ruolo semantico assegnato, tempi di elaborazione e anteprima del documento anonimizzato.
Il `SUMMARY.json` aggrega i conteggi per categoria su tutti i documenti.

---

## 6. Frontend

Apri `frontend/index.html` direttamente nel browser (nessun server richiesto).
Il frontend si aspetta il backend in ascolto su `http://localhost:8000`.

---

## Architettura della pipeline `/extract`

```
documento markdown
       │
       ▼
┌──────────────────────────────────────┐
│  Modulo Identificazione              │
│  ┌───────────────────────────────┐   │
│  │ Presidio + spaCy (NER rules)  │──►│ pattern-based: email, IBAN,
│  └───────────────────────────────┘   │ telefono, codice fiscale, ecc.
│  ┌───────────────────────────────┐   │
│  │ LLM NER (llm_ner_service)     │──►│ semantico, multilingua (IT/EN/FR/DE)
│  └───────────────────────────────┘   │
│          merge (LLM priorità)         │
└──────────────────────────────────────┘
       │  entities con source = "ner" | "llm" | "merged"
       ▼
┌──────────────────────────────────────┐
│  Modulo Ruoli Semantici              │
│  LLM assegna ruolo contestuale a     │
│  persone_fisiche / persone_giuridiche│
└──────────────────────────────────────┘
       │  entities con semantic_role
       ▼
    ExtractionResult
```

### Sostituzioni prodotte da `/anonymize`

| Categoria | Con ruolo semantico | Senza ruolo (fallback) |
| --- | --- | --- |
| `persone_fisiche` | `fornitore1`, `paziente1` | `persona1` |
| `persone_giuridiche` | `azienda_fornitrice1`, `banca1` | `organizzazione1` |
| `dati_contatto` | — | `[EMAIL_1]`, `[TELEFONO_1]`, `[INDIRIZZO_1]` |
| `identificativi` | — | `[CODICE_FISCALE_1]`, `[AVS_1]`, `[PASSAPORTO_1]` |
| `dati_finanziari` | — | `[IBAN_1]`, `[CARTA_1]` |
| `dati_temporali` | — | `[DATA_NASCITA_1]`, `[DATA_1]` |

---

## Struttura del progetto

```
anonymization-platform/
├── backend/
│   ├── .venv/                           # virtual environment (non committato)
│   ├── app/
│   │   ├── config.py                    # variabili di configurazione (env override)
│   │   ├── domain/
│   │   │   ├── entities.py              # EntityCategory, Entity, AnonymizationMapping
│   │   │   └── document.py              # ExtractionResult, AnonymizationResult
│   │   ├── infrastructure/
│   │   │   ├── llm/ollama_client.py     # client HTTP verso Ollama
│   │   │   └── storage/file_handler.py  # lettura/scrittura file
│   │   ├── services/
│   │   │   ├── conversion_service.py    # conversione file → Markdown
│   │   │   ├── identification_service.py # Modulo Identificazione (Presidio + LLM)
│   │   │   ├── llm_ner_service.py       # NER semantico via LLM
│   │   │   ├── semantic_role_service.py  # Modulo Ruoli Semantici
│   │   │   ├── extraction_service.py    # orchestrazione dei due moduli
│   │   │   └── anonymization_service.py # sostituzione con label semantiche
│   │   └── api/routes/
│   │       ├── convert.py
│   │       ├── extract.py
│   │       └── anonymize.py
│   ├── tests/dataset_tests/
│   │   ├── runner.py                    # test runner sui documenti reali
│   │   └── results/                     # risultati tracciati (JSON, non committati)
│   ├── requirements.txt
│   └── main.py                          # entry point FastAPI
├── dataset/                             # 10 documenti multilingua (IT, EN, FR, DE)
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
└── docs/
```

---

## Configurazione

Le variabili di configurazione possono essere sovrascritte tramite variabili d'ambiente:

| Variabile | Valore predefinito | Descrizione |
|-----------|--------------------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Endpoint Ollama |
| `OLLAMA_MODEL` | `llama3.1:8b` | Modello LLM da utilizzare |
| `OLLAMA_TIMEOUT` | `120` | Timeout richieste LLM (secondi) |

Esempio con modello alternativo:

```bash
OLLAMA_MODEL=llama3.2:3b uvicorn main:app --reload
```

---

## Risoluzione problemi

### Ollama non raggiungibile

```bash
docker start ollama
docker logs ollama
```

### Modello LLM non trovato

```bash
docker exec -it ollama ollama list
docker exec -it ollama ollama pull llama3.1:8b
```

### Risposta lenta

`llama3.1:8b` richiede ~8 GB di RAM. In alternativa usa un modello più leggero:

```bash
docker exec -it ollama ollama pull llama3.2:3b
OLLAMA_MODEL=llama3.2:3b uvicorn main:app --reload
```

### Presidio/spaCy non disponibile

Il sistema funziona comunque in modalità LLM-only. Per abilitare Presidio:

```bash
cd backend/
source .venv/bin/activate
python -m spacy download en_core_web_sm
```
