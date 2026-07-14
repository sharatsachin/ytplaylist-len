"""Playlist logic tests (no live YouTube API calls)."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.playlist import Playlist, _UNAVAILABLE_STUB
from src.video import Video


def _yt_video(video_id: str, seconds: int, title: str = "Video") -> dict:
    return {
        "id": video_id,
        "snippet": {
            "title": title,
            "channelTitle": "Channel",
            "publishedAt": "2024-01-01T00:00:00Z",
        },
        "contentDetails": {"duration": f"PT{seconds}S"},
        "statistics": {"viewCount": "1", "likeCount": "0", "commentCount": "0"},
    }


def _make_video(video_id: str, seconds: int, considered: bool = True) -> Video:
    stub = _yt_video(video_id, seconds if considered else 0)
    if not considered:
        stub["contentDetails"]["duration"] = "PT0S"
    return Video(video_id, stub)


class TestApplyRangeLogic:
    """Exercise range slicing by pre-loading videos and skipping the API/cache."""

    def _playlist_with_videos(self, count: int, start: int, end: int) -> Playlist:
        pl = Playlist("PLtest", start_range=start, end_range=end, youtube_api="test")
        pl.videos = [_make_video(f"vid{i}", 60) for i in range(1, count + 1)]
        pl.available_count = count
        pl.unavailable_count = 0
        pl.total_duration = timedelta(seconds=60 * count)
        pl.average_duration = timedelta(seconds=60)
        pl.video_count = count
        positional_count = len(pl.videos)
        pl.start_range = max(1, pl.start_range) if pl.start_range else 1
        pl.end_range = min(positional_count, pl.end_range) if pl.end_range else positional_count
        if pl.start_range and pl.end_range and pl.start_range <= pl.end_range:
            pl.videos_range = pl.videos[pl.start_range - 1 : pl.end_range]
            pl.total_duration = sum((v.duration for v in pl.videos_range), timedelta(0))
            pl.available_count = sum(v.considered for v in pl.videos_range)
            pl.unavailable_count = len(pl.videos_range) - pl.available_count
            pl.average_duration = (
                pl.total_duration / pl.available_count
                if pl.available_count
                else timedelta(0)
            )
        else:
            pl.videos_range = []
        return pl

    def test_range_uses_positional_length_not_available_only(self):
        pl = self._playlist_with_videos(count=100, start=1, end=100)
        assert pl.end_range == 100
        assert len(pl.videos_range) == 100

    def test_range_subset(self):
        pl = self._playlist_with_videos(count=50, start=10, end=20)
        assert len(pl.videos_range) == 11
        assert pl.videos_range[0].video_id == "vid10"
        assert pl.videos_range[-1].video_id == "vid20"
        assert pl.total_duration == timedelta(seconds=11 * 60)

    def test_zero_available_in_range_does_not_crash(self):
        pl = Playlist("PLtest", start_range=1, end_range=3, youtube_api="test")
        pl.playlist_name = "Test Playlist"
        pl.playlist_creator = "Test Channel"
        pl.videos = [
            _make_video("a", 0, considered=False),
            _make_video("b", 0, considered=False),
            _make_video("c", 0, considered=False),
        ]
        pl.video_count = 3
        pl.start_range = 1
        pl.end_range = 3
        pl.videos_range = pl.videos[0:3]
        pl.total_duration = timedelta(0)
        pl.available_count = 0
        pl.unavailable_count = 3
        pl.average_duration = timedelta(0)
        output = pl.get_output()
        avg = next(v for k, v, _ in output if k == "result_avg_length")
        assert avg == "0 seconds"


@pytest.mark.asyncio
class TestGetVideosDetails:
    async def test_preserves_order_and_stubs_missing(self):
        pl = Playlist("PLtest", youtube_api="test-key")
        pl.video_ids = ["vid1", "vid2", "vid3"]

        api_response = {"items": [_yt_video("vid1", 60), _yt_video("vid3", 120)]}

        with patch("src.playlist.call_youtube_api", new=AsyncMock(return_value=api_response)):
            await pl.get_videos_details()

        assert [v.video_id for v in pl.videos] == ["vid1", "vid2", "vid3"]
        assert pl.videos[0].duration == timedelta(seconds=60)
        assert pl.videos[1].title == "(Unavailable)"
        assert pl.videos[1].considered is False
        assert pl.videos[2].duration == timedelta(seconds=120)
