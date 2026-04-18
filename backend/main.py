"""
Anonymization Platform - Backend
SUPSI - Anno Accademico 2025/2026

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload

Docs:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import anonymize, convert, extract
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL

from app.infrastructure.llm.ollama_client import OllamaClient, OllamaError

client = OllamaClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    if client.model not in client.available_models():
        success = client.pull_model()
        if not success:
            raise OllamaError("Impossibile scaricare il modello")

    if not client.is_available():
        raise OllamaError("Ollama backend is not available at startup.")

    yield  # <-- l'app gira mentre siamo qui

    # shutdown
    # (non c'è nulla da fare al momento)

app = FastAPI(
    title="Anonymization Platform API",
    description="API per l'anonimizzazione di documenti tramite IA generativa locale (Ollama).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(convert.router, prefix="/api", tags=["convert"])
app.include_router(extract.router, prefix="/api", tags=["extract"])
app.include_router(anonymize.router, prefix="/api", tags=["anonymize"])


@app.get("/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "llm_backend": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL,
    }
