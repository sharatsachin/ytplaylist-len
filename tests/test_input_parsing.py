"""
Parametrized input → expected-output tests for URL / ID parsing.

Each case is a single user-pasteable line (or multiline block) and the
playlists / videos lists that get_item_ids() should produce.
"""

import pytest

# (input_line, expected_id, expected_type) for ItemList.get_id
GET_ID_CASES = [
    # watch URLs — video
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ", "video"),
    ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ", "video"),
    ("http://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share", "dQw4w9WgXcQ", "video"),
    # youtu.be short links
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ", "video"),
    ("https://youtu.be/dQw4w9WgXcQ?t=42", "dQw4w9WgXcQ", "video"),
    # bare 11-char video ID
    ("dQw4w9WgXcQ", "dQw4w9WgXcQ", "video"),
    # playlist URLs — playlist wins when list= is present
    (
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv",
        "PLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv",
        "playlist",
    ),
    ("https://www.youtube.com/playlist?list=PLabc123xyz", "PLabc123xyz", "playlist"),
    # bare playlist ID (longer than 11 chars, or any non-11-char token)
    ("PLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv", "PLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv", "playlist"),
    ("UUabcdefghijklmnopqrstuvwx", "UUabcdefghijklmnopqrstuvwx", "playlist"),
    # hyphenated bare tokens match the playlist fallback pattern
    ("not-a-url", "not-a-url", "playlist"),
    # v= is matched on any host, not only youtube.com
    ("https://example.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ", "video"),
    # whitespace trimmed
    ("  https://youtu.be/dQw4w9WgXcQ  ", "dQw4w9WgXcQ", "video"),
    # empty
    ("", "invalid", "invalid"),
    ("   ", "invalid", "invalid"),
]

# (multiline input, expected_playlists, expected_videos) for get_item_ids
GET_ITEM_IDS_CASES = [
    ("https://youtu.be/dQw4w9WgXcQ", [], ["dQw4w9WgXcQ"]),
    ("PLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv", ["PLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv"], []),
    (
        "https://youtu.be/aaaaaaaaaaa\nPLbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        ["PLbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"],
        ["aaaaaaaaaaa"],
    ),
    # deduplication preserves first-seen order within each type
    (
        "dQw4w9WgXcQ\ndQw4w9WgXcQ\nhttps://youtu.be/dQw4w9WgXcQ",
        [],
        ["dQw4w9WgXcQ"],
    ),
    (
        "PLone123456789012345678901234\nPLone123456789012345678901234",
        ["PLone123456789012345678901234"],
        [],
    ),
    # blank lines ignored
    (
        "dQw4w9WgXcQ\n\n\nPLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv",
        ["PLrAXtmErZgOeiKm4ygOhk874XkFEdxvRv"],
        ["dQw4w9WgXcQ"],
    ),
    ("", [], []),
    ("not-a-url\nalso-bad", ["not-a-url", "also-bad"], []),
]


class TestGetId:
    @pytest.mark.parametrize("input_line,expected_id,expected_type", GET_ID_CASES)
    def test_get_id(self, itemlist, input_line, expected_id, expected_type):
        il = itemlist("")
        assert il.get_id(input_line) == (expected_id, expected_type)


class TestGetItemIds:
    @pytest.mark.parametrize(
        "input_string,expected_playlists,expected_videos", GET_ITEM_IDS_CASES
    )
    def test_get_item_ids(
        self, itemlist, input_string, expected_playlists, expected_videos
    ):
        il = itemlist(input_string)
        playlists, videos = il.get_item_ids()
        assert playlists == expected_playlists
        assert videos == expected_videos

    def test_structured_output_none_when_no_ids(self, itemlist):
        il = itemlist("garbage input")
        assert il.get_structured_output() is None
