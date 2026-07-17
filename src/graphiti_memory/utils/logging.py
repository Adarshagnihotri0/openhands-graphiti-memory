"""Structured logging utilities for Graphiti memory system."""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator
from uuid import UUID

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer

from graphiti_memory.config.settings import GraphitiConfig


def configure_logging(config: GraphitiConfig) -> structlog.BoundLogger:
    """Configure structured logging for the memory system."""
    # Set log level
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            JSONRenderer() if config.log_level == "DEBUG" else ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger("graphiti_memory")


class MemoryMetrics:
    """Collect and track memory system metrics."""

    def __init__(self) -> None:
        self.retrieval_count = 0
        self.storage_count = 0
        self.update_count = 0
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0
        self.total_retrieval_time_ms = 0.0
        self.total_storage_time_ms = 0.0

    def record_retrieval(self, latency_ms: float, hit: bool) -> None:
        """Record a retrieval operation."""
        self.retrieval_count += 1
        self.total_retrieval_time_ms += latency_ms
        if hit:
            self.hit_count += 1
        else:
            self.miss_count += 1

    def record_storage(self, latency_ms: float) -> None:
        """Record a storage operation."""
        self.storage_count += 1
        self.total_storage_time_ms += latency_ms

    def record_update(self) -> None:
        """Record an update operation."""
        self.update_count += 1

    def record_error(self) -> None:
        """Record an error."""
        self.error_count += 1

    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0

    def get_avg_retrieval_latency_ms(self) -> float:
        """Get average retrieval latency in milliseconds."""
        return (
            self.total_retrieval_time_ms / self.retrieval_count
            if self.retrieval_count > 0
            else 0.0
        )

    def get_avg_storage_latency_ms(self) -> float:
        """Get average storage latency in milliseconds."""
        return self.total_storage_time_ms / self.storage_count if self.storage_count > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "retrieval_count": self.retrieval_count,
            "storage_count": self.storage_count,
            "update_count": self.update_count,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "error_count": self.error_count,
            "hit_rate": self.get_hit_rate(),
            "avg_retrieval_latency_ms": self.get_avg_retrieval_latency_ms(),
            "avg_storage_latency_ms": self.get_avg_storage_latency_ms(),
        }


class MemoryLogger:
    """Enhanced logger with memory-specific functionality."""

    def __init__(self, config: GraphitiConfig) -> None:
        self.config = config
        self.logger = configure_logging(config)
        self.metrics = MemoryMetrics() if config.enable_metrics else None

    @contextmanager
    def log_operation(
        self,
        operation: str,
        uuid: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[None]:
        """Context manager to log an operation with timing."""
        start_time = datetime.utcnow()
        context = {
            "operation": operation,
            "start_time": start_time.isoformat(),
        }
        if uuid:
            context["memory_uuid"] = str(uuid)
        if metadata:
            context.update(metadata)

        self.logger.info(f"Starting {operation}", **context)

        try:
            yield
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            context["latency_ms"] = round(latency_ms, 2)
            context["status"] = "success"

            self.logger.info(f"Completed {operation}", **context)

            # Record metrics
            if self.metrics:
                if operation == "retrieve":
                    self.metrics.record_retrieval(latency_ms, hit=True)
                elif operation == "store":
                    self.metrics.record_storage(latency_ms)
                elif operation == "update":
                    self.metrics.record_update()

        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            context["latency_ms"] = round(latency_ms, 2)
            context["status"] = "error"
            context["error_type"] = type(e).__name__
            context["error_message"] = str(e)

            self.logger.error(f"Failed {operation}", **context)

            if self.metrics:
                self.metrics.record_error()

            raise

    def log_memory_created(
        self,
        uuid: UUID,
        memory_type: str,
        title: str,
        confidence: float,
    ) -> None:
        """Log memory creation."""
        self.logger.info(
            "Memory created",
            memory_uuid=str(uuid),
            memory_type=memory_type,
            title=title,
            confidence=confidence,
        )

    def log_memory_retrieved(
        self,
        uuid: UUID,
        score: float,
        query: str,
        retrieval_method: str,
    ) -> None:
        """Log memory retrieval."""
        self.logger.debug(
            "Memory retrieved",
            memory_uuid=str(uuid),
            score=score,
            query=query[:100],  # Truncate long queries
            retrieval_method=retrieval_method,
        )

    def log_memory_updated(self, uuid: UUID, fields_updated: list[str]) -> None:
        """Log memory update."""
        self.logger.info(
            "Memory updated",
            memory_uuid=str(uuid),
            fields_updated=fields_updated,
        )

    def log_search_query(
        self,
        query: str,
        results_count: int,
        latency_ms: float,
    ) -> None:
        """Log search query."""
        self.logger.info(
            "Search executed",
            query=query[:100],
            results_count=results_count,
            latency_ms=round(latency_ms, 2),
        )

    def log_graphiti_failure(self, error: Exception, operation: str) -> None:
        """Log Graphiti failure."""
        self.logger.error(
            "Graphiti operation failed",
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
        )

    def log_fallback_activated(self, reason: str) -> None:
        """Log fallback mode activation."""
        self.logger.warning(
            "Fallback mode activated",
            reason=reason,
        )

    def get_metrics(self) -> dict[str, Any] | None:
        """Get current metrics."""
        return self.metrics.to_dict() if self.metrics else None
