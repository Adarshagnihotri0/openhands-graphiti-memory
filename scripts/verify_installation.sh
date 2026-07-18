#!/bin/bash
# Installation verification script for Graphiti Memory System

set -e

echo "======================================"
echo "Graphiti Memory System - Verification"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 10 ]); then
    echo "❌ Python 3.10+ required (found $python_version)"
    exit 1
fi
echo "✓ Python $python_version"
echo ""

# Check if uv is installed
echo "Checking uv package manager..."
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "✓ uv installed"
echo ""

# Install dependencies
echo "Installing dependencies..."
uv sync
echo "✓ Dependencies installed"
echo ""

# Run basic tests
echo "Running basic tests..."
uv run pytest graphiti_memory/tests/test_memory_system.py::TestMemoryModels -v
echo "✓ Basic tests passed"
echo ""

# Check configuration
echo "Checking configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, copying from .env.example"
    cp .env.example .env
    echo "  Please edit .env with your configuration"
fi
echo "✓ Configuration file exists"
echo ""

# Verify imports
echo "Verifying imports..."
uv run python -c "
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import ArchitectureMemory, MemoryType
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.mcp.server import GraphitiMemoryMCPServer
print('✓ All imports successful')
"
echo ""

# Check Docker
echo "Checking Docker (optional)..."
if command -v docker &> /dev/null; then
    echo "✓ Docker installed"
    if docker ps &> /dev/null; then
        echo "✓ Docker daemon running"
    else
        echo "⚠️  Docker daemon not running (memory system will use local database)"
    fi
else
    echo "⚠️  Docker not installed (optional for containerized database)"
fi
echo ""

# Summary
echo "======================================"
echo "Verification Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your database and LLM credentials"
echo "  2. Start Neo4j or FalkorDB: docker-compose up -d"
echo "  3. Run examples: uv run python examples/quickstart.py"
echo "  4. Start MCP server: uv run python -m graphiti_memory.mcp.server"
echo ""
echo "For more information, see README.md"
echo ""
