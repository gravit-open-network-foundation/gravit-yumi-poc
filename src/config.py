#!/usr/bin/env python3
"""
Configuration for Gravit Epistemic Verifier
Uses Pydantic Settings for type-safe configuration
"""

from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMProvider(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"


class Settings(BaseSettings):
    """Main application configuration"""

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    websocket_port: int = 8081
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])

    # Verification thresholds
    semantic_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    policy_strictness: float = Field(default=0.8, ge=0.0, le=1.0)
    adversarial_detection_enabled: bool = True
    adversarial_sensitivity: float = Field(default=0.7, ge=0.0, le=1.0)

    # Trust score thresholds (0-255)
    trust_approve_threshold: int = Field(default=217, ge=0, le=255)  # 85%
    trust_review_threshold: int = Field(default=153, ge=0, le=255)   # 60%

    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.MOCK
    llm_model: str = "gpt-4"
    llm_temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    llm_max_tokens: int = 500
    llm_timeout: int = 30

    # API Keys (from environment)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    grok_api_key: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_ttl_seconds: int = 3600

    # Audit
    audit_storage_path: str = "./audit_logs"
    enable_cryptographic_signatures: bool = True

    # Performance
    max_concurrent_requests: int = 100
    request_timeout_seconds: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "forbid"  # Reject unknown variables


    # Global configuration instance
settings = Settings()
