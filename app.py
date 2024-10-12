from datetime import timedelta
from typing import Annotated, Tuple, Optional
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import datetime
import isodate
import json
import re
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlencode


# find out which time slice an time lies in, to decide which API key to use
def find_time_slice():
    time_slice = datetime.datetime.now().time().hour // 4
    return time_slice


load_dotenv()

APIS = os.environ["APIS"].strip("][").split(",")
API = APIS[find_time_slice()].strip('"').strip("'")


def call_youtube_api(url_type, **kwargs):

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

    params["key"] = API
    url = f"{base_url}?{urlencode(params, safe=',')}"
    response = requests.get(url)
    return json.loads(response.text)


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


class ItemList:
    def __init__(
        self, input_string, start_range=None, end_range=None, custom_speed=None
    ):
        self.input_string = input_string
        self.start_range = start_range
        self.end_range = end_range
        self.custom_speed = custom_speed
        self.playlist_ids, self.video_ids = self.get_item_ids()
        self.populate_playlist_names()
        self.populate_video_names()

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

    def populate_playlist_names(self):
        results = call_youtube_api("playlists", playlist_ids=self.playlist_ids)

        refined_list = []

        if len(results["items"]) == 0:
            raise ValueError("No valid playlist found.")

        for id, data in zip(self.playlist_ids, results["items"]):

            if len(refined_list) == 0:
                playlist = Playlist(
                    id,
                    custom_speed=self.custom_speed,
                    start_range=self.start_range,
                    end_range=self.end_range,
                )
            else:
                playlist = Playlist(id, custom_speed=self.custom_speed)

            playlist.playlist_name = data["snippet"]["title"]
            playlist.playlist_creator = data["snippet"]["channelTitle"]
            refined_list.append(playlist)

        self.playlist_ids = refined_list

    def populate_video_names(self):
        results = call_youtube_api("videos", video_ids=self.video_ids)

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

        for playlist in self.playlist_ids:
            output_string += [playlist.get_output_string()]

        for video in self.video_ids:
            output_string += [video.get_output_string()]

        return output_string


class Video:

    def __init__(self, video_id, video_data, custom_speed=None):
        self.video_id = video_id
        try:
            self.update_video_details(video_data)
        except Exception as e:
            print(f"Error: {e}")
            print(video_data)
            self.considered = False
        self.custom_speed = custom_speed

    def update_video_details(self, video_data: dict):
        self.title = video_data["snippet"]["title"]
        self.channel = video_data["snippet"]["channelTitle"]
        self.published = video_data["snippet"]["publishedAt"]
        self.duration = isodate.parse_duration(video_data["contentDetails"]["duration"])
        self.views = video_data["statistics"].get("viewCount", 0)
        self.likes = video_data["statistics"].get("likeCount", 0)
        self.comments = video_data["statistics"].get("commentCount", 0)
        self.considered = True if self.duration.total_seconds() > 0 else False

    def __repr__(self):
        return f"Video(video_id={self.video_id}, title={self.title}, duration={self.duration})"

    def get_output_string(self):
        output_string = [
            "Video : " + self.title,
            "ID : " + self.video_id,
            "Duration : " + parse(self.duration),
            "At 1.25x : " + parse(self.duration / 1.25),
            "At 1.50x : " + parse(self.duration / 1.5),
            "At 1.75x : " + parse(self.duration / 1.75),
            "At 2.00x : " + parse(self.duration / 2),
        ]

        if self.custom_speed:
            output_string.append(
                f"At {self.custom_speed:.2f}x : {parse(self.duration / self.custom_speed)}"
            )
        return output_string


