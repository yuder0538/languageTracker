from app.core.config import get_settings
from app.services.http_client import get_json


class TranslationApiError(Exception):
    """Raised when MyMemory reports a non-200 responseStatus in the response body."""


def _fetch_zh_translation(headword: str, langpair: str) -> str:
    settings = get_settings()
    params = {"q": headword, "langpair": langpair}

    data = get_json(settings.de_translation_api_base_url, params=params)

    response_status = data.get("responseStatus")
    if str(response_status) != "200":
        raise TranslationApiError(
            f"MyMemory translation failed for '{headword}': "
            f"responseStatus={response_status}"
        )

    translated_text = (data.get("responseData") or {}).get("translatedText")
    if not translated_text:
        raise TranslationApiError(
            f"MyMemory returned no translatedText for '{headword}'"
        )

    return translated_text


def fetch_de_to_zh_translation(headword: str) -> str:
    # "zh" alone resolves to Simplified Chinese on MyMemory; this project's UI
    # and users are Traditional Chinese, so pin the target explicitly.
    return _fetch_zh_translation(headword, "de|zh-TW")


def fetch_en_to_zh_translation(headword: str) -> str:
    return _fetch_zh_translation(headword, "en|zh-TW")
