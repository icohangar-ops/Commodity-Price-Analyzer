"""
Configuration management for Commodity Price Analyzer.
Loads settings from environment variables and .env file.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from typing import Optional

# Load .env file
load_dotenv()


@dataclass
class AzureAIConfig:
    """Azure AI Foundry configuration."""
    endpoint: str = field(default_factory=lambda: os.getenv("AZURE_AI_ENDPOINT", ""))
    api_key: str = field(default_factory=lambda: os.getenv("AZURE_AI_KEY", ""))
    deployment: str = field(default_factory=lambda: os.getenv("AZURE_AI_DEPLOYMENT", "Kimi-K2.6"))

    def validate(self) -> bool:
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure AI credentials not found. "
                "Set AZURE_AI_ENDPOINT and AZURE_AI_KEY in your .env file."
            )
        return True


@dataclass
class FabricConfig:
    """Microsoft Fabric configuration."""
    tenant_id: str = field(default_factory=lambda: os.getenv("FABRIC_TENANT_ID", ""))
    workspace_id: str = field(default_factory=lambda: os.getenv("FABRIC_WORKSPACE_ID", ""))
    lakehouse_id: str = field(default_factory=lambda: os.getenv("FABRIC_LAKEHOUSE_ID", ""))
    client_id: str = field(default_factory=lambda: os.getenv("FABRIC_CLIENT_ID", ""))
    client_secret: str = field(default_factory=lambda: os.getenv("FABRIC_CLIENT_SECRET", ""))

    @property
    def workspace_url(self) -> str:
        return f"https://app.fabric.microsoft.com/groups/{self.workspace_id}"

    @property
    def api_base(self) -> str:
        return "https://api.fabric.microsoft.com/v1"

    def validate(self) -> bool:
        required = [self.tenant_id, self.workspace_id, self.client_id]
        if not all(required):
            raise ValueError(
                "Microsoft Fabric credentials incomplete. "
                "Set FABRIC_TENANT_ID, FABRIC_WORKSPACE_ID, FABRIC_CLIENT_ID "
                "in your .env file."
            )
        return True


@dataclass
class DataSourcesConfig:
    """External data source API keys."""
    alphavantage_key: str = field(default_factory=lambda: os.getenv("ALPHAVANTAGE_API_KEY", ""))
    regulations_gov_key: str = field(default_factory=lambda: os.getenv("REGULATIONS_GOV_API_KEY", ""))


@dataclass
class AppConfig:
    """Main application configuration."""
    azure_ai: AzureAIConfig = field(default_factory=AzureAIConfig)
    fabric: FabricConfig = field(default_factory=FabricConfig)
    data_sources: DataSourcesConfig = field(default_factory=DataSourcesConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    refresh_interval: int = field(default_factory=lambda: int(os.getenv("DATA_REFRESH_INTERVAL_MINUTES", "60")))
    retention_days: int = field(default_factory=lambda: int(os.getenv("HISTORY_RETENTION_DAYS", "365")))


# Singleton config instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the application configuration."""
    return config
