---
title: "How to Download YouTube Video Thumbnails in Every Resolution (2026)"
description: "The direct URL patterns for downloading YouTube video thumbnails at every resolution — plus a free tool that does it for you in one click."
slug: download-youtube-thumbnails
date: 2026-06-30
updated: 2026-07-12
author: Sharat Sachin
reading_time: 5
tags:
  - youtube
  - thumbnails
  - tools
faq:
  - q: What is the highest resolution YouTube thumbnail I can download?
    a: 1280x720 (maxresdefault.jpg). Note that not every video has a max-res thumbnail — smaller channels or older videos may only have the 480x360 hqdefault available.
  - q: Are YouTube thumbnails copyrighted?
    a: Yes. Thumbnails belong to the video creator. Downloading them for personal reference or study is generally fine; redistributing or using them commercially without permission is not.
  - q: Why does maxresdefault sometimes 404?
    a: Not every video has a max-resolution thumbnail generated. Fall back to hqdefault (480x360) which always exists for public videos.
---

YouTube exposes video thumbnails at several fixed resolutions via a predictable URL pattern. If you know the pattern, you can grab any thumbnail directly — but the [Thumbnail Downloader](/thumbnails) makes it easier by showing all four sizes at once.

## The URL pattern

For any video ID `VIDEOID`, YouTube serves thumbnails at:

```
https://img.youtube.com/vi/VIDEOID/maxresdefault.jpg   # 1280x720
https://img.youtube.com/vi/VIDEOID/hqdefault.jpg       # 480x360
https://img.youtube.com/vi/VIDEOID/mqdefault.jpg       # 320x180
https://img.youtube.com/vi/VIDEOID/default.jpg         # 120x90
```

The video ID is the 11-character string after `v=` in a YouTube URL. For `https://www.youtube.com/watch?v=dQw4w9WgXcQ`, the video ID is `dQw4w9WgXcQ`, and the max-res thumbnail lives at `https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg`.

## Additional thumbnails available on some videos

YouTube also generates:

- `sddefault.jpg` (640x480) — standard definition
- Frame captures: `1.jpg`, `2.jpg`, `3.jpg` at 120x90 — three "moments" pulled from the video, used as fallbacks

These are available on most videos but are not guaranteed the way `hqdefault` is.

## Common gotchas

**maxresdefault sometimes returns 404.** Not every video has a max-res thumbnail generated — very old videos, videos from small channels, and some deleted/private videos will not have one. Fall back to `hqdefault` which is guaranteed for every public video.

**Some tools "download" a placeholder image.** If a video has been deleted, YouTube's thumbnail URLs return a grey placeholder image instead of a 404. Check that the returned image is not a 120x90 grey square before using.

**Live-stream thumbnails change.** For a live stream, the thumbnail URL is stable but the underlying image updates every few seconds. If you need a specific moment, download it while watching.

## Using the tool

The [Thumbnail Downloader](/thumbnails) is a zero-friction way to get all four resolutions:

1. Paste the video URL.
2. Click **Get Thumbnails**.
3. Click any of the four preview images to open it full-size, then save-as.

The tool works with `youtube.com/watch?v=...`, `youtu.be/...`, and even `youtube.com/shorts/...` URLs. It only extracts the video ID and never sends the URL to YouTube from your browser — it constructs the thumbnail URLs directly.

## Legit use cases

Common good-faith reasons to download a YouTube thumbnail:

- **Reference for your own thumbnail design.** Composing a mood board of what works in your niche.
- **Educational analysis.** Writing a blog post about what makes a thumbnail effective (like this one).
- **Personal archive.** Keeping a copy for a video you rely on that might get taken down.

Reasons that are not okay: re-uploading someone else's thumbnail with a stolen video, using thumbnails commercially without licensing.

## Try it

Grab any YouTube video URL and try the [Thumbnail Downloader](/thumbnails). It's free and instant.

## Related reading

- [How Long Is a YouTube Playlist? The Complete Guide](/blog/how-long-is-a-youtube-playlist)
- [How to Share a YouTube Video at a Specific Time](/blog/youtube-timestamp-links-explained)
