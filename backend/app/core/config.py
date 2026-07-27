from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./data/immersion_tracker.db"

    en_dictionary_api_base_url: str = "https://api.dictionaryapi.dev/api/v2/entries/en"
    de_dictionary_api_base_url: str = ""
    de_translation_api_base_url: str = "https://api.mymemory.translated.net/get"

    llm_api_key: str | None = None

    # Seed value only — used to create the app_settings DB row (see
    # app/services/app_settings.py) the first time it's read. After that, the
    # persisted DB value is the source of truth (adjustable via GET/PATCH
    # /settings), not this constant.
    daily_new_card_limit: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
