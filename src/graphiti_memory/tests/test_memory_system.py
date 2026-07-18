"""Tests for Graphiti memory system."""

from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4

import pytest

from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import (
    ArchitectureMemory,
    BugFixMemory,
    ConfidenceLevel,
    DecisionMemory,
    MemoryQuery,
    MemoryType,
)
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.utils.logging import MemoryLogger


@pytest.fixture
def config():
    """Create test configuration."""
    return GraphitiConfig(
        database_provider="falkordb",
        database_uri="redis://localhost:6379",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        repository_scope="test_repo",
        retrieval_limit=10,
        confidence_threshold=0.7,
    )


@pytest.fixture
def logger(config):
    """Create test logger."""
    return MemoryLogger(config)


@pytest.fixture
def scorer(config, logger):
    """Create test scorer."""
    return MemoryScorer(config, logger)


class TestMemoryScorer:
    """Tests for memory scoring logic."""

    def test_should_remember_architecture(self, scorer):
        """Test that architecture content is recognized."""
        content = "AuthService depends on TokenService for JWT validation"
        should_remember, confidence, memory_type = scorer.should_remember(content)

        assert should_remember is True
        assert confidence >= 0.5
        assert memory_type in [MemoryType.ARCHITECTURE.value, MemoryType.RELATIONSHIP.value]

    def test_should_remember_decision(self, scorer):
        """Test that design decisions are recognized."""
        content = "We chose PostgreSQL over MongoDB because we need ACID transactions"
        should_remember, confidence, memory_type = scorer.should_remember(content)

        assert should_remember is True
        assert memory_type == MemoryType.DECISION.value

    def test_should_remember_bug_fix(self, scorer):
        """Test that bug fixes are recognized."""
        content = "Fixed race condition in Redis cache by adding distributed lock"
        should_remember, confidence, memory_type = scorer.should_remember(content)

        assert should_remember is True
        assert memory_type == MemoryType.BUG_FIX.value

    def test_should_not_remember_greeting(self, scorer):
        """Test that conversational content is not stored."""
        content = "Hello, can you help me with something?"
        should_remember, confidence, memory_type = scorer.should_remember(content)

        assert should_remember is False
        assert confidence < 0.3

    def test_should_not_remember_stack_trace(self, scorer):
        """Test that raw stack traces are not stored."""
        content = """
        Traceback (most recent call last):
          File "app.py", line 42, in <module>
            raise ValueError("test")
        ValueError: test
        """
        should_remember, confidence, memory_type = scorer.should_remember(content)

        # Should not remember raw stack trace
        assert should_remember is False or confidence < 0.5

    def test_confidence_level_calculation(self, scorer):
        """Test confidence level calculation."""
        assert scorer.calculate_confidence_level(0.98) == ConfidenceLevel.VERIFIED
        assert scorer.calculate_confidence_level(0.90) == ConfidenceLevel.HIGH
        assert scorer.calculate_confidence_level(0.75) == ConfidenceLevel.MEDIUM
        assert scorer.calculate_confidence_level(0.50) == ConfidenceLevel.LOW

    def test_memory_similarity(self, scorer):
        """Test similarity calculation between memories."""
        memory1 = ArchitectureMemory(
            title="Auth Service Architecture",
            content="AuthService depends on TokenService",
            component_type="service",
            dependencies=["TokenService"],
            repository="test",
        )

        memory2 = ArchitectureMemory(
            title="Auth Service Dependencies",
            content="AuthService uses TokenService",
            component_type="service",
            dependencies=["TokenService"],
            repository="test",
        )

        similarity = scorer.calculate_similarity(memory1, memory2)
        assert similarity >= 0.5  # Should detect similarity

    def test_memory_importance_calculation(self, scorer):
        """Test importance calculation."""
        high_confidence_memory = ArchitectureMemory(
            title="Critical Architecture",
            content="Core system architecture",
            component_type="system",
            confidence=0.95,
            confidence_level=ConfidenceLevel.VERIFIED,
        )

        low_confidence_memory = ArchitectureMemory(
            title="Minor Detail",
            content="Minor detail",
            component_type="module",
            confidence=0.6,
        )

        high_importance = scorer.calculate_memory_importance(high_confidence_memory)
        low_importance = scorer.calculate_memory_importance(low_confidence_memory)

        assert high_importance > low_importance


