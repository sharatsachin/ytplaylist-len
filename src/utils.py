import datetime
import json
import os
from urllib.parse import urlencode

import aiohttp


# find out which time slice an time lies in, to decide which API key to use
def find_time_slice():
    time_slice = datetime.datetime.now().time().hour // 4
    return time_slice


async def call_youtube_api(url_type, api, **kwargs):

    base_url = f"https://www.googleapis.com/youtube/v3/{url_type}"
    url_params = {
        "playlists": {
            "part": "snippet",
            "fields": "items/snippet/title,items/snippet/channelTitle",
            "id": ",".join(kwargs.get("playlist_ids", [])),
        },
        "playlistItems": {
            "part": "contentDetails",
            "maxResults": "50",
            "fields": "items/contentDetails/videoId,nextPageToken",
            "playlistId": kwargs.get("playlistId"),
            "pageToken": kwargs.get("pageToken", ""),  # Optional Page Token
        },
        "videos": {
            "part": "contentDetails,statistics,snippet",
            "id": ",".join(kwargs.get("video_ids", [])),  # List of video IDs
            "fields": "items/contentDetails/duration,items/statistics/likeCount,"
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
            return json.loads(await response.text())


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
