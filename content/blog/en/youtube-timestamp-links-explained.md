---
title: "How to Share a YouTube Video at a Specific Time (Timestamp Links Explained)"
description: "The complete guide to YouTube timestamp URLs: how to create them, share them across platforms, and generate them for any moment in seconds."
slug: youtube-timestamp-links-explained
date: 2026-06-28
updated: 2026-07-12
author: Sharat Sachin
reading_time: 5
tags:
  - youtube
  - sharing
  - links
faq:
  - q: How do timestamp links work on YouTube?
    a: YouTube reads a `t=` query parameter and starts the video at that second offset. `t=90` starts the video at 1:30. It works on youtube.com, youtu.be, and mobile clients.
  - q: Does the timestamp work on mobile YouTube?
    a: Yes. Both iOS and Android YouTube apps honor the `t=` parameter when a link is opened from another app. Timestamp links generated on desktop work everywhere.
  - q: Can I link to a range, not just a start time?
    a: Not through URLs. You can only specify a start time via `t=`. Ranges require the embed player and can be set with `start=X&end=Y` in the embed URL.
---

Sharing a specific moment in a long video is one of those small workflows that saves hours over a year. YouTube supports it natively — you just need to know the URL pattern, or use a [Timestamp Link Generator](/timestamp) that does the math for you.

## The URL pattern

For any YouTube video, appending `?t=<seconds>` (or `&t=<seconds>` if the URL already has query parameters) makes the video start at that second offset:

```
https://youtu.be/dQw4w9WgXcQ?t=43
https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=43
```

Both work. The `youtu.be` short form is one character less. Both work on desktop, mobile web, and inside the mobile app.

## Human-readable timestamps

You can also use `1h2m3s`-style timestamps:

```
https://youtu.be/dQw4w9WgXcQ?t=1h2m3s
```

YouTube's copy-link-with-timestamp feature (right-click a video, choose "Copy video URL at current time") uses the seconds form. Both work identically.

## When to share a timestamp vs. share the whole video

Use a timestamp when:

- Answering a specific question that a video covers at a specific point.
- Pointing to a controversial or interesting moment.
- Referencing a chapter you want the reader to watch, not the whole video.

Skip the timestamp when:

- The video's power is cumulative — sharing "the ending" of a documentary robs the viewer of the setup.
- Attribution is important — some creators prefer viewers see the whole video to boost watch time (helpful for the algorithm and their revenue).

## Ranges via the embed player

The `t=` parameter is only for starting the video. To limit a range, you need the embed URL:

```
https://www.youtube.com/embed/VIDEOID?start=90&end=180
```

This embeds the video and plays only from 1:30 to 3:00. Useful for embedding a specific segment in a blog post or documentation.

## Common mistakes

**Mixing up `t=` and `time_continue=`.** You may see YouTube's own share dialog output `&t=90s` or `&time_continue=90&t=90s`. All variants work; the simple `t=90` form is the cleanest.

**Forgetting the URL scheme.** If you paste `youtube.com/watch?v=xxx&t=90` without `https://`, most chat apps will not autolink it. Always include the full URL when sharing.

**Timestamp beyond video length.** If you set `t=` past the video's duration, YouTube plays from the beginning silently. Test your link before sharing.

## Using the generator

The [Timestamp Link Generator](/timestamp) is the least-friction way to make a timestamp link if you do not want to compute seconds mentally:

1. Paste the video URL.
2. Enter hours, minutes, and seconds.
3. Copy the generated link.

The generator handles all URL formats (`youtu.be`, full URLs, shorts) and normalizes them to the compact share form.

## Try it

Pick a video with a moment worth sharing, drop the URL into the [Timestamp Link Generator](/timestamp), and share the resulting link with a friend.

## Related reading

- [How Long Is a YouTube Playlist? The Complete Guide](/blog/how-long-is-a-youtube-playlist)
- [How to Download YouTube Video Thumbnails](/blog/download-youtube-thumbnails)
