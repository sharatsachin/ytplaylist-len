from dotenv import load_dotenv

load_dotenv()

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional

from fastapi import FastAPI, Form, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, Response as StarletteResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from src.itemlist import ItemList
from src.utils import find_time_slice, extract_video_id, parse, pick_api_key
from src.i18n import (
    SUPPORTED_LOCALES,
    LOCALE_CODES,
    LOCALE_MAP,
    load_locales,
    get_translator,
)
from src import blog as blog_module

YOUTUBE_APIS = [k.strip() for k in os.environ["APIS"].split(";") if k.strip()]
BASE_URL = os.environ.get("BASE_URL", "https://ytplaylist-len.sharats.dev")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

fapp = FastAPI(title="YouTube Playlist Length", docs_url=None, redoc_url=None)
fapp.add_middleware(GZipMiddleware, minimum_size=500)

load_locales()


class CachedStaticFiles(StaticFiles):
    """StaticFiles subclass that sets long cache headers on served files."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=604800, immutable"
        return response


fapp.mount("/static", CachedStaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class I18nMiddleware(BaseHTTPMiddleware):
    """
    Strip a language prefix from the URL, set request.state.lang, and rewrite the
    path so downstream routes stay unchanged.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.scope["path"]
        parts = path.strip("/").split("/", 1)
        first = parts[0] if parts else ""
        if first in LOCALE_CODES and first != "en":
            request.state.lang = first
            rest = "/" + parts[1] if len(parts) > 1 else "/"
            request.scope["path"] = rest
            request.scope["raw_path"] = rest.encode("utf-8")
        else:
            request.state.lang = "en"
        return await call_next(request)


fapp.add_middleware(I18nMiddleware)


def base_context(request: Request, *, canonical_path: str = "/") -> dict:
    """Return context vars needed by base.html on every page."""
    lang = getattr(request.state, "lang", "en")
    loc = LOCALE_MAP.get(lang, LOCALE_MAP["en"])
    canonical_path = canonical_path if canonical_path.startswith("/") else "/" + canonical_path
    current_path_rel = canonical_path.lstrip("/")
    return {
        "lang": lang,
        "rtl": loc.rtl,
        "og_locale": loc.og_locale,
        "t": get_translator(lang),
        "locales": SUPPORTED_LOCALES,
        "canonical_path": canonical_path,
        "current_path": current_path_rel,
        "current_year": datetime.now(timezone.utc).year,
        "base_url": BASE_URL,
    }


def _parse_int(value: Optional[str], default: int) -> int:
    if not value or not str(value).strip():
        return default
    return int(value)


def _parse_float(value: Optional[str]) -> Optional[float]:
    if not value or not str(value).strip():
        return None
    return float(value)


@fapp.get("/", response_class=HTMLResponse)
async def home_get(request: Request):
    ctx = base_context(request, canonical_path="/")
    return templates.TemplateResponse(request=request, name="home.html", context=ctx)


@fapp.post("/", response_class=HTMLResponse)
async def home_post(
    request: Request,
    search_string: Annotated[str, Form()],
    range_start: Annotated[Optional[str], Form()] = None,
    range_end: Annotated[Optional[str], Form()] = None,
    custom_speed: Annotated[Optional[str], Form()] = None,
    youtube_api: Annotated[Optional[str], Form()] = None,
    watched_count: Annotated[Optional[str], Form()] = None,
):
    progress = None
    playlist_detail = None
    playlist_data = None
    form_error_key = None

    try:
        range_start_val = _parse_int(range_start, 1)
        range_end_val = _parse_int(range_end, 500)
        custom_speed_val = _parse_float(custom_speed)

        if range_start_val > range_end_val:
            range_start_val, range_end_val = range_end_val, range_start_val

        logger.info(f"Input TS({find_time_slice()}): {search_string}")
        api_key = pick_api_key(YOUTUBE_APIS, youtube_api.strip() if youtube_api else None)
        items = ItemList(
            search_string, range_start_val, range_end_val, custom_speed_val, api_key
        )
        await items.do_async_work()
        playlist_detail = items.get_structured_output()
        if playlist_detail is None:
            playlist_detail = [[("error_no_valid_input", "", {})]]
        else:
            playlist_data = items.get_playlist_data()

            if watched_count and items.playlist_ids:
                pl = items.playlist_ids[0]
                w = min(int(watched_count), len(pl.videos_range))
                watched_duration = sum(
                    (v.duration for v in pl.videos_range[:w]), timedelta(0)
                )
                remaining_duration = pl.total_duration - watched_duration
                total_secs = pl.total_duration.total_seconds()
                watched_secs = watched_duration.total_seconds()
                progress = {
                    "watched": w,
                    "total": len(pl.videos_range),
                    "watched_pct": round(watched_secs / total_secs * 100, 1) if total_secs else 0,
                    "watched_seconds": int(watched_secs),
                    "watched_duration": parse(watched_duration),
                    "remaining_duration": parse(remaining_duration),
                    "total_duration": parse(pl.total_duration),
                }
    except ValueError:
        logger.exception("Invalid form input")
        form_error_key = "error_invalid_form"
        playlist_detail = [[("error_invalid_form", "", {})]]
    except Exception as e:
        logger.exception(f"Error processing input: {e}")
        playlist_detail = [[("error_generic", "", {})]]

    ctx = base_context(request, canonical_path="/")
    ctx.update({
        "playlist_detail": playlist_detail,
        "search_string": search_string,
        "progress": progress,
        "watched_count": watched_count,
        "form_error_key": form_error_key,
        "playlist_data_json": json.dumps(playlist_data) if playlist_data else None,
    })
    return templates.TemplateResponse(request=request, name="home.html", context=ctx)


