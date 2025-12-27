"""Configuration management with Pydantic validation."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScopeConfig(BaseModel):
    """Scope configuration for allowed targets."""

    allowed_ips: List[str] = Field(default_factory=list, description="Allowed IP ranges")
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains")
    strict_mode: bool = Field(default=True, description="Enforce strict scope checking")


class OllamaConfig(BaseModel):
    """Ollama LLM configuration."""

    model: str = Field(default="llama3.2", description="Ollama model name")
    base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")


class GeminiConfig(BaseModel):
    """Gemini API configuration."""

    api_key: str = Field(default="", description="Gemini API key (optional)")


class OpenAIConfig(BaseModel):
    """OpenAI API configuration (future support)."""

    api_key: str = Field(default="", description="OpenAI API key")


class LLMConfig(BaseModel):
    """LLM backend configuration."""

    primary_llm: str = Field(
        default="ollama", description="Primary LLM backend: ollama, gemini-cli, google-generativeai"
    )
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)

    @field_validator("primary_llm")
    @classmethod
    def validate_primary_llm(cls, v: str) -> str:
        """Validate primary LLM selection."""
        allowed = ["ollama", "gemini-cli", "google-generativeai", "openai"]
        if v not in allowed:
            raise ValueError(f"primary_llm must be one of {allowed}")
        return v


class SafetyConfig(BaseModel):
    """Safety and security configuration."""

    require_confirmation: bool = Field(default=True, description="Require confirmation for dangerous actions")
    dangerous_actions: List[str] = Field(
        default_factory=lambda: ["exploit", "payload", "inject"],
        description="Keywords that trigger confirmation prompts",
    )
    containerized_execution: bool = Field(default=True, description="Run tools in containers")


class HexstrikeConfig(BaseModel):
    """hexstrike-ai MCP server configuration."""

    server_url: str = Field(default="http://127.0.0.1:8888", description="hexstrike-ai MCP server URL")
    auto_start: bool = Field(default=True, description="Auto-start server if not running")
    timeout: int = Field(default=300, description="Request timeout in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Logging level")
    file: str = Field(default="~/.kali-orchestrator/logs/session.log", description="Log file path")
    json_log: bool = Field(default=True, description="Enable structured JSON logging")


class ReportingConfig(BaseModel):
    """Reporting configuration."""

    default_format: str = Field(default="markdown", description="Default report format")
    include_screenshots: bool = Field(default=True, description="Include screenshots in reports")
    bug_bounty_template: bool = Field(default=True, description="Use bug bounty template format")


class OrchestratorConfig(BaseSettings):
    """Main orchestrator configuration."""

    model_config = SettingsConfigDict(env_prefix="KALI_ORCHESTRATOR_", case_sensitive=False)

    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    hexstrike: HexstrikeConfig = Field(default_factory=HexstrikeConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "OrchestratorConfig":
        """Load configuration from YAML file."""
        if config_path is None:
            # Try multiple locations
            possible_paths = [
                Path("kali_orchestrator/config.yaml"),
                Path("config.yaml"),
                Path.home() / ".kali-orchestrator" / "config.yaml",
            ]
            config_path = None
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break

            if config_path is None:
                # Return default config
                return cls()

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        # Expand ~ in file paths
        if "logging" in config_data and "file" in config_data["logging"]:
            config_data["logging"]["file"] = os.path.expanduser(config_data["logging"]["file"])

        return cls(**config_data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        config_dict = self.model_dump(mode="json", exclude_none=True)
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