class Playlist:
    def __init__(
        self, playlist_id, custom_speed=None, start_range=None, end_range=None
    ):
        self.playlist_id = playlist_id
        self.next_page = ""  # for pagination
        self.total_duration = timedelta(0)  # total duration
        self.custom_speed = custom_speed

        self.get_video_list()
        self.available_count = sum([x.considered for x in self.videos])
        self.unavailable_count = len(self.videos) - self.available_count
        self.total_duration = sum([x.duration for x in self.videos], timedelta(0))
        self.average_duration = self.total_duration / self.available_count
        self.video_count = len(self.videos)
        self.start_range = max(1, start_range) if start_range else 1
        self.end_range = (
            min(self.available_count, end_range) if end_range else self.available_count
        )

        if start_range and end_range:
            self.videos_range = self.videos[start_range - 1 : end_range]
            self.total_duration = sum(
                [x.duration for x in self.videos_range], timedelta(0)
            )
            self.available_count = sum([x.considered for x in self.videos_range])
            self.unavailable_count = len(self.videos_range) - self.available_count
            self.average_duration = self.total_duration / self.available_count

    def __repr__(self):
        return f"Playlist(playlist_id={self.playlist_id}, video_count={self.video_count}, total_duration={self.total_duration}, average_duration={self.average_duration})"

    def get_video_list(self):

        self.videos = []

        while True:
            results = call_youtube_api(
                "playlistItems", playlistId=self.playlist_id, pageToken=self.next_page
            )
            video_ids = [x["contentDetails"]["videoId"] for x in results["items"]]

            try:
                video_data = call_youtube_api("videos", video_ids=video_ids)
            except KeyError:
                print(video_data)
                break

            self.video_ids = video_ids
            self.video_data = video_data

            for id, data in zip(video_ids, video_data["items"]):
                video = Video(id, data, self.custom_speed)
                self.videos.append(video)

            if "nextPageToken" in results and len(self.videos) < 500:
                self.next_page = results["nextPageToken"]
            else:
                break

    def get_output_string(self):
        output_string = [
            "Playlist : " + self.playlist_name,
            "ID : " + self.playlist_id,
            "Creator : " + self.playlist_creator,
        ]

        if self.video_count >= 500:
            output_string.append("No of videos limited to 500.")

        output_string += [
            f"Video count : {self.available_count} (from {self.start_range} to {self.end_range}) ({self.unavailable_count} unavailable)",
            "Average video length : "
            + parse(self.total_duration / self.available_count),
            "Total length : " + parse(self.total_duration),
            "At 1.25x : " + parse(self.total_duration / 1.25),
            "At 1.50x : " + parse(self.total_duration / 1.5),
            "At 1.75x : " + parse(self.total_duration / 1.75),
            "At 2.00x : " + parse(self.total_duration / 2),
        ]

        if self.custom_speed:
            output_string.append(
                f"At {self.custom_speed:.2f}x : {parse(self.total_duration / self.custom_speed)}"
            )

        return output_string


fapp = FastAPI()

fapp.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@fapp.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@fapp.post("/", response_class=HTMLResponse)
async def home(
    request: Request,
    search_string: Annotated[str, Form()],
    range_start: Annotated[Optional[str], Form()],
    range_end: Annotated[Optional[str], Form()],
    custom_speed: Annotated[Optional[str], Form()],
    youtube_api: Annotated[Optional[str], Form()],
):
    global API
    API = youtube_api if youtube_api else APIS[find_time_slice()].strip('"').strip("'")

    range_start = int(range_start) if range_start else 1
    range_end = int(range_end) if range_end else 500
    custom_speed = float(custom_speed) if custom_speed else None

    if range_start > range_end:
        range_start, range_end = range_end, range_start

    try:
        items = ItemList(search_string, range_start, range_end, custom_speed)
        output = items.get_output_string()

    except Exception as e:
        output = [[f"Error: {e}"]]

    return templates.TemplateResponse(
        "home.html", {"request": request, "playlist_detail": output}
    )


@fapp.route("/healthz", methods=["GET", "POST"])
def healthz():
    return "Success", 200


@fapp.route("/ads.txt")
def static_from_root_google():
    return Response(
        "google.com, pub-8874895270666721, DIRECT, f08c47fec0942fa0",
        mimetype="text/plain",
    )


if __name__ == "__main__":
    fapp.run(use_reloader=True, debug=False)
