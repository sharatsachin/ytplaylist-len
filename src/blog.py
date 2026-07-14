"""
Blog post loader: parses YAML frontmatter + Markdown from content/blog/{lang}/*.md.
Falls back to English when a translation is not available.
"""
import os
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

try:
    from markdown_it import MarkdownIt
    _md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": True}).enable("table")
except ImportError:
    _md = None

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content", "blog")


@dataclass
class BlogPost:
    slug: str
    title: str
    description: str
    date: str
    updated: str = ""
    author: str = "Sharat Sachin"
    tags: list = field(default_factory=list)
    reading_time: int = 5
    hero_image: str = ""
    faq: list = field(default_factory=list)
    body_html: str = ""
    lang: str = "en"
    is_translated: bool = True

    @property
    def date_iso(self) -> str:
        return self.date

    @property
    def date_display(self) -> str:
        try:
            return date.fromisoformat(self.date).strftime("%B %d, %Y")
        except (ValueError, TypeError):
            return self.date


_cache: dict[str, list[BlogPost]] = {}


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Very small YAML frontmatter parser; only supports flat scalar / list values."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")

    meta: dict = {}
    current_list_key: Optional[str] = None
    faq_current: Optional[dict] = None
    faq_list: list = []
    for raw in fm_text.split("\n"):
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("  - q:"):
            faq_current = {"q": line.split(":", 1)[1].strip().strip('"').strip("'")}
            faq_list.append(faq_current)
            continue
        if line.startswith("    a:") and faq_current is not None:
            faq_current["a"] = line.split(":", 1)[1].strip().strip('"').strip("'")
            continue
        if line.startswith("  - "):
            if current_list_key:
                meta.setdefault(current_list_key, []).append(line[4:].strip().strip('"').strip("'"))
            continue
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                current_list_key = key
                if key == "faq":
                    meta[key] = faq_list
                else:
                    meta.setdefault(key, [])
            else:
                current_list_key = None
                meta[key] = value.strip('"').strip("'")
    if faq_list:
        meta["faq"] = faq_list
    return meta, body


def _render_body(md_text: str) -> str:
    if _md is None:
        return f"<pre>{md_text}</pre>"
    return _md.render(md_text)


def _load_post_file(path: str, lang: str) -> Optional[BlogPost]:
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return None
    meta, body = _parse_frontmatter(raw)
    slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        reading_time = int(meta.get("reading_time", 5))
    except (ValueError, TypeError):
        reading_time = max(1, len(body.split()) // 200)
    return BlogPost(
        slug=slug,
        title=meta.get("title", slug),
        description=meta.get("description", ""),
        date=meta.get("date", "2026-01-01"),
        updated=meta.get("updated", ""),
        author=meta.get("author", "Sharat Sachin"),
        tags=tags,
        reading_time=reading_time,
        hero_image=meta.get("hero_image", ""),
        faq=meta.get("faq", []),
        body_html=_render_body(body),
        lang=lang,
    )


def load_posts(lang: str = "en") -> list[BlogPost]:
    """Return all posts for a language, falling back to English."""
    if lang in _cache:
        return _cache[lang]
    posts: list[BlogPost] = []
    lang_dir = os.path.join(CONTENT_DIR, lang)
    en_dir = os.path.join(CONTENT_DIR, "en")
    seen: set[str] = set()

    if os.path.isdir(lang_dir):
        for fname in sorted(os.listdir(lang_dir)):
            if fname.endswith(".md"):
                p = _load_post_file(os.path.join(lang_dir, fname), lang)
                if p:
                    posts.append(p)
                    seen.add(p.slug)

    if lang != "en" and os.path.isdir(en_dir):
        for fname in sorted(os.listdir(en_dir)):
            if fname.endswith(".md"):
                slug = os.path.splitext(fname)[0]
                if slug in seen:
                    continue
                p = _load_post_file(os.path.join(en_dir, fname), lang)
                if p:
                    p.is_translated = False
                    posts.append(p)

    posts.sort(key=lambda p: p.date, reverse=True)
    _cache[lang] = posts
    return posts


def get_post(slug: str, lang: str = "en") -> Optional[BlogPost]:
    for post in load_posts(lang):
        if post.slug == slug:
            return post
    return None


def get_related(post: BlogPost, lang: str = "en", limit: int = 3) -> list[BlogPost]:
    all_posts = [p for p in load_posts(lang) if p.slug != post.slug]
    scored = []
    for other in all_posts:
        overlap = len(set(post.tags) & set(other.tags))
        if overlap > 0:
            scored.append((overlap, other))
    scored.sort(key=lambda x: (-x[0], x[1].date), reverse=False)
    related = [p for _, p in scored[:limit]]
    if len(related) < limit:
        for other in all_posts:
            if other not in related:
                related.append(other)
            if len(related) >= limit:
                break
    return related
