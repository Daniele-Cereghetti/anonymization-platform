import os

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "360"))

CACHE_DIR: str = os.getenv("CACHE_DIR", "/tmp/anon_cache")
CACHE_MAX_DISK_MB: int = int(os.getenv("CACHE_MAX_DISK_MB", "500"))
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", str(7 * 24 * 3600)))

AUDIT_LOG_PATH: str = os.getenv("AUDIT_LOG_PATH", "logs/audit.log")