@fapp.get("/healthz")
def healthz():
    return "Success"


@fapp.get("/thumbnails", response_class=HTMLResponse)
async def thumbnails_get(request: Request):
    ctx = base_context(request, canonical_path="/thumbnails")
    return templates.TemplateResponse(request=request, name="thumbnails.html", context=ctx)


@fapp.post("/thumbnails", response_class=HTMLResponse)
async def thumbnails_post(request: Request, video_url: Annotated[str, Form()]):
    video_id = extract_video_id(video_url)
    if video_id:
        result = {
            "video_id": video_id,
            "thumbnails": [
                {"label_key": "thumb_max_res", "key": "maxresdefault"},
                {"label_key": "thumb_hq", "key": "hqdefault"},
                {"label_key": "thumb_mq", "key": "mqdefault"},
                {"label_key": "thumb_default", "key": "default"},
            ],
        }
    else:
        result = {"error": True}
    ctx = base_context(request, canonical_path="/thumbnails")
    ctx.update({"result": result, "video_url": video_url})
    return templates.TemplateResponse(request=request, name="thumbnails.html", context=ctx)


@fapp.get("/timestamp", response_class=HTMLResponse)
async def timestamp_get(request: Request):
    ctx = base_context(request, canonical_path="/timestamp")
    return templates.TemplateResponse(request=request, name="timestamp.html", context=ctx)


@fapp.post("/timestamp", response_class=HTMLResponse)
async def timestamp_post(
    request: Request,
    video_url: Annotated[str, Form()],
    hours: Annotated[Optional[str], Form()] = None,
    minutes: Annotated[Optional[str], Form()] = None,
    seconds: Annotated[Optional[str], Form()] = None,
):
    result = None
    try:
        video_id = extract_video_id(video_url)
        if video_id:
            h = _parse_int(hours, 0)
            m = _parse_int(minutes, 0)
            s = _parse_int(seconds, 0)
            total_seconds = h * 3600 + m * 60 + s
            result = {
                "link": f"https://youtu.be/{video_id}?t={total_seconds}",
                "label": f"{h}h {m}m {s}s".strip(),
            }
        else:
            result = {"error": True}
    except ValueError:
        result = {"error": True}

    ctx = base_context(request, canonical_path="/timestamp")
    ctx.update({
        "result": result,
        "video_url": video_url,
        "hours": hours or "",
        "minutes": minutes or "",
        "seconds": seconds or "",
    })
    return templates.TemplateResponse(request=request, name="timestamp.html", context=ctx)


@fapp.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    lang = getattr(request.state, "lang", "en")
    posts = blog_module.load_posts(lang)
    ctx = base_context(request, canonical_path="/blog")
    ctx.update({"posts": posts})
    return templates.TemplateResponse(request=request, name="blog/index.html", context=ctx)


@fapp.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_post(request: Request, slug: str):
    lang = getattr(request.state, "lang", "en")
    post = blog_module.get_post(slug, lang)
    if not post:
        ctx = base_context(request, canonical_path=f"/blog/{slug}")
        return templates.TemplateResponse(
            request=request, name="blog/index.html",
            context={**ctx, "posts": blog_module.load_posts(lang), "not_found": True},
            status_code=404,
        )
    related = blog_module.get_related(post, lang, limit=3)
    ctx = base_context(request, canonical_path=f"/blog/{slug}")
    ctx.update({"post": post, "related": related})
    return templates.TemplateResponse(request=request, name="blog/post.html", context=ctx)


@fapp.get("/sitemap.xml", response_class=Response)
async def sitemap():
    urls = []
    tools = ["/", "/thumbnails", "/timestamp", "/blog"]
    post_slugs = [p.slug for p in blog_module.load_posts("en")]
    all_paths = tools + [f"/blog/{s}" for s in post_slugs]

    lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for path in all_paths:
        for loc in SUPPORTED_LOCALES:
            loc_prefix = "" if loc.code == "en" else f"/{loc.code}"
            display_path = path if path != "/" else ""
            url = f"{BASE_URL}{loc_prefix}{display_path or '/'}"
            alternates = []
            for alt in SUPPORTED_LOCALES:
                alt_prefix = "" if alt.code == "en" else f"/{alt.code}"
                alt_url = f"{BASE_URL}{alt_prefix}{display_path or '/'}"
                alternates.append(
                    f'    <xhtml:link rel="alternate" hreflang="{alt.code}" href="{alt_url}"/>'
                )
            xdefault_url = f"{BASE_URL}{display_path or '/'}"
            alternates.append(
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{xdefault_url}"/>'
            )
            priority = "1.0" if path == "/" else ("0.9" if path.startswith("/blog") and path != "/blog" else "0.8")
            urls.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{priority}</priority>
{chr(10).join(alternates)}
  </url>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{chr(10).join(urls)}
</urlset>"""
    return Response(content=xml, media_type="application/xml")


@fapp.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return f"""User-agent: *
Allow: /
Disallow: /healthz

Sitemap: {BASE_URL}/sitemap.xml
"""


@fapp.get("/manifest.webmanifest")
async def manifest():
    return JSONResponse({
        "name": "YouTube Playlist Length",
        "short_name": "PL Length",
        "description": "Calculate the total length and duration of any YouTube playlist.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0a0a0a",
        "theme_color": "#dc2626",
        "icons": [
            {"src": "/static/favicon.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/favicon.png", "sizes": "512x512", "type": "image/png"},
        ],
    })


@fapp.get("/ads.txt", response_class=PlainTextResponse)
def ads_txt():
    return "google.com, pub-8874895270666721, DIRECT, f08c47fec0942fa0"


if __name__ == "__main__":
    fapp.run(
        use_reloader=True, debug=False, host="0.0.0.0", port=10000, access_log=False
    )
