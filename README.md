# YouTube Playlist Length

Analyze YouTube playlists and videos with ease. Get detailed information about video durations, playlist lengths, and plan your watch schedule. Hosted at [ytplaylist-len.sharats.dev](https://ytplaylist-len.sharats.dev/).

## Features

- Analyze multiple playlists and individual videos in one request (up to 5)
- Calculate total duration at 1.25x, 1.50x, 1.75x, 2.00x and custom speeds
- Analyze specific video ranges within playlists (up to 500 videos)
- **Watch Schedule calculator** — enter hours per day + which days of the week you watch, get a real finish date and progress ring
- **Full internationalization** into 27 languages (URL-prefixed with `/es/`, `/fr/`, `/ja/`, `/ta/`, `/bn/`, etc. and `hreflang` alternates for SEO)
- **YouTube Thumbnail Downloader** at `/thumbnails`
- **YouTube Timestamp Link Generator** at `/timestamp`
- Redis-backed caching (24h TTL) and parallel async YouTube API calls

## Getting started

```
git clone https://github.com/sharatsachin/ytplaylist-len.git
cd ytplaylist-len
pip install -r requirements.txt
```

Create a `.env` file with:

```
APIS=your_youtube_api_key
REDIS_URL=redis://localhost:6379
MONGO_URL=mongodb://localhost:27017
BASE_URL=https://ytplaylist-len.sharats.dev
```

You can supply multiple API keys separated by `;` — the app time-slices between them based on the current hour to spread quota load.

Run the app:

```
fastapi dev app.py
```

Then open `http://localhost:8000`.

## Tests

Install dev dependencies and run the offline unit tests (no YouTube API key required):

```
pip install -r requirements-dev.txt
pytest
```

Offline tests cover URL/ID parsing (`get_id`, `get_item_ids`), utility helpers (`extract_video_id`, `parse`, `pick_api_key`), and playlist range / video-order logic using mocked API responses.

### Online integration tests

With a real `APIS` key in `.env`, run live tests against the YouTube Data API:

```
pytest --run-online
```

Online tests fetch a known public video and that video's channel uploads playlist (or a playlist you set via `YOUTUBE_TEST_PLAYLIST_ID`), exercise `call_youtube_api`, and run end-to-end `ItemList` / `Playlist` flows. They consume a small amount of API quota (~5–15 units per run).

Optional env overrides:

```
YOUTUBE_TEST_VIDEO_ID=dQw4w9WgXcQ
YOUTUBE_TEST_PLAYLIST_ID=PLxxxxxxxx   # skip auto-discovery when set
```

## Project structure

```
app.py                       FastAPI app: routes, i18n middleware, sitemap, gzip
src/
  i18n.py                    Locale loader + translator factory
  blog.py                    Markdown blog post loader
  itemlist.py                Playlist/video parsing entry point
  playlist.py                Playlist API + Redis cache
  video.py                   Video model
  utils.py                   YouTube API + duration helpers
locales/                     27 JSON translation files
content/blog/en/             Blog posts (Markdown + YAML frontmatter)
templates/
  base.html                  Shared layout, SEO, JSON-LD
  home.html                  Playlist calculator + schedule + FAQ + HowTo
  thumbnails.html            Thumbnail downloader
  timestamp.html             Timestamp link generator
  blog/                      Blog list + post templates
static/
  favicon.png, logo.png
  form_validation.js         Inline form validation
  js/schedule.js             Client-side reactive watch schedule calculator
tests/                       pytest unit tests (input parsing, utils, playlist logic)
```

## Adding a language

1. Copy `locales/en.json` to `locales/xx.json`.
2. Translate the values (keep keys unchanged).
3. Add a `LocaleInfo` entry to `SUPPORTED_LOCALES` in `src/i18n.py`.
4. Restart the app. That's it — the URL prefix routing and hreflang alternates work automatically.

## 🤝 Contributing

I'm actually not looking for contributions to this repository, and I won't be actively watching it. However, feel free to fork the repository and make your own changes!

## Technologies

- [Python](https://www.python.org/) 3.13
- [FastAPI](https://fastapi.tiangolo.com/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Jinja2](https://jinja.palletsprojects.com/)
- [Tailwind CSS](https://tailwindcss.com/) (CDN)
- [Redis](https://redis.io/) — playlist caching
- [MongoDB](https://www.mongodb.com/) — request analytics
- [Render](https://render.com/) — hosting