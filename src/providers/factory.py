from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import SecretStr

from core.config import Settings
from models.schemas import ProviderConfig, ProviderSummary


@dataclass(frozen=True)
class ProviderHandle:
    kind: str
    provider_name: str
    model_name: str
    api_key: SecretStr | None = None
    base_url: str | None = None
    options: dict[str, object] = field(default_factory=dict)

    def summary(self) -> ProviderSummary:
        return ProviderSummary(
            provider_name=self.provider_name,
            model_name=self.model_name,
            base_url=self.base_url,
            api_key_configured=self.api_key is not None,
        )


@dataclass(frozen=True)
class ProviderBundle:
    llm: ProviderHandle | None = None
    embedding: ProviderHandle | None = None
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, ProviderSummary | None]:
        return {
            "llm": self.llm.summary() if self.llm else None,
            "embedding": self.embedding.summary() if self.embedding else None,
        }


class ProviderFactory:
    """Build normalized handles without binding strategies to a concrete SDK."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()

    def build_bundle(self) -> ProviderBundle:
        warnings: list[str] = []
        llm_provider_config = self._config_from_env("LLM", warnings)
        embedding_provider_config = self._config_from_env("EMBEDDING", warnings)
        llm = self._build("llm", llm_provider_config, warnings)
        embedding = self._build("embedding", embedding_provider_config, warnings)
        return ProviderBundle(llm=llm, embedding=embedding, warnings=warnings)

    def _config_from_env(
        self,
        prefix: str,
        warnings: list[str],
    ) -> ProviderConfig | None:
        values = self.settings.provider_env(prefix)
        provider_name = values["provider_name"]
        model_name = values["model_name"]
        if not provider_name and not model_name:
            return None
        if not provider_name or not model_name:
            warnings.append(
                f"SPLITTER_{prefix}_PROVIDER and SPLITTER_{prefix}_MODEL must both "
                "be set; ignoring incomplete default provider config."
            )
            return None
        return ProviderConfig(
            provider_name=provider_name,
            model_name=model_name,
            api_key=values["api_key"] or None,
            base_url=values["base_url"] or None,
        )

    def _build(
        self,
        kind: str,
        config: ProviderConfig | None,
        warnings: list[str],
    ) -> ProviderHandle | None:
        if config is None:
            return None

        provider_name = config.provider_name.strip().lower()
        if provider_name in {"openai", "azure_openai"} and config.api_key is None:
            warnings.append(
                f"{kind} provider '{provider_name}' was configured without api_key; "
                "ignoring incomplete provider config."
            )
            return None

        return ProviderHandle(
            kind=kind,
            provider_name=provider_name,
            model_name=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url,
            options=dict(config.options),
        )
