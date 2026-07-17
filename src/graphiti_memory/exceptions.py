"""Custom exceptions for Graphiti memory system."""

from __future__ import annotations

from typing import Any


class GraphitiMemoryError(Exception):
    """Base exception for Graphiti memory system."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConnectionError(GraphitiMemoryError):
    """Failed to connect to Graphiti database."""

    pass


class ConfigurationError(GraphitiMemoryError):
    """Invalid configuration."""

    pass


class MemoryStorageError(GraphitiMemoryError):
    """Failed to store memory."""

    pass


class MemoryRetrievalError(GraphitiMemoryError):
    """Failed to retrieve memory."""

    pass


class MemoryNotFoundError(GraphitiMemoryError):
    """Memory not found."""

    def __init__(self, uuid: str):
        super().__init__(f"Memory not found: {uuid}", {"uuid": uuid})
        self.uuid = uuid


class DuplicateMemoryError(GraphitiMemoryError):
    """Attempted to create duplicate memory."""

    def __init__(self, existing_uuid: str, similarity_score: float):
        super().__init__(
            f"Similar memory already exists (UUID: {existing_uuid}, similarity: {similarity_score:.2%})",
            {"existing_uuid": existing_uuid, "similarity_score": similarity_score},
        )
        self.existing_uuid = existing_uuid
        self.similarity_score = similarity_score


class ValidationError(GraphitiMemoryError):
    """Validation failed."""

    pass


class TimeoutError(GraphitiMemoryError):
    """Operation timed out."""

    def __init__(self, operation: str, timeout_seconds: float):
        super().__init__(
            f"Operation '{operation}' timed out after {timeout_seconds}s",
            {"operation": operation, "timeout_seconds": timeout_seconds},
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class LLMError(GraphitiMemoryError):
    """LLM operation failed."""

    pass


class EmbeddingError(GraphitiMemoryError):
    """Embedding operation failed."""

    pass


class GraphOperationError(GraphitiMemoryError):
    """Graph database operation failed."""

    pass


class InsufficientConfidenceError(GraphitiMemoryError):
    """Memory confidence below threshold for operation."""

    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            f"Confidence {confidence:.2%} below threshold {threshold:.2%}",
            {"confidence": confidence, "threshold": threshold},
        )
        self.confidence = confidence
        self.threshold = threshold
