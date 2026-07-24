from app.core.config import Settings, get_settings


def test_defaults_without_env_file(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("EN_DICTIONARY_API_BASE_URL", raising=False)
    monkeypatch.delenv("DE_DICTIONARY_API_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./data/immersion_tracker.db"
    assert settings.en_dictionary_api_base_url == "https://api.dictionaryapi.dev/api/v2/entries/en"
    assert settings.de_dictionary_api_base_url == ""
    assert settings.llm_api_key is None


def test_env_vars_override_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/custom.db")
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./data/custom.db"
    assert settings.llm_api_key == "test-key"


def test_get_settings_is_cached():
    assert get_settings() is get_settings()
