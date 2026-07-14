function showError(id, message) {
    var el = document.getElementById(id);
    if (el) {
        el.textContent = message;
        el.classList.remove('hidden');
    }
}

function clearErrors() {
    ['search_string_error', 'api_error'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });
}

function msg(key, fallback) {
    return (window.__formI18n && window.__formI18n[key]) || fallback;
}

function validateForm() {
    clearErrors();
    var searchEl = document.querySelector('textarea[name="search_string"]');
    var apiEl = document.querySelector('input[name="youtube_api"]');
    if (!searchEl) return true;

    var searchString = searchEl.value.trim();
    var youtubeApi = apiEl ? apiEl.value : '';
    var lines = searchString.split('\n');
    if (lines.length > 5) {
        showError('search_string_error', msg('maxLines', 'Please enter no more than 5 lines.'));
        return false;
    }
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (line.length > 0 && line.length < 10) {
            showError('search_string_error', msg('minLineLength', 'Each line must be at least 10 characters long.'));
            return false;
        }
    }
    if (youtubeApi && !/^[a-zA-Z0-9\-_]+$/.test(youtubeApi)) {
        showError('api_error', msg('apiChars', 'API key must only contain alphanumeric characters, hyphens, or underscores.'));
        return false;
    }
    if (youtubeApi && youtubeApi.length < 39) {
        showError('api_error', msg('apiLength', 'API key must be at least 39 characters long.'));
        return false;
    }
    return true;
}

(function () {
    try {
        var form = document.querySelector('form[method="POST"]');
        if (!form) return;
        var ta = form.querySelector('textarea[name="search_string"]');
        if (ta) {
            var saved = localStorage.getItem('ytpl:search_string');
            if (saved && !ta.value) ta.value = saved;
            ta.addEventListener('input', function () {
                try { localStorage.setItem('ytpl:search_string', ta.value); } catch (e) {}
            });
        }
        document.addEventListener('keydown', function (e) {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && form) {
                if (typeof form.requestSubmit === 'function') form.requestSubmit();
                else form.submit();
            }
        });
    } catch (e) { /* no-op */ }
})();
