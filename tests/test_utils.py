"""Tests for src.utils helpers."""

from datetime import timedelta

import pytest

from src.utils import extract_video_id, parse, pick_api_key


EXTRACT_VIDEO_ID_CASES = [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtube.com/watch?v=abcdefghijk", "abcdefghijk"),
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtu.be/dQw4w9WgXcQ?t=120", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/embed/dQw4w9WgXcQ?start=30", None),
    ("https://example.com/not-youtube", None),
    ("", None),
]

PARSE_DURATION_CASES = [
    (timedelta(0), "0 seconds"),
    (timedelta(seconds=45), "45 seconds"),
    (timedelta(minutes=1, seconds=30), "1 minute, 30 seconds"),
    (timedelta(hours=2, minutes=5), "2 hours, 5 minutes"),
    (timedelta(days=1, hours=3), "1 day, 3 hours"),
    (timedelta(days=2), "2 days"),
]


class TestExtractVideoId:
    @pytest.mark.parametrize("url,expected", EXTRACT_VIDEO_ID_CASES)
    def test_extract_video_id(self, url, expected):
        assert extract_video_id(url) == expected


class TestParseDuration:
    @pytest.mark.parametrize("delta,expected", PARSE_DURATION_CASES)
    def test_parse(self, delta, expected):
        assert parse(delta) == expected


class TestPickApiKey:
    def test_user_key_takes_priority(self):
        assert pick_api_key(["a", "b", "c"], "user-supplied") == "user-supplied"

    def test_rotates_within_key_list(self, monkeypatch):
        keys = ["alpha", "beta", "gamma"]
        monkeypatch.setattr("src.utils.find_time_slice", lambda: 0)
        assert pick_api_key(keys) == "alpha"
        monkeypatch.setattr("src.utils.find_time_slice", lambda: 1)
        assert pick_api_key(keys) == "beta"
        monkeypatch.setattr("src.utils.find_time_slice", lambda: 2)
        assert pick_api_key(keys) == "gamma"
        monkeypatch.setattr("src.utils.find_time_slice", lambda: 3)
        assert pick_api_key(keys) == "alpha"

    def test_single_key_always_returned(self):
        assert pick_api_key(["only-key"]) == "only-key"

    def test_empty_keys_raises(self):
        with pytest.raises(RuntimeError, match="No YouTube API keys"):
            pick_api_key([])
