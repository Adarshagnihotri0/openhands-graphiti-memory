"""
Memory Provider Loader for OpenHands

This file is called by OpenHands on startup (via environment variable config).
It:
1. Reads memory_config.json
2. Creates MemoryProvider
3. Attaches to agent

This file should be in your OpenHands startup path.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_memory_config_path() -> Path:
    """Get memory config path."""
    config_from_env = os.environ.get('OPENHANDS_MEMORY_PROVIDER_CONFIG')
    if config_from_env:
        return Path(config_from_env)
    
    # Default location
    return Path.home() / '.openhands' / 'memory_config.json'


def load_memory_provider():
    """
    Load and initialize memory provider from config.
    
    Returns None if:
    - Config file doesn't exist
    - Memory is disabled
    - Connection fails
    
    This is the entry point called by OpenHands agent initialization.
    """
    from openhands.sdk.agent import Agent
    from milestone5_provider import MemoryProvider
    from milestone8_real_graphiti import RealGraphitiBackend
    from milestone3_builder import ContextBuilder
    from milestone4_classifier import IntentClassifier
    from milestone1_models import MemoryConfig
    
    config_path = get_memory_config_path()
    
    # Check if config exists
    if not config_path.exists():
        logger.info("No memory config found at {config_path}")
        logger.info("Memory system disabled")
        return None
    
    # Load config
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load memory config: {e}")
        return None
    
    # Check if enabled
    if not config.get('enabled', False):
        logger.info("Memory system disabled in config")
        return None
    
    # Extract backend config
    backend_config = config.get('backend', {})
    provider_config = config.get('config', {})
    
    # Create backend
    try:
        backend_type = backend_config.get('type', 'graphiti')
        
        if backend_type == 'graphiti':
            backend = RealGraphitiBackend(
                uri=backend_config.get('uri', 'bolt://localhost:7687'),
                user=backend_config.get('user', 'neo4j'),
                password=backend_config.get('password', 'openhands123')
            )
        else:
            logger.error(f"Unknown backend type: {backend_type}")
            return None
        
        logger.info(f"Connected to {backend_type} backend")
        
    except Exception as e:
        logger.error(f"Failed to connect to memory backend: {e}")
        logger.info("Memory system disabled (graceful fallback)")
        return None
    
    # Create provider
    try:
        memory_config = MemoryConfig(
            enabled=True,
            timeout_ms=provider_config.get('timeout_ms', 500),
            max_memories=provider_config.get('max_memories', 5),
            min_confidence=provider_config.get('min_confidence', 0.7),
            max_tokens=provider_config.get('max_tokens', 1500)
        )
        
        provider = MemoryProvider(
            backend=backend,
            context_builder=ContextBuilder(memory_config),
            classifier=IntentClassifier(),
            config=memory_config
        )
        
        logger.info("Memory Provider initialized successfully")
        return provider
        
    except Exception as e:
        logger.error(f"Failed to create memory provider: {e}")
        return None


def inject_memory_into_agent(agent: Optional['Agent'] = None) -> None:
    """
    Inject memory provider into agent.
    
    This should be called after agent initialization.
    If agent is None, it will be imported and modified globally.
    """
    if agent is None:
        # Import and modify global Agent class
        from openhands.sdk.agent import Agent as AgentClass
        
        # Store original __init__
        original_init = AgentClass.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Load memory provider
            provider = load_memory_provider()
            
            if provider:
                self.memory_provider = provider
                logger.info("Memory provider injected into agent")
            else:
                logger.info("Agent running without memory")
        
        AgentClass.__init__ = new_init
        
    else:
        # Inject into specific agent instance
        provider = load_memory_provider()
        
        if provider:
            agent.memory_provider = provider
            logger.info("Memory provider injected into agent instance")
        else:
            logger.info("Agent instance running without memory")


# Auto-initialization when this module is imported
# This hooks into the Agent class globally
try:
    inject_memory_into_agent()
    logger.info("Memory provider auto-initialization complete")
except Exception as e:
    logger.warning(f"Memory provider auto-init failed: {e}")
    logger.info("OpenHands will run without memory (graceful fallback)")
