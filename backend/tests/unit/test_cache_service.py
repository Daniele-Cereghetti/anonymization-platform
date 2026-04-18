"""
Unit tests for CacheService (TTL and LRU eviction).

Uses pytest tmp_path to isolate the filesystem.
"""

import time
from unittest.mock import patch

import app.services.cache_service as _mod
from app.services.cache_service import CacheService


def _make_service(tmp_path):
    """Create a CacheService backed by a temporary directory."""
    with patch.object(_mod, "CACHE_DIR", str(tmp_path)):
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
        with patch.object(_mod, "CACHE_DIR", str(tmp_path)), \
             patch.object(_mod, "CACHE_TTL_SECONDS", 60):
            svc = CacheService()
            doc_id = svc.store("expired content")

            # Simulate time passing beyond TTL
            with patch.object(_mod, "time") as mock_time:
                mock_time.time.return_value = time.time() + 120
                result = svc.get(doc_id)

            assert result is None

    def test_fresh_document_returned(self, tmp_path):
        with patch.object(_mod, "CACHE_DIR", str(tmp_path)), \
             patch.object(_mod, "CACHE_TTL_SECONDS", 60):
            svc = CacheService()
            doc_id = svc.store("fresh content")

            # Still within TTL
            with patch.object(_mod, "time") as mock_time:
                mock_time.time.return_value = time.time() + 30
                result = svc.get(doc_id)

            assert result == "fresh content"


class TestLRUEviction:
    def test_oldest_entry_evicted_when_over_limit(self, tmp_path):
        # ~10 bytes threshold — enough for one small doc, not two
        with patch.object(_mod, "CACHE_DIR", str(tmp_path)), \
             patch.object(_mod, "CACHE_MAX_DISK_MB", 10 / (1024 * 1024)):
            svc = CacheService()

            doc1 = svc.store("aaaaaaaa")  # 8 bytes — fits
            doc2 = svc.store("bbbbbbbb")  # 8 more — total 16 > 10, evicts doc1

        assert svc.get(doc1) is None
        assert svc.get(doc2) == "bbbbbbbb"