class TestMemoryModels:
    """Tests for memory data models."""

    def test_architecture_memory_creation(self):
        """Test creating architecture memory."""
        memory = ArchitectureMemory(
            title="API Gateway Architecture",
            content="API Gateway routes to microservices",
            component_type="gateway",
            dependencies=["AuthService", "UserService"],
            interfaces=["REST API", "GraphQL"],
            repository="myapp",
        )

        assert memory.memory_type == MemoryType.ARCHITECTURE
        assert memory.component_type == "gateway"
        assert len(memory.dependencies) == 2

    def test_decision_memory_creation(self):
        """Test creating decision memory."""
        memory = DecisionMemory(
            title="Database Selection",
            content="Selected PostgreSQL for ACID compliance",
            decision_type="database",
            rationale="Need ACID transactions for financial data",
            alternatives_considered=["MongoDB", "Cassandra"],
            trade_offs="Slower writes than NoSQL",
        )

        assert memory.memory_type == MemoryType.DECISION
        assert len(memory.alternatives_considered) == 2

    def test_bug_fix_memory_creation(self):
        """Test creating bug fix memory."""
        memory = BugFixMemory(
            title="Race Condition in Cache",
            content="Fixed race condition by adding distributed lock",
            bug_type="race condition",
            root_cause="Concurrent cache updates without locking",
            solution="Implemented Redis distributed lock with Redlock",
            symptoms=["Inconsistent cache state", "Stale reads"],
            prevention="Use distributed locks for concurrent writes",
        )

        assert memory.memory_type == MemoryType.BUG_FIX
        assert memory.bug_type == "race condition"
        assert len(memory.symptoms) == 2

    def test_memory_to_episode_content(self):
        """Test converting memory to episode content."""
        memory = ArchitectureMemory(
            title="Test Architecture",
            content="Test content",
            component_type="service",
            module="auth",
            tags=["test", "architecture"],
            repository="myapp",
        )

        episode_content = memory.to_episode_content()

        assert "[ARCHITECTURE]" in episode_content
        assert "Test Architecture" in episode_content
        assert "Test content" in episode_content
        assert "auth" in episode_content
        assert "test, architecture" in episode_content

    def test_memory_query_creation(self):
        """Test creating memory query."""
        query = MemoryQuery(
            query_text="find authentication service",
            memory_types=[MemoryType.ARCHITECTURE, MemoryType.DECISION],
            min_confidence=0.7,
            limit=20,
        )

        assert query.query_text == "find authentication service"
        assert len(query.memory_types) == 2
        assert query.limit == 20

    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        memory = ArchitectureMemory(
            title="Test",
            content="Test",
            component_type="service",
            confidence=0.756789,
        )

        # Should be rounded to 2 decimal places
        assert memory.confidence == 0.76


class TestLogger:
    """Tests for logging functionality."""

    def test_logger_initialization(self, config):
        """Test logger can be initialized."""
        logger = MemoryLogger(config)
        assert logger.config == config
        assert logger.metrics is not None

    def test_metrics_recording(self, logger):
        """Test metrics are recorded correctly."""
        logger.metrics.record_retrieval(100.5, hit=True)
        logger.metrics.record_storage(50.2)
        logger.metrics.record_error()

        metrics = logger.get_metrics()

        assert metrics["retrieval_count"] == 1
        assert metrics["storage_count"] == 1
        assert metrics["error_count"] == 1
        assert metrics["hit_rate"] == 1.0
        assert metrics["avg_retrieval_latency_ms"] == 100.5

    def test_metrics_with_misses(self, logger):
        """Test hit rate calculation with misses."""
        logger.metrics.record_retrieval(50.0, hit=True)
        logger.metrics.record_retrieval(60.0, hit=False)

        metrics = logger.get_metrics()
        assert metrics["hit_rate"] == 0.5


