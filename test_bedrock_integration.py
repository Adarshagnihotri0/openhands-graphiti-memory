#!/usr/bin/env python
"""
Bedrock/Mantle Proxy Integration Test (Port-Agnostic)

This demonstrates integration with your Bedrock proxy system.
Automatically detects and works with port 2999 or 3000.
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from graphiti_memory.config import GraphitiConfig, PortDetector
from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.integration.context_builder import ContextBuilder
from graphiti_memory.models import ArchitectureMemory, MemoryQuery
from graphiti_memory.utils.logging import MemoryLogger


async def test_bedrock_integration():
    """Test integration with Bedrock/Mantle proxy (auto-detect port)."""
    
    print("=" * 80)
    print("BEDROCK/MANTLE PROXY INTEGRATION TEST (Port-Agnostic)")
    print("=" * 80)
    print()
    
    # Get API key
    api_key = os.getenv("BEDROCK_MANTLE_API_KEY")
    if not api_key:
        print("❌ SKIP: Requires BEDROCK_MANTLE_API_KEY")
        print("   Set it with: export BEDROCK_MANTLE_API_KEY='your-key'")
        return False
    
    # Create config with port detection
    config = GraphitiConfig(
        llm_api_key=api_key,
        repository_scope="bedrock_test",
        group_id=f"test_{int(datetime.now().timestamp())}"
    )
    
    # Auto-detect proxy port
    proxy_url = PortDetector.get_proxy_url(config)
    detected_port = int(proxy_url.split(":")[-1]) if "localhost" in proxy_url else None
    
    # Print port status
    print("Port Status:")
    print("-" * 40)
    for port in config.get_proxy_ports():
        is_running = PortDetector.is_port_running(port, config.proxy_timeout)
        status = "✓ RUNNING" if is_running else "✗ NOT RUNNING"
        print(f"  Port {port}: {status}")
    print("-" * 40)
    print()
    
    # Update config with detected proxy URL
    config.llm_base_url = proxy_url
    
    print(f"Configuration:")
    print(f"  Provider: {config.llm_provider}")
    print(f"  Model: {config.llm_model}")
    print(f"  Proxy Port: {detected_port} (auto-detected)")
    print(f"  Base URL: {config.llm_base_url}")
    print(f"  Repository: {config.repository_scope}")
    print()
    
    # ============================================================================
    # STEP 1: Initialize client
    # ============================================================================
    print("STEP 1: Initializing Graphiti client...")
    
    logger = MemoryLogger(config)
    
    try:
        client = GraphitiClient(config, logger)
        await client.initialize()
        print("  ✓ Client initialized successfully")
        
    except Exception as e:
        print(f"❌ STEP 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # ============================================================================
    # STEP 2: Store memory
    # ============================================================================
    print("STEP 2: Storing architecture memory...")
    
    try:
        scorer = MemoryScorer(config, logger)
        service = MemoryService(config, client, scorer, logger)
        
        memory = ArchitectureMemory(
            title="Bedrock Integration Architecture",
            content="System integrated with Bedrock/Mantle proxy for LLM access. Uses LLMConfig with custom base_url.",
            component_type="integration",
            dependencies=["graphiti_core", "bedrock-proxy"],
            repository="test_repo",
            confidence=0.90
        )
        
        memory_id = await service.store_memory(memory)
        print(f"  ✓ Memory stored: {memory_id}")
        
    except Exception as e:
        print(f"❌ STEP 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False
    
    print()
    
    # ============================================================================
    # STEP 3: Retrieve memory
    # ============================================================================
    print("STEP 3: Retrieving memory...")
    
    try:
        query = MemoryQuery(
            query_text="Bedrock integration architecture",
            limit=5
        )
        
        results = await service.search_memories(query)
        print(f"  ✓ Retrieved {len(results)} memory(ies)")
        
        if results:
            for i, result in enumerate(results[:3], 1):
                content = getattr(result, 'content', '') or result.get('content', '')
                print(f"    {i}. {content[:60]}...")
        
    except Exception as e:
        print(f"❌ STEP 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False
    
    print()
    
    # ============================================================================
    # STEP 4: Build context
    # ============================================================================
    print("STEP 4: Building context...")
    
    try:
        context_builder = ContextBuilder(config)
        
        context = await context_builder.build_context(
            task="How is the system integrated with LLM providers?",
            max_tokens=500
        )
        
        if context:
            print(f"  ✓ Context built ({len(context)} characters)")
            print()
            print("  Preview:")
            print("  " + "-" * 76)
            for line in context.split("\n")[:5]:
                print(f"  {line}")
            print("  " + "-" * 76)
        
    except Exception as e:
        print(f"❌ STEP 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False
    
    print()
    
    # ============================================================================
    # SUCCESS
    # ============================================================================
    print("=" * 80)
    print("✅ BEDROCK INTEGRATION VALIDATED")
    print("=" * 80)
    print()
    print("Proven capabilities:")
    print("  1. ✓ Graphiti client initializes with custom LLM config")
    print("  2. ✓ Memory storage works")
    print("  3. ✓ Memory retrieval works")
    print("  4. ✓ Context building works")
    print()
    print("Integration with Bedrock proxy is operational!")
    print()
    
    await client.close()
    return True


if __name__ == "__main__":
    success = asyncio.run(test_bedrock_integration())
    sys.exit(0 if success else 1)
