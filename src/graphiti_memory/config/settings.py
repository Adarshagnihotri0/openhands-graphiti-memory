"""Configuration settings for Graphiti memory system."""

from __future__ import annotations

import os

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GraphitiConfig(BaseSettings):
    """Graphiti database configuration."""

    model_config = SettingsConfigDict(env_prefix="GRAPHITI_", env_file=".env", extra="ignore")

    # Database settings
    database_provider: Literal["neo4j", "falkordb"] = Field(
        default="neo4j", description="Graph database provider"
    )
    database_uri: str = Field(default="bolt://localhost:7687", description="Database URI")
    database_user: str = Field(default="neo4j", description="Database username")
    database_password: str = Field(default="password", description="Database password")
    database_name: str = Field(default="openhands_memory", description="Database name")

    # LLM settings
    llm_provider: Literal["openai", "anthropic", "azure_openai"] = Field(
        default="openai", description="LLM provider for entity extraction"
    )
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM temperature")
    llm_api_key: str | None = Field(default=None, description="LLM API key")
    llm_base_url: str | None = Field(default=None, description="LLM API base URL (for proxies)")
    
    # Proxy port detection settings (comma-separated for easier env var usage)
    proxy_ports: str = Field(
        default="2999,3000", 
        description="Comma-separated ports to check for proxy (e.g., '2999,3000')"
    )
    proxy_timeout: int = Field(
        default=2, ge=1, le=10, description="Timeout in seconds for port detection"
    )
    
    def get_proxy_ports(self) -> list[int]:
        """Parse proxy ports from comma-separated string."""
        return [int(p.strip()) for p in self.proxy_ports.split(",")]

    # Embedding settings
    embedder_provider: Literal["openai", "voyage", "sentence_transformers"] = Field(
        default="openai", description="Embedding provider"
    )
    embedder_model: str = Field(
        default="text-embedding-3-small", description="Embedding model name"
    )
    embedder_api_key: str | None = Field(default=None, description="Embedder API key")

    # Memory settings
    group_id: str = Field(
        default="openhands_default", description="Group ID for repository isolation"
    )
    repository_scope: str = Field(
        default="default", description="Repository identifier for multi-repo isolation"
    )
    branch_scope: str = Field(default="main", description="Branch identifier for isolation")

    # Retrieval settings
    retrieval_limit: int = Field(
        default=10, ge=1, le=100, description="Maximum memories to retrieve"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence score for retrieval"
    )
    semantic_weight: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Weight for semantic similarity"
    )
    graph_weight: float = Field(
        default=0.4, ge=0.0, le=1.0, description="Weight for graph traversal"
    )

    # Performance settings
    semaphore_limit: int = Field(
        default=10, ge=1, le=100, description="Concurrent episode processing limit"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, description="Delay between retries in seconds")
    timeout_seconds: float = Field(default=30.0, ge=1.0, description="Operation timeout")

    # Memory lifecycle settings
    memory_expiration_days: int = Field(
        default=365, ge=30, description="Days before memory expiration"
    )
    auto_update_similar: bool = Field(
        default=True, description="Update similar memories instead of creating duplicates"
    )
    min_confidence_to_store: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence to store memory"
    )

    # Observability settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")

    # Failure handling
    fail_silently: bool = Field(
        default=True, description="Continue if Graphiti is unavailable"
    )
    fallback_to_cache: bool = Field(
        default=True, description="Use local cache if Graphiti fails"
    )
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")

    @field_validator("group_id")
    @classmethod
    def validate_group_id(cls, v: str) -> str:
        """Validate group ID format."""
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("group_id must contain only alphanumeric, hyphen, or underscore")
        if len(v) > 64:
            raise ValueError("group_id must be 64 characters or less")
        return v

    def get_scoped_group_id(self) -> str:
        """Get fully scoped group ID including repository and branch."""
        return f"{self.repository_scope}_{self.branch_scope}_{self.group_id}"


class MemoryTypeConfig(BaseSettings):
    """Configuration for memory types and their handling."""

    model_config = SettingsConfigDict(env_prefix="MEMORY_TYPE_", extra="ignore")

    # Entity types for structured extraction
    architecture_entity_type: str = "Architecture"
    decision_entity_type: str = "Decision"
    bug_fix_entity_type: str = "BugFix"
    convention_entity_type: str = "Convention"
    relationship_entity_type: str = "Dependency"
    implementation_entity_type: str = "Implementation"

    # Edge types for relationships
    depends_on_edge: str = "DEPENDS_ON"
    uses_edge: str = "USES"
    implements_edge: str = "IMPLEMENTS"
    fixes_edge: str = "FIXES"
    follows_edge: str = "FOLLOWS"
    conflicts_with_edge: str = "CONFLICTS_WITH"
