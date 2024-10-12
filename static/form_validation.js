function validateForm() {
    const searchString = document.querySelector('textarea[name="search_string"]').value.trim();
    const youtubeApi = document.querySelector('input[name="youtube_api"]').value;

    // Check search string (no more than 5 lines, and no line less than 10 chars)
    const lines = searchString.split('\n');
    if (lines.length > 5) {
        alert("The search string cannot contain more than 5 rows of text.");
        return false;
    }
    for (let line of lines) {
        if (line.length > 0 && line.length < 10) {
            alert("Each line in the search string must be at least 10 characters long.");
            return false;
        }
    }

    // Check YouTube API key contains only alphanumeric, hyphen, or underscore
    if (youtubeApi && !/^[a-zA-Z0-9\-_]+$/.test(youtubeApi)) {
        alert("YouTube API key must only contain alphanumeric characters, hyphens, or underscores.");
        return false;
    }

    // Check Youtube API key is at least 39 characters long
    if (youtubeApi && youtubeApi.length < 39) {
        alert("YouTube API key must be at least 39 characters long.");
        return false;
    }

    return true; // Form is valid
}