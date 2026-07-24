from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.services.http_client import ExternalApiError, get_json


class DictionaryLookupError(Exception):
    """Raised when the external dictionary has no entry for the headword."""


@dataclass
class EnDictionaryData:
    ipa: str | None
    definition: str | None
    part_of_speech: str | None


def fetch_en_dictionary_data(headword: str) -> EnDictionaryData:
    settings = get_settings()
    url = f"{settings.en_dictionary_api_base_url}/{quote(headword, safe='')}"

    try:
        entries = get_json(url)
    except ExternalApiError as exc:
        cause = exc.__cause__
        if isinstance(cause, httpx.HTTPStatusError) and cause.response.status_code == 404:
            raise DictionaryLookupError(f"No dictionary entry found for '{headword}'") from exc
        raise

    if not isinstance(entries, list) or not entries:
        raise DictionaryLookupError(f"No dictionary entry found for '{headword}'")

    entry = entries[0]

    ipa = entry.get("phonetic") or None
    if not ipa:
        for phonetic in entry.get("phonetics") or []:
            if phonetic.get("text"):
                ipa = phonetic["text"]
                break

    definition = None
    part_of_speech = None
    meanings = entry.get("meanings") or []
    if meanings:
        first_meaning = meanings[0]
        part_of_speech = first_meaning.get("partOfSpeech") or None
        definitions = first_meaning.get("definitions") or []
        if definitions:
            definition = definitions[0].get("definition") or None

    return EnDictionaryData(ipa=ipa, definition=definition, part_of_speech=part_of_speech)
