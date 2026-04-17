import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ..config import AUDIT_LOG_PATH


def compute_file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def log_event(event: str, document_id: str, **kwargs) -> None:
    """Append a single JSON-Lines audit entry.

    Never log document content, entity values, or anonymization mappings.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "document_id": document_id,
        **kwargs,
    }

    path = Path(AUDIT_LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
