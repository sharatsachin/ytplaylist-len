import datetime
import json
import os
import re
from urllib.parse import urlencode

import aiohttp


def find_time_slice():
    """Return 0–5 time bucket from current hour (used for API key rotation)."""
    return datetime.datetime.now().time().hour // 4


def pick_api_key(keys: list[str], user_key: str | None = None) -> str:
    """Pick a YouTube API key, rotating by time slice when multiple are configured."""
    if user_key:
        return user_key
    if not keys:
        raise RuntimeError("No YouTube API keys configured")
    return keys[find_time_slice() % len(keys)]


async def call_youtube_api(url_type, api, **kwargs):

    base_url = f"https://www.googleapis.com/youtube/v3/{url_type}"
    url_params = {
        "playlists": {
            "part": "snippet",
            "fields": "items/id,items/snippet/title,items/snippet/channelTitle",
            "id": ",".join(kwargs.get("playlist_ids", [])),
        },
        "playlistItems": {
            "part": "contentDetails",
            "maxResults": "50",
            "fields": "items/contentDetails/videoId,nextPageToken",
            "playlistId": kwargs.get("playlistId"),
            "pageToken": kwargs.get("pageToken", ""),
        },
        "videos": {
            "part": "contentDetails,statistics,snippet",
            "id": ",".join(kwargs.get("video_ids", [])),
            "fields": "items/id,items/contentDetails/duration,items/statistics/likeCount,"
            "items/statistics/viewCount,items/statistics/commentCount,"
            "items/snippet/title,items/snippet/channelTitle,items/snippet/publishedAt",
        },
    }

    params = url_params.get(url_type, {})
    if not params:
        raise ValueError(f"Invalid URL type: {url_type}")

    params["key"] = api
    url = f"{base_url}?{urlencode(params, safe=',')}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = json.loads(await response.text())
            if not response.ok:
                msg = data.get("error", {}).get("message", f"YouTube API HTTP {response.status}")
                raise RuntimeError(msg)
            return data


def extract_video_id(url):
    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None


def parse(a):
    ts, td = a.seconds, a.days
    th, tr = divmod(ts, 3600)
    tm, ts = divmod(tr, 60)
    ds = ""
    if td:
        ds += " {} day{},".format(td, "s" if td != 1 else "")
    if th:
        ds += " {} hour{},".format(th, "s" if th != 1 else "")
    if tm:
        ds += " {} minute{},".format(tm, "s" if tm != 1 else "")
    if ts:
        ds += " {} second{}".format(ts, "s" if ts != 1 else "")
    if ds == "":
        ds = "0 seconds"
    return ds.strip().strip(",")
