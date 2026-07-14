import logging
import re
from typing import Tuple

from src.playlist import Playlist
from src.utils import call_youtube_api, find_time_slice
from src.video import Video


class ItemList:
    def __init__(
        self,
        input_string,
        start_range=None,
        end_range=None,
        custom_speed=None,
        youtube_api=None,
    ):
        self.input_string = input_string
        self.start_range = start_range
        self.end_range = end_range
        self.custom_speed = custom_speed
        self.youtube_api = youtube_api
        self.playlist_ids, self.video_ids = self.get_item_ids()

    async def do_async_work(self):
        await self.populate_playlist_names()
        await self.populate_video_names()

    def get_id(self, playlist_link: str) -> Tuple[str, str]:
        playlist_link = playlist_link.strip()
        if not playlist_link:
            return "invalid", "invalid"

        patterns = [
            (r"^[\S]+list=([\w_-]+)[\S]*$", "playlist"),
            (r"^[\S]+v=([\w_-]+)[\S]*$", "video"),
            (r"^[\S]+be/([\w_-]+)[\S]*$", "video"),
            (r"^([\w-]{11})$", "video"),  # bare 11-char video ID
            (r"^([\w_-]+)$", "playlist"),  # bare playlist ID
        ]
        for pattern, link_type in patterns:
            match = re.match(pattern, playlist_link)
            if match:
                return match.group(1), link_type
        return "invalid", "invalid"

    async def populate_playlist_names(self):
        if not self.playlist_ids:
            return

        results = await call_youtube_api(
            "playlists", api=self.youtube_api, playlist_ids=self.playlist_ids
        )

        items = results.get("items", [])
        if not items:
            raise RuntimeError("No playlists found for the provided ID(s)")

        by_id = {item["id"]: item for item in items}
        refined_list = []

        for pid in self.playlist_ids:
            data = by_id.get(pid)
            if not data:
                logging.warning(f"Playlist {pid} not returned by YouTube API")
                continue

            if len(refined_list) == 0:
                playlist = Playlist(
                    pid,
                    custom_speed=self.custom_speed,
                    start_range=self.start_range,
                    end_range=self.end_range,
                    youtube_api=self.youtube_api,
                )
                await playlist.do_async_work()
            else:
                playlist = Playlist(
                    pid, custom_speed=self.custom_speed, youtube_api=self.youtube_api
                )
                await playlist.do_async_work()

            playlist.playlist_name = data["snippet"]["title"]
            playlist.playlist_creator = data["snippet"]["channelTitle"]
            refined_list.append(playlist)

        if not refined_list and self.playlist_ids:
            raise RuntimeError("No playlists found for the provided ID(s)")

        self.playlist_ids = refined_list

    async def populate_video_names(self):
        if not self.video_ids:
            return

        results = await call_youtube_api(
            "videos", api=self.youtube_api, video_ids=self.video_ids
        )

        by_id = {item["id"]: item for item in results.get("items", [])}
        refined_list = []
        for vid in self.video_ids:
            data = by_id.get(vid)
            if data:
                refined_list.append(Video(vid, data, custom_speed=self.custom_speed))
            else:
                logging.warning(f"Video {vid} not returned by YouTube API")

        self.video_ids = refined_list

    def get_item_ids(self):
        playlists = []
        videos = []

        for item in self.input_string.split("\n"):
            item = item.strip()
            if not item:
                continue
            item_id, item_type = self.get_id(item)

            if item_type == "video":
                videos.append(item_id)
            elif item_type == "playlist":
                playlists.append(item_id)

        playlists = list(dict.fromkeys(playlists))
        videos = list(dict.fromkeys(videos))
        return playlists, videos

    def get_output_string(self):
        output_string = []

        if not self.playlist_ids and not self.video_ids:
            return [["No valid playlist or video IDs found in input."]]

        for playlist in self.playlist_ids:
            output_string += [playlist.get_output_string()]

        for video in self.video_ids:
            output_string += [video.get_output_string()]

        return output_string

    def get_structured_output(self):
        """Return list of blocks, each a list of (label_key, value, kwargs) tuples for i18n."""
        blocks = []
        if not self.playlist_ids and not self.video_ids:
            return None

        for playlist in self.playlist_ids:
            blocks.append(playlist.get_output())

        for video in self.video_ids:
            blocks.append(video.get_output())

        return blocks or None

    def get_playlist_data(self):
        """Return raw duration data for JS-side schedule calculator (first playlist only)."""
        if not self.playlist_ids:
            return None
        pl = self.playlist_ids[0]
        try:
            videos = pl.videos_range
        except AttributeError:
            videos = getattr(pl, "videos", [])
        return {
            "video_count": len(videos),
            "total_seconds": int(pl.total_duration.total_seconds()),
            "video_durations": [int(v.duration.total_seconds()) for v in videos],
            "playlist_name": pl.playlist_name,
        }
