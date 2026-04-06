import json
import time
import uuid
from pathlib import Path
from typing import Optional

from ..config import CACHE_DIR, CACHE_MAX_DISK_MB, CACHE_TTL_SECONDS

_METADATA_FILE = "metadata.json"


class CacheService:
    def __init__(self) -> None:
        self._cache_dir = Path(CACHE_DIR)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self._cache_dir / _METADATA_FILE

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, markdown: str) -> str:
        """Persist *markdown* to disk and return the new document_id."""
        document_id = str(uuid.uuid4())
        (self._cache_dir / f"{document_id}.md").write_text(markdown, encoding="utf-8")

        metadata = self._load_metadata()
        now = time.time()
        metadata[document_id] = {
            "created_at": now,
            "last_accessed": now,
            "size": len(markdown.encode("utf-8")),
        }
        self._evict_if_needed(metadata)
        self._save_metadata(metadata)
        return document_id

    def get(self, document_id: str) -> Optional[str]:
        """Return cached markdown for *document_id*, or None if missing/expired."""
        content_path = self._cache_dir / f"{document_id}.md"
        if not content_path.exists():
            return None

        metadata = self._load_metadata()
        entry = metadata.get(document_id)
        if entry is None:
            return None

        if time.time() - entry["created_at"] > CACHE_TTL_SECONDS:
            self._delete_entry(document_id, metadata)
            self._save_metadata(metadata)
            return None

        entry["last_accessed"] = time.time()
        self._save_metadata(metadata)
        return content_path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_metadata(self) -> dict:
        if self._metadata_path.exists():
            try:
                return json.loads(self._metadata_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_metadata(self, metadata: dict) -> None:
        self._metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def _delete_entry(self, document_id: str, metadata: dict) -> None:
        (self._cache_dir / f"{document_id}.md").unlink(missing_ok=True)
        metadata.pop(document_id, None)

    def _evict_if_needed(self, metadata: dict) -> None:
        """LRU eviction: remove least-recently-used entries until under the disk threshold."""
        max_bytes = CACHE_MAX_DISK_MB * 1024 * 1024
        total = sum(e["size"] for e in metadata.values())
        if total <= max_bytes:
            return

        sorted_entries = sorted(metadata.items(), key=lambda x: x[1]["last_accessed"])
        for doc_id, entry in sorted_entries:
            if total <= max_bytes:
                break
            total -= entry["size"]
            self._delete_entry(doc_id, metadata)
