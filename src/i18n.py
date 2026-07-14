"""
Minimal i18n module: loads JSON locale files, provides a translator factory,
and exposes the canonical list of supported locales.
"""
import json
import os
from dataclasses import dataclass
from typing import Callable, Dict

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")

@dataclass
class LocaleInfo:
    code: str
    native_name: str
    english_name: str
    rtl: bool = False
    og_locale: str = ""

    def __post_init__(self):
        if not self.og_locale:
            self.og_locale = self.code.replace("-", "_")


SUPPORTED_LOCALES: list[LocaleInfo] = [
    LocaleInfo("en", "English", "English", og_locale="en_US"),
    LocaleInfo("es", "Español", "Spanish", og_locale="es_ES"),
    LocaleInfo("hi", "हिन्दी", "Hindi", og_locale="hi_IN"),
    LocaleInfo("zh", "中文", "Chinese", og_locale="zh_CN"),
    LocaleInfo("ar", "العربية", "Arabic", rtl=True, og_locale="ar_SA"),
    LocaleInfo("pt", "Português", "Portuguese", og_locale="pt_BR"),
    LocaleInfo("ru", "Русский", "Russian", og_locale="ru_RU"),
    LocaleInfo("ja", "日本語", "Japanese", og_locale="ja_JP"),
    LocaleInfo("de", "Deutsch", "German", og_locale="de_DE"),
    LocaleInfo("fr", "Français", "French", og_locale="fr_FR"),
    LocaleInfo("id", "Bahasa Indonesia", "Indonesian", og_locale="id_ID"),
    LocaleInfo("it", "Italiano", "Italian", og_locale="it_IT"),
    LocaleInfo("nl", "Nederlands", "Dutch", og_locale="nl_NL"),
    LocaleInfo("pl", "Polski", "Polish", og_locale="pl_PL"),
    LocaleInfo("ko", "한국어", "Korean", og_locale="ko_KR"),
    LocaleInfo("vi", "Tiếng Việt", "Vietnamese", og_locale="vi_VN"),
    LocaleInfo("tl", "Filipino", "Filipino", og_locale="tl_PH"),
    LocaleInfo("bn", "বাংলা", "Bengali", og_locale="bn_IN"),
    LocaleInfo("ta", "தமிழ்", "Tamil", og_locale="ta_IN"),
    LocaleInfo("te", "తెలుగు", "Telugu", og_locale="te_IN"),
    LocaleInfo("mr", "मराठी", "Marathi", og_locale="mr_IN"),
    LocaleInfo("gu", "ગુજરાતી", "Gujarati", og_locale="gu_IN"),
    LocaleInfo("kn", "ಕನ್ನಡ", "Kannada", og_locale="kn_IN"),
    LocaleInfo("ml", "മലയാളം", "Malayalam", og_locale="ml_IN"),
    LocaleInfo("pa", "ਪੰਜਾਬੀ", "Punjabi", og_locale="pa_IN"),
    LocaleInfo("or", "ଓଡ଼ିଆ", "Odia", og_locale="or_IN"),
    LocaleInfo("ur", "اردو", "Urdu", rtl=True, og_locale="ur_PK"),
]

LOCALE_CODES = {loc.code for loc in SUPPORTED_LOCALES}
LOCALE_MAP = {loc.code: loc for loc in SUPPORTED_LOCALES}

_translations: Dict[str, dict] = {}


def load_locales() -> None:
    """Load all locale JSON files into memory. Called once at app startup."""
    for loc in SUPPORTED_LOCALES:
        path = os.path.join(LOCALES_DIR, f"{loc.code}.json")
        try:
            with open(path, encoding="utf-8") as f:
                _translations[loc.code] = json.load(f)
        except FileNotFoundError:
            _translations[loc.code] = {}


def get_translator(lang: str) -> Callable[[str], str]:
    """
    Return a t(key, **kwargs) function for the given language code.
    Falls back to English, then returns the key itself.
    """
    translations = _translations.get(lang, {})
    english = _translations.get("en", {})

    def t(key: str, **kwargs) -> str:
        value = translations.get(key) or english.get(key) or key
        if kwargs:
            try:
                value = value.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return value

    return t
