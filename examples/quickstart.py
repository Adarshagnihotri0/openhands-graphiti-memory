#!/usr/bin/env python
"""
Quickstart example for Graphiti Memory System.

This script demonstrates how to:
1. Initialize the Graphiti memory system
2. Store different types of memories
3. Search and retrieve memories
4. Use the automatic memory pipeline

Usage:
    python examples/quickstart.py
"""

import asyncio
import os
from datetime import datetime

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.models import MemoryQuery
from graphiti_memory.utils.logging import MemoryLogger


async def main():
    """Main quickstart demonstration."""
    
    print("=" * 80)
    print("Graphiti Memory System - Quickstart Example")
    print("=" * 80)
    print()
    
    # Step 1: Initialize Configuration
    print("Step 1: Initializing configuration...")
    config = GraphitiConfig(
        database_provider="neo4j",
        database_uri=os.getenv("GRAPHITI_DATABASE_URI", "bolt://localhost:7687"),
        database_user=os.getenv("GRAPHITI_DATABASE_USER", "neo4j"),
        database_password=os.getenv("GRAPHITI_DATABASE_PASSWORD", "password"),
        llm_api_key=os.getenv("GRAPHITI_LLM_API_KEY", ""),
        repository_scope="quickstart_demo",
        group_id="demo_project",
    )
    print(f"  ✓ Repository: {config.repository_scope}")
    print(f"  ✓ Group ID: {config.get_scoped_group_id()}")
    print()
    
    # Step 2: Initialize Components
    print("Step 2: Initializing components...")
    logger = MemoryLogger(config)
    client = GraphitiClient(config, logger)
    await client.initialize()
    print(f"  ✓ Client connected: {client.is_connected}")
    
    scorer = MemoryScorer(config, logger)
    service = MemoryService(config, client, scorer, logger)
    print(f"  ✓ Memory service ready")
    print()
    
    # Step 3: Store Architecture Knowledge
    print("Step 3: Storing architecture knowledge...")
    arch_uuid = await service.remember_architecture(
        title="Authentication Service Architecture",
        content="AuthService validates JWT tokens and manages user sessions using TokenService",
        component_type="service",
        dependencies=["TokenService", "SessionStore", "UserRepository"],
        interfaces=["validate_token()", "create_session()", "refresh_token()"],
        module="auth",
        service="AuthService",
    )
    print(f"  ✓ Stored: {arch_uuid}")
    print()
    
    # Step 4: Store Design Decision
    print("Step 4: Storing design decision...")
    decision_uuid = await service.remember_decision(
        title="JWT Token Strategy",
        decision_type="security",
        rationale="Stateless JWT tokens enable horizontal scaling without session storage",
        content="Selected JWT tokens for authentication to support microservices architecture. Tokens expire after 15 minutes with automatic refresh.",
        alternatives_considered=["Session cookies", "OAuth2 tokens"],
        trade_offs="Cannot revoke tokens immediately without blacklist",
    )
    print(f"  ✓ Stored: {decision_uuid}")
    print()
    
    # Step 5: Store Bug Fix
    print("Step 5: Storing bug fix discovery...")
    bug_uuid = await service.remember_bug_fix(
        title="Race Condition in Token Refresh",
        bug_type="race condition",
        root_cause="Concurrent refresh requests created duplicate tokens",
        solution="Implemented idempotent refresh using request-idempotency-key header",
        symptoms=["Multiple valid tokens", "Session confusion"],
        prevention="Always use idempotency keys for state-changing operations",
        module="auth/token_refresh",
    )
    print(f"  ✓ Stored: {bug_uuid}")
    print()
    
    # Step 6: Store Convention
    print("Step 6: Storing coding convention...")
    conv_uuid = await service.remember_convention(
        title="Error Handling Pattern",
        convention_type="pattern",
        rule="All service methods must return Result<T> type for operations that can fail",
        rationale="Explicit error handling makes failure cases visible in function signatures",
        examples=[
            "Result<User> authenticate(credentials)",
            "Result<Token> refresh_token(token_id)",
        ],
        anti_patterns=[
            "Throwing exceptions for control flow",
            "Returning None for errors",
        ],
    )
    print(f"  ✓ Stored: {conv_uuid}")
    print()
    
    # Step 7: Store Relationship
    print("Step 7: Storing entity relationship...")
    rel_uuid = await service.remember_relationship(
        title="AuthService Dependency Graph",
        source_entity="AuthService",
        target_entity="TokenService",
        relation_type="DEPENDS_ON",
        properties={"reason": "JWT token validation"},
    )
    print(f"  ✓ Stored: {rel_uuid}")
    print()
    
    # Step 8: Demonstrate Scoring
    print("Step 8: Testing memory scoring...")
    
    test_content = "AuthService depends on TokenService for JWT validation"
    should_remember, confidence, mem_type = scorer.should_remember(test_content)
    print(f"  Content: '{test_content[:50]}...'")
    print(f"  Should remember: {should_remember}")
    print(f"  Confidence: {confidence:.2%}")
    print(f"  Type detected: {mem_type}")
    print()
    
    transient_content = "Hello, can you help me with my code?"
    should_remember2, confidence2, mem_type2 = scorer.should_remember(transient_content)
    print(f"  Content: '{transient_content}'")
    print(f"  Should remember: {should_remember2}")
    print(f"  Confidence: {confidence2:.2%}")
    print()
    
    # Step 9: Search Memories
    print("Step 9: Searching memories...")
    
    # Create search query
    search_results = await service.search_memories(
        MemoryQuery(
            query_text="authentication token validation",
            limit=5,
            min_confidence=0.5,
        )
    )
    
    print(f"  Found {len(search_results)} results:")
    for idx, result in enumerate(search_results, 1):
        print(f"    {idx}. [{result.memory.memory_type.value}] {result.memory.title}")
        print(f"       Score: {result.score:.2f}, Confidence: {result.memory.confidence:.0%}")
    print()
    
    # Step 10: Get Metrics
    print("Step 10: System metrics...")
    metrics = logger.get_metrics()
    if metrics:
        print(f"  Total memories stored: {metrics['storage_count']}")
        print(f"  Total searches: {metrics['retrieval_count']}")
        print(f"  Average retrieval latency: {metrics['avg_retrieval_latency_ms']:.2f}ms")
    print()
    
    # Step 11: Cleanup
    print("Step 11: Cleaning up...")
    await client.close()
    print(f"  ✓ Client disconnected")
    print()
    
    print("=" * 80)
    print("Quickstart completed successfully!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  - Integrate with OpenHands using the MCP server")
    print("  - Configure automatic memory pipeline")
    print("  - Add repository-specific knowledge")
    print()


if __name__ == "__main__":
    asyncio.run(main())
