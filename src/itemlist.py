import asyncio
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

        patterns = [
            (r"^([\S]+list=)([\w_-]+)[\S]*$", "playlist"),  # playlist URL pattern
            (r"^([\S]+v=)([\w_-]+)[\S]*$", "video"),  # video URL pattern with "v="
            (r"^([\S]+be/)([\w_-]+)[\S]*$", "video"),  # shortened YouTube link pattern
            (r"^([\S]+list=)?([\w_-]+)[\S]*$", "playlist"),  # playlist URL pattern
        ]
        for pattern, link_type in patterns:
            match = re.match(pattern, playlist_link)
            if match:
                return match.group(2), link_type
        return "invalid", "invalid"

    async def populate_playlist_names(self):
        results = await call_youtube_api(
            "playlists", api=self.youtube_api, playlist_ids=self.playlist_ids
        )

        refined_list = []
        try:
            if len(results["items"]) == 0:
                self.playlist_ids = []
                return
        except KeyError:
            logging.error(find_time_slice())
            logging.error(self.youtube_api)
            logging.error(results)
            raise Exception(results["error"]["message"])

        for id, data in zip(self.playlist_ids, results["items"]):

            if len(refined_list) == 0:
                playlist = Playlist(
                    id,
                    custom_speed=self.custom_speed,
                    start_range=self.start_range,
                    end_range=self.end_range,
                    youtube_api=self.youtube_api,
                )
                await playlist.do_async_work()
            else:
                playlist = Playlist(
                    id, custom_speed=self.custom_speed, youtube_api=self.youtube_api
                )
                await playlist.do_async_work()

            playlist.playlist_name = data["snippet"]["title"]
            playlist.playlist_creator = data["snippet"]["channelTitle"]
            refined_list.append(playlist)

        self.playlist_ids = refined_list

    async def populate_video_names(self):
        results = await call_youtube_api(
            "videos", api=self.youtube_api, video_ids=self.video_ids
        )

        refined_list = []
        for id, data in zip(self.video_ids, results["items"]):
            video = Video(id, data, custom_speed=self.custom_speed)
            refined_list.append(video)
        self.video_ids = refined_list

    def get_item_ids(self):
        playlists = []
        videos = []

        for item in self.input_string.split("\n"):
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
