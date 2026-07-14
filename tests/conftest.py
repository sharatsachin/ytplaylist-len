"""Shared pytest fixtures and environment defaults for offline unit tests."""

import os

from dotenv import load_dotenv

load_dotenv()

# Must be set before any src module that reads Redis/Mongo env at import time.
os.environ.setdefault("APIS", "test-api-key")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/15")
os.environ.setdefault("MONGO_URL", "mongodb://127.0.0.1:27017")

import pytest

from src.itemlist import ItemList
from tests.youtube_fixtures import fetch_uploads_playlist_id


def pytest_addoption(parser):
    parser.addoption(
        "--run-online",
        action="store_true",
        default=False,
        help="Run tests that call the live YouTube Data API (requires APIS in .env)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "online: hits the live YouTube Data API (pass --run-online to enable)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-online"):
        return
    skip = pytest.mark.skip(reason="pass --run-online to run live YouTube API tests")
    for item in items:
        if "online" in item.keywords:
            item.add_marker(skip)


def _configured_api_keys() -> list[str]:
    return [k.strip() for k in os.environ.get("APIS", "").split(";") if k.strip()]


@pytest.fixture
def youtube_api_keys():
    keys = _configured_api_keys()
    if not keys or keys == ["test-api-key"]:
        pytest.skip("Set APIS in .env or the environment to run online tests")
    return keys


@pytest.fixture
def youtube_api(youtube_api_keys):
    return youtube_api_keys[0]


_resolved_playlist_id: str | None = None


@pytest.fixture
async def resolved_playlist_id(youtube_api):
    """Discover a stable uploads playlist once per test run."""
    global _resolved_playlist_id
    override = os.environ.get("YOUTUBE_TEST_PLAYLIST_ID")
    if override:
        return override
    if _resolved_playlist_id is None:
        video_id = os.environ.get("YOUTUBE_TEST_VIDEO_ID", "dQw4w9WgXcQ")
        _resolved_playlist_id = await fetch_uploads_playlist_id(youtube_api, video_id)
    return _resolved_playlist_id


@pytest.fixture
def itemlist():
    """Factory that builds ItemList instances without calling the YouTube API."""

    def _make(input_string: str, **kwargs) -> ItemList:
        defaults = {"start_range": 1, "end_range": 500, "youtube_api": "test-key"}
        defaults.update(kwargs)
        return ItemList(input_string, **defaults)

    return _make
