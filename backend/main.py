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

from app.api.routes import anonymize, convert, extract
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL

app = FastAPI(
    title="Anonymization Platform API",
    description="API per l'anonimizzazione di documenti tramite IA generativa locale (Ollama).",
    version="0.1.0",
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
