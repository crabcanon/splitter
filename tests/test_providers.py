from core.config import Settings
from providers.factory import ProviderFactory


def test_provider_factory_uses_default_llm_env(monkeypatch) -> None:
    monkeypatch.setenv("SPLITTER_LLM_PROVIDER", "openai")
    monkeypatch.setenv("SPLITTER_LLM_MODEL", "gpt-test")
    monkeypatch.setenv("SPLITTER_LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("SPLITTER_LLM_API_KEY", "test-key")

    bundle = ProviderFactory(Settings.from_env()).build_bundle()

    assert bundle.llm is not None
    assert bundle.llm.provider_name == "openai"
    assert bundle.llm.model_name == "gpt-test"
    assert bundle.llm.base_url == "https://llm.example/v1"
    assert bundle.summary()["llm"].api_key_configured is True
