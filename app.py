from dotenv import load_dotenv

load_dotenv()

import logging
import os
from typing import Annotated, Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.itemlist import ItemList
from src.utils import find_time_slice

YOUTUBE_APIS = os.environ["APIS"].split(";")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

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

    range_start = int(range_start) if range_start else 1
    range_end = int(range_end) if range_end else 500
    custom_speed = float(custom_speed) if custom_speed else None

    if range_start > range_end:
        range_start, range_end = range_end, range_start

    try:
        logger.info(f"Input TS({find_time_slice()}): {search_string}")
        youtube_api = youtube_api if youtube_api else YOUTUBE_APIS[find_time_slice()]
        items = ItemList(
            search_string, range_start, range_end, custom_speed, youtube_api
        )
        await items.do_async_work()
        output = items.get_output_string()

    except Exception as e:
        output = [[f"Error: {e}"]]
        logger.error(f"{output}")

    return templates.TemplateResponse(
        "home.html", {"request": request, "playlist_detail": output}
    )


@fapp.get("/healthz")
def healthz():
    return "Success"


@fapp.get("/ads.txt", response_class=PlainTextResponse)
def static_from_root_google():
    return "google.com, pub-8874895270666721, DIRECT, f08c47fec0942fa0"


if __name__ == "__main__":
    fapp.run(
        use_reloader=True, debug=False, host="0.0.0.0", port=10000, access_log=False
    )
