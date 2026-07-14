"""Helpers for live YouTube API integration tests."""

from urllib.parse import urlencode

import aiohttp


async def fetch_uploads_playlist_id(api_key: str, video_id: str) -> str:
    """Return a channel's public uploads playlist ID for a known video."""
    async with aiohttp.ClientSession() as session:
        video_url = (
            "https://www.googleapis.com/youtube/v3/videos?"
            + urlencode(
                {
                    "part": "snippet",
                    "id": video_id,
                    "fields": "items/snippet/channelId",
                    "key": api_key,
                }
            )
        )
        async with session.get(video_url) as response:
            video_data = await response.json()
            if not response.ok:
                msg = video_data.get("error", {}).get("message", response.reason)
                raise RuntimeError(msg)

        channel_id = video_data["items"][0]["snippet"]["channelId"]

        channel_url = (
            "https://www.googleapis.com/youtube/v3/channels?"
            + urlencode(
                {
                    "part": "contentDetails",
                    "id": channel_id,
                    "fields": "items/contentDetails/relatedPlaylists/uploads",
                    "key": api_key,
                }
            )
        )
        async with session.get(channel_url) as response:
            channel_data = await response.json()
            if not response.ok:
                msg = channel_data.get("error", {}).get("message", response.reason)
                raise RuntimeError(msg)

    return channel_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
