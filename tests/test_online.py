"""
Live integration tests against the YouTube Data API.

Run with a real API key configured in `.env` or the APIS environment variable:

    pytest --run-online

These tests consume API quota (~5–15 units per run depending on playlist size).
"""

import os

import pytest

from src.itemlist import ItemList
from src.playlist import Playlist
from src.utils import call_youtube_api, pick_api_key

# Stable public video (override via env for your own target).
TEST_VIDEO_ID = os.environ.get("YOUTUBE_TEST_VIDEO_ID", "dQw4w9WgXcQ")
TEST_VIDEO_URL = f"https://www.youtube.com/watch?v={TEST_VIDEO_ID}"


pytestmark = pytest.mark.online


@pytest.fixture
def test_playlist_id(youtube_api, resolved_playlist_id):
    override = os.environ.get("YOUTUBE_TEST_PLAYLIST_ID")
    return override or resolved_playlist_id


@pytest.fixture
def test_playlist_url(test_playlist_id):
    return f"https://www.youtube.com/playlist?list={test_playlist_id}"


@pytest.mark.asyncio
async def test_videos_api_returns_known_video(youtube_api):
    data = await call_youtube_api("videos", api=youtube_api, video_ids=[TEST_VIDEO_ID])
    items = data.get("items", [])
    assert len(items) == 1
    item = items[0]
    assert item["id"] == TEST_VIDEO_ID
    assert item["snippet"]["title"]
    assert item["contentDetails"]["duration"]


@pytest.mark.asyncio
async def test_playlists_api_returns_metadata(youtube_api, test_playlist_id):
    data = await call_youtube_api(
        "playlists", api=youtube_api, playlist_ids=[test_playlist_id]
    )
    items = data.get("items", [])
    assert len(items) == 1
    item = items[0]
    assert item["id"] == test_playlist_id
    assert item["snippet"]["title"]
    assert item["snippet"]["channelTitle"]


@pytest.mark.asyncio
async def test_playlist_items_api_returns_entries(youtube_api, test_playlist_id):
    data = await call_youtube_api(
        "playlistItems",
        api=youtube_api,
        playlistId=test_playlist_id,
    )
    items = data.get("items", [])
    assert len(items) >= 1
    assert items[0]["contentDetails"]["videoId"]


@pytest.mark.asyncio
async def test_itemlist_single_video_end_to_end(youtube_api):
    il = ItemList(TEST_VIDEO_URL, youtube_api=youtube_api)
    assert il.video_ids == [TEST_VIDEO_ID]
    assert il.playlist_ids == []

    await il.do_async_work()
    assert len(il.video_ids) == 1

    video = il.video_ids[0]
    assert video.video_id == TEST_VIDEO_ID
    assert video.title
    assert video.duration.total_seconds() > 0

    blocks = il.get_structured_output()
    assert blocks is not None
    assert len(blocks) == 1
    duration_line = next(row for row in blocks[0] if row[0] == "result_duration")
    assert duration_line[1] != "0 seconds"


@pytest.mark.asyncio
async def test_itemlist_playlist_with_small_range(youtube_api, test_playlist_url, test_playlist_id):
    il = ItemList(
        test_playlist_url,
        start_range=1,
        end_range=5,
        youtube_api=youtube_api,
    )
    assert il.playlist_ids == [test_playlist_id]

    await il.do_async_work()
    assert len(il.playlist_ids) == 1

    playlist = il.playlist_ids[0]
    assert playlist.playlist_name
    assert playlist.playlist_creator
    assert len(playlist.videos) >= 1
    assert len(playlist.videos_range) >= 1
    assert playlist.total_duration.total_seconds() > 0

    blocks = il.get_structured_output()
    assert blocks is not None
    total_line = next(row for row in blocks[0] if row[0] == "result_total_length")
    assert total_line[1] != "0 seconds"


@pytest.mark.asyncio
async def test_playlist_fetch_preserves_video_order(youtube_api, test_playlist_id):
    pl = Playlist(test_playlist_id, youtube_api=youtube_api)
    await pl.get_video_ids_list()
    assert len(pl.video_ids) >= 2

    first_ids = pl.video_ids[:5]
    await pl.get_videos_details()
    assert [v.video_id for v in pl.videos[:5]] == first_ids


def test_pick_api_key_uses_configured_keys(youtube_api_keys):
    assert pick_api_key(youtube_api_keys) in youtube_api_keys
