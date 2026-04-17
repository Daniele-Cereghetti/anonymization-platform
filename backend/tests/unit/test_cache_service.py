"""
Unit tests for CacheService (TTL and LRU eviction).

Uses pytest tmp_path to isolate the filesystem.
"""

import time
from unittest.mock import patch

from app.services.cache_service import CacheService


def _make_service(tmp_path, max_disk_mb=500, ttl_seconds=604_800):
    """Create a CacheService backed by a temporary directory."""
    with patch("app.services.cache_service.CACHE_DIR", str(tmp_path)), \
         patch("app.services.cache_service.CACHE_MAX_DISK_MB", max_disk_mb), \
         patch("app.services.cache_service.CACHE_TTL_SECONDS", ttl_seconds):
        return CacheService()


class TestStoreAndGet:
    def test_round_trip(self, tmp_path):
        svc = _make_service(tmp_path)
        doc_id = svc.store("# Hello")

        assert svc.get(doc_id) == "# Hello"

    def test_get_missing_returns_none(self, tmp_path):
        svc = _make_service(tmp_path)

        assert svc.get("nonexistent-id") is None


class TestTTL:
    def test_expired_document_returns_none(self, tmp_path):
        svc = _make_service(tmp_path, ttl_seconds=60)
        doc_id = svc.store("expired content")

        # Simulate time passing beyond TTL
        with patch("app.services.cache_service.time") as mock_time:
            mock_time.time.return_value = time.time() + 120
            result = svc.get(doc_id)

        assert result is None

    def test_fresh_document_returned(self, tmp_path):
        svc = _make_service(tmp_path, ttl_seconds=60)
        doc_id = svc.store("fresh content")

        # Still within TTL
        with patch("app.services.cache_service.time") as mock_time:
            mock_time.time.return_value = time.time() + 30
            result = svc.get(doc_id)

        assert result == "fresh content"


class TestLRUEviction:
    def test_oldest_entry_evicted_when_over_limit(self, tmp_path):
        # 1 byte max — forces eviction after every store
        svc = _make_service(tmp_path, max_disk_mb=0)

        with patch("app.services.cache_service.CACHE_MAX_DISK_MB", 0):
            # Patch at the module level so _evict_if_needed sees max_bytes = 0
            svc._cache_dir = tmp_path
            svc._metadata_path = tmp_path / "metadata.json"

            doc1 = svc.store("first")
            doc2 = svc.store("second")

        # The first document should have been evicted
        assert svc.get(doc1) is None
        assert svc.get(doc2) == "second"
