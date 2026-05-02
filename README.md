# Anonymization Platform

Document Anonymization Platform via Local Generative AI
SUPSI — Semester Project C11149 — Academic Year 2025/2026

All inference (LLM and NER) runs **locally**: no data leaves the machine.

---

## Quickstart (Docker)

The fastest way to try out the platform. Only requires [Docker](https://www.docker.com/get-started).

### 1. Start Ollama and download the LLM model

```bash
docker run -d -v ollama_data:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.1:8b
```

> The pull downloads about 5 GB and runs only once (the model is kept in the `ollama_data` volume).

In subsequent sessions just run `docker start ollama`.

### 2. Build the backend and start the stack

```bash
cd backend
docker build -t anon-platform-backend .
cd ..
docker compose up
```

(For older Docker versions: `docker-compose`.)

The stack exposes:
- **Frontend** → `http://localhost:8080` (served by Nginx)
- **Backend (API + Swagger)** → `http://localhost:8000` ([Swagger UI](http://localhost:8000/docs))

To stop the stack: `docker compose down`.

---

## Quickstart (local development, without Docker for the backend)

Useful for editing backend code with auto-reload.

### Prerequisites
- Docker (for Ollama)
- Python 3.10+

### 1. Start Ollama (see above)

### 2. Python backend

The virtual environment must be created **inside `backend/`** (`backend/.venv/` is already in `.gitignore`).

```bash
cd backend/
python3 -m venv .venv
source .venv/bin/activate           # macOS/Linux
# .venv\Scripts\activate            # Windows

pip install -r requirements.txt
```

### 3. (Optional) spaCy models for the hybrid NER layer

The Identification module combines **Presidio + spaCy** (pattern-based: email, IBAN, phone numbers, fiscal codes, …) with **semantic NER via LLM**. To enable the Presidio layer download at least one spaCy model:

```bash
python -m spacy download it_core_news_sm   # Italian (recommended)
python -m spacy download en_core_web_sm    # English
python -m spacy download fr_core_news_sm   # French
python -m spacy download de_core_news_sm   # German
```

The document language is detected automatically with `lingua-language-detector` and the corresponding spaCy model is selected. If the model for the detected language is not installed, the first available one is used as a fallback.

> Without any spaCy model the system still works in **LLM-only** mode: Presidio is disabled and all detection goes through the LLM.

### 4. Start the backend

```bash
cd backend/
source .venv/bin/activate
uvicorn main:app --reload
```

API on `http://localhost:8000`, Swagger UI on `http://localhost:8000/docs`.

### 5. Frontend

Open `frontend/index.html` directly in your browser (no server required). The frontend expects the backend on `http://localhost:8000`.

Alternatively, serve it via Docker together with the rest of the stack (`docker compose up`).

---

## Using the platform

The user flow is in three stages (see also the labels in the UI):

1. **Ingestion and Normalization** — upload of the source document; the file is parsed (text, layout, tables) and converted to canonical Markdown.
2. **Entity Recognition and Validation (NER)** — selection of the categories to detect, execution of recognition, manual validation (accept/discard) of every proposed placeholder.
3. **Substitution and Redaction** — application of the approved placeholders to the original text; once finished the substitution map is deleted from the process memory (irreversible operation).

### Supported document formats

The backend accepts: `.md`, `.txt`, `.pdf`, `.docx`, `.pptx`, `.html`, `.htm` (see `conversion_service.py`).

> The frontend selector also shows `.doc`, `.rtf`, `.odt` but these formats are **not** supported by the backend: uploading them will be rejected.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Service status + LLM configuration (`status`, `llm_backend`, `model`) |
| `POST` | `/api/convert` | File upload → normalized Markdown |
| `POST` | `/api/extract` | Extraction pipeline: hybrid NER (Presidio + LLM) + semantic roles |
| `POST` | `/api/anonymize` | Substitution of validated entities with semantic placeholders |

Full reference (requests/responses): `http://localhost:8000/docs`.

---

## `/extract` pipeline architecture

```
markdown document
       │
       ▼
┌──────────────────────────────────────┐
│  Identification Module               │
│  ┌───────────────────────────────┐   │
│  │ Presidio + spaCy (NER rules)  │──►│ pattern-based: email, IBAN,
│  └───────────────────────────────┘   │ phone, fiscal code, etc.
│  ┌───────────────────────────────┐   │
│  │ LLM NER (llm_ner_service)     │──►│ semantic, multilingual (IT/EN/FR/DE)
│  └───────────────────────────────┘   │
│          merge (LLM priority)        │
└──────────────────────────────────────┘
       │  entities with source = "ner" | "llm" | "merged"
       ▼
┌──────────────────────────────────────┐
│  Semantic Roles Module               │
│  LLM assigns contextual role to      │
│  persone_fisiche / persone_giuridiche│
└──────────────────────────────────────┘
       │  entities with semantic_role
       ▼
    ExtractionResult
```

### Placeholders produced by `/anonymize`

| Category | With semantic role | Without role (fallback) |
| --- | --- | --- |
| `persone_fisiche` | `[CANDIDATO_1]`, `[PAZIENTE_1]`, … | `[PERSONA_1]` |
| `persone_giuridiche` | `[AZIENDA_FORNITRICE_1]`, `[BANCA_1]`, … | `[ORGANIZZAZIONE_1]` |
| `dati_contatto` | — | `[EMAIL_1]`, `[TELEFONO_1]`, `[INDIRIZZO_1]` |
| `identificativi` | — | `[CODICE_FISCALE_1]`, `[AVS_1]`, `[PASSAPORTO_1]` |
| `dati_finanziari` | — | `[IBAN_1]`, `[CARTA_1]` |
| `dati_temporali` | — | `[DATA_NASCITA_1]`, `[DATA_1]` |

Labels are **localized** based on the document language (e.g. `[CANDIDATE_1]` in EN, `[CANDIDAT_1]` in FR, `[KANDIDAT_1]` in DE).

---

## Configuration

Environment variables (read by `backend/app/config.py`):

| Variable | Default | Description |
|-----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.1:8b` | LLM model used |
| `OLLAMA_TIMEOUT` | `360` | LLM request timeout (seconds) |
| `CACHE_DIR` | `/tmp/anon_cache` | Cache directory for converted documents |
| `CACHE_MAX_DISK_MB` | `500` | LRU eviction threshold (MB) |
| `CACHE_TTL_SECONDS` | `604800` | Cache entry TTL (7 days) |
| `AUDIT_LOG_PATH` | `logs/audit.log` | Audit log path |

Example with an alternative model:

```bash
OLLAMA_MODEL=llama3.2:1b uvicorn main:app --reload
```

---

## Dataset tests

Two runners are available:

| Runner            | Description |
|-------------------|-------------|
| `runner`          | Full pipeline: Presidio/spaCy + LLM + semantic roles + anonymization |
| `runner_ner_only` | Presidio/spaCy only — useful to evaluate the NER layer coverage without LLM |

### Full pipeline

```bash
cd backend/
source .venv/bin/activate
python -m tests.dataset_tests.runner
```

### NER only (Presidio/spaCy, without LLM)

```bash
python -m tests.dataset_tests.runner_ner_only
```

### Filter by document group

Both runners accept `--group` (or `-g`) to process only documents whose name starts with the given prefix:

```bash
python -m tests.dataset_tests.runner --group 01
python -m tests.dataset_tests.runner_ner_only -g 01
python -m tests.dataset_tests.runner -g CV
```

### Output and options

```bash
# Suppress per-document intermediate tables (only show final summary)
ANON_VERBOSE=0 python -m tests.dataset_tests.runner
```

Results are saved in `backend/tests/dataset_tests/results/`:

```
results/
├── 20260327T120000Z_01_CV_IT.json        # per-document result
├── 20260327T120000Z_02_CV_EN.json
├── ...
└── 20260327T120000Z_SUMMARY.json         # summary of the whole run
```

Each file contains: timestamp, model used, entity source (`ner` / `llm` / `merged`), assigned semantic role, processing times, preview of the anonymized document. The `SUMMARY.json` aggregates counts by category across all documents.

---

## Project structure

```
anonymization-platform/
├── backend/
│   ├── .venv/                            # virtual environment (not committed)
│   ├── app/
│   │   ├── config.py                     # configuration variables (env override)
│   │   ├── domain/
│   │   │   ├── entities.py               # EntityCategory, Entity, AnonymizationMapping
│   │   │   └── document.py               # ExtractionResult, AnonymizationResult
│   │   ├── infrastructure/
│   │   │   ├── llm/ollama_client.py      # HTTP client to Ollama
│   │   │   └── storage/file_handler.py   # file read/write
│   │   ├── services/
│   │   │   ├── conversion_service.py     # file parsing → Markdown (Docling + plain text)
│   │   │   ├── identification_service.py # Identification module (Presidio + LLM)
│   │   │   ├── llm_ner_service.py        # semantic NER via LLM
│   │   │   ├── semantic_role_service.py  # Semantic Roles module
│   │   │   ├── extraction_service.py     # orchestration of the two modules
│   │   │   └── anonymization_service.py  # substitution with semantic labels
│   │   └── api/routes/
│   │       ├── convert.py
│   │       ├── extract.py
│   │       └── anonymize.py
│   ├── tests/dataset_tests/
│   │   ├── runner.py                     # full pipeline runner
│   │   ├── runner_ner_only.py            # NER-only runner
│   │   └── results/                      # tracked results (JSON, not committed)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py                           # FastAPI entry point
├── dataset/                              # multilingual documents (IT, EN, FR, DE)
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docker-compose.yml
└── docs/
```

---

## Troubleshooting

### Ollama not reachable

```bash
docker start ollama
docker logs ollama
```

### LLM model not found

```bash
docker exec -it ollama ollama list
docker exec -it ollama ollama pull llama3.1:8b
```

### Slow response

`llama3.1:8b` requires ~8 GB of RAM. Alternatively, use a lighter model:

```bash
docker exec -it ollama ollama pull llama3.2:3b
OLLAMA_MODEL=llama3.2:3b uvicorn main:app --reload
```

### Presidio/spaCy unavailable

The system still works in LLM-only mode. To enable Presidio install at least one spaCy model (Italian recommended):

```bash
cd backend/
source .venv/bin/activate
python -m spacy download it_core_news_sm
```