class TestConfiguration:
    """Tests for configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = GraphitiConfig()

        assert config.database_provider == "neo4j"
        assert config.llm_model == "gpt-4o-mini"
        assert config.retrieval_limit == 10
        assert config.confidence_threshold == 0.7

    def test_scoped_group_id(self, config):
        """Test scoped group ID generation."""
        config.repository_scope = "myrepo"
        config.branch_scope = "develop"
        config.group_id = "project"

        scoped_id = config.get_scoped_group_id()

        assert scoped_id == "myrepo_develop_project"

    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid group_id should raise error
        with pytest.raises(ValueError):
            config = GraphitiConfig(group_id="invalid group id!")


@pytest.mark.asyncio
class TestMemoryService:
    """Tests for memory service (integration tests)."""

    async def test_store_and_retrieve_memory(self, config):
        """Test storing and retrieving a memory."""
        from graphiti_memory.client.graphiti_client import GraphitiClient
        from graphiti_memory.service.memory_service import MemoryService
        from graphiti_memory.models import ArchitectureMemory, MemoryQuery
        
        # Skip if no API key
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("Requires OPENAI_API_KEY environment variable")
        
        # Initialize client and service
        logger = MemoryLogger(config)
        client = GraphitiClient(config, logger)
        await client.initialize()
        
        scorer = MemoryScorer(config, logger)
        service = MemoryService(config, client, scorer, logger)
        
        try:
            # Store a memory
            memory = ArchitectureMemory(
                title="Test Architecture",
                content="TestService depends on MockService for testing",
                component_type="service",
                dependencies=["MockService"],
                repository="test_repo",
                confidence=0.9
            )
            
            await service.store_memory(memory)
            
            # Retrieve it
            query = MemoryQuery(
                query_text="Test Architecture",
                repositories=["test_repo"],
                limit=1
            )
            
            results = await service.search_memories(query)
            
            assert len(results) > 0, "Should retrieve stored memory"
            assert results[0].memory.title == "Test Architecture"
            
        finally:
            await client.close()

    async def test_search_memories(self, config):
        """Test searching for memories."""
        from graphiti_memory.client.graphiti_client import GraphitiClient
        from graphiti_memory.service.memory_service import MemoryService
        from graphiti_memory.models import DecisionMemory, MemoryQuery
        
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("Requires OPENAI_API_KEY environment variable")
        
        logger = MemoryLogger(config)
        client = GraphitiClient(config, logger)
        await client.initialize()
        
        scorer = MemoryScorer(config, logger)
        service = MemoryService(config, client, scorer, logger)
        
        try:
            # Store a decision
            memory = DecisionMemory(
                title="Test Decision",
                content="We chose PostgreSQL for ACID compliance",
                decision_type="database",
                rationale="Need ACID transactions",
                alternatives_considered=["MongoDB"],
                repository="test_repo",
                confidence=0.85
            )
            
            await service.store_memory(memory)
            
            # Search for it
            query = MemoryQuery(
                query_text="database choice",
                repositories=["test_repo"],
                limit=5
            )
            
            results = await service.search_memories(query)
            
            assert len(results) > 0, "Should find relevant memories"
            
        finally:
            await client.close()

    async def test_deduplication(self, config):
        """Test duplicate detection."""
        from graphiti_memory.client.graphiti_client import GraphitiClient
        from graphiti_memory.service.memory_service import MemoryService
        from graphiti_memory.models import BugFixMemory, MemoryQuery
        
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("Requires OPENAI_API_KEY environment variable")
        
        logger = MemoryLogger(config)
        client = GraphitiClient(config, logger)
        await client.initialize()
        
        scorer = MemoryScorer(config, logger)
        service = MemoryService(config, client, scorer, logger)
        
        try:
            # Store same memory twice
            memory1 = BugFixMemory(
                title="Duplicate Test",
                content="Fixed bug in test module",
                bug_type="logic",
                root_cause="Incorrect condition",
                solution="Fixed condition",
                prevention="Add tests",
                repository="test_repo",
                confidence=0.8
            )
            
            memory2 = BugFixMemory(
                title="Duplicate Test",
                content="Fixed bug in test module",
                bug_type="logic",
                root_cause="Incorrect condition",
                solution="Fixed condition",
                prevention="Add tests",
                repository="test_repo",
                confidence=0.8
            )
            
            await service.store_memory(memory1)
            await service.store_memory(memory2)
            
            # Should deduplicate
            query = MemoryQuery(
                query_text="bug fix test",
                repositories=["test_repo"],
                limit=10
            )
            
            results = await service.search_memories(query)
            
            # Should have only one result (deduped)
            duplicates = [r for r in results if r.memory.title == "Duplicate Test"]
            assert len(duplicates) <= 1, "Should deduplicate similar memories"
            
        finally:
            await client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
