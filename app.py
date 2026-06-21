from dotenv import load_dotenv

load_dotenv()

import logging
import os
from datetime import timedelta
from typing import Annotated, Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.itemlist import ItemList
from src.utils import find_time_slice, extract_video_id, parse

YOUTUBE_APIS = os.environ["APIS"].split(";")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

fapp = FastAPI()

fapp.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@fapp.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")


@fapp.post("/", response_class=HTMLResponse)
async def home(
    request: Request,
    search_string: Annotated[str, Form()],
    range_start: Annotated[Optional[str], Form()] = None,
    range_end: Annotated[Optional[str], Form()] = None,
    custom_speed: Annotated[Optional[str], Form()] = None,
    youtube_api: Annotated[Optional[str], Form()] = None,
    watched_count: Annotated[Optional[str], Form()] = None,
):

    range_start = int(range_start) if range_start else 1
    range_end = int(range_end) if range_end else 500
    custom_speed = float(custom_speed) if custom_speed else None

    if range_start > range_end:
        range_start, range_end = range_end, range_start

    progress = None
    try:
        logger.info(f"Input TS({find_time_slice()}): {search_string}")
        youtube_api = youtube_api if youtube_api else YOUTUBE_APIS[find_time_slice()]
        items = ItemList(
            search_string, range_start, range_end, custom_speed, youtube_api
        )
        await items.do_async_work()
        output = items.get_output_string()

        if watched_count and items.playlist_ids:
            pl = items.playlist_ids[0]
            w = min(int(watched_count), len(pl.videos_range))
            watched_duration = sum([v.duration for v in pl.videos_range[:w]], timedelta(0))
            remaining_duration = pl.total_duration - watched_duration
            progress = {
                "watched": w,
                "total": pl.available_count,
                "watched_pct": round(w / pl.available_count * 100, 1) if pl.available_count else 0,
                "watched_duration": parse(watched_duration),
                "remaining_duration": parse(remaining_duration),
                "total_duration": parse(pl.total_duration),
            }

    except Exception as e:
        output = [[f"Error: {e}"]]
        logger.error(f"{output}")

    return templates.TemplateResponse(
        request=request, name="home.html",
        context={"playlist_detail": output, "search_string": search_string, "progress": progress, "watched_count": watched_count}
    )


@fapp.get("/healthz")
def healthz():
    return "Success"


@fapp.get("/thumbnails", response_class=HTMLResponse)
async def thumbnails_get(request: Request):
    return templates.TemplateResponse(request=request, name="thumbnails.html")


@fapp.post("/thumbnails", response_class=HTMLResponse)
async def thumbnails_post(request: Request, video_url: Annotated[str, Form()]):
    video_id = extract_video_id(video_url)
    if video_id:
        result = {
            "video_id": video_id,
            "thumbnails": [
                {"label": "Max Resolution", "key": "maxresdefault"},
                {"label": "High Quality", "key": "hqdefault"},
                {"label": "Medium Quality", "key": "mqdefault"},
                {"label": "Default", "key": "default"},
            ],
        }
    else:
        result = {"error": "Could not extract a video ID from the provided URL."}
    return templates.TemplateResponse(request=request, name="thumbnails.html", context={"result": result, "video_url": video_url})


@fapp.get("/timestamp", response_class=HTMLResponse)
async def timestamp_get(request: Request):
    return templates.TemplateResponse(request=request, name="timestamp.html")


@fapp.post("/timestamp", response_class=HTMLResponse)
async def timestamp_post(
    request: Request,
    video_url: Annotated[str, Form()],
    hours: Annotated[Optional[str], Form()] = None,
    minutes: Annotated[Optional[str], Form()] = None,
    seconds: Annotated[Optional[str], Form()] = None,
):
    video_id = extract_video_id(video_url)
    if video_id:
        h = int(hours) if hours else 0
        m = int(minutes) if minutes else 0
        s = int(seconds) if seconds else 0
        total_seconds = h * 3600 + m * 60 + s
        result = {
            "link": f"https://youtu.be/{video_id}?t={total_seconds}",
            "label": f"{h}h {m}m {s}s".strip(),
        }
    else:
        result = {"error": "Could not extract a video ID from the provided URL."}
    return templates.TemplateResponse(request=request, name="timestamp.html", context={"result": result})


@fapp.get("/ads.txt", response_class=PlainTextResponse)
def static_from_root_google():
    return "google.com, pub-8874895270666721, DIRECT, f08c47fec0942fa0"


if __name__ == "__main__":
    fapp.run(
        use_reloader=True, debug=False, host="0.0.0.0", port=10000, access_log=False
    )
