from app.core.config import get_settings
from app.services.http_client import get_json


class TranslationApiError(Exception):
    """Raised when MyMemory reports a non-200 responseStatus in the response body."""


def fetch_de_to_zh_translation(headword: str) -> str:
    settings = get_settings()
    params = {"q": headword, "langpair": "de|zh"}

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
