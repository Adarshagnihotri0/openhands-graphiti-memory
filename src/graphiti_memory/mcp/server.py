"""MCP server for Graphiti memory system."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import MemoryQuery, MemoryType, MemoryUpdate
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.utils.logging import MemoryLogger


class GraphitiMemoryMCPServer:
    """
    MCP server exposing Graphiti memory tools.

    Provides tools for:
    - remember_architecture: Store architecture knowledge
    - remember_decision: Store design decisions
    - remember_bug_fix: Store bug fixes
    - remember_convention: Store coding conventions
    - remember_relationship: Store entity relationships
    - search_memory: Search for relevant memories
    - update_memory: Update existing memory
    - delete_memory: Delete memory
    - recent_changes: Get recent memories
    - get_status: Check system status
    """

    def __init__(self, config: GraphitiConfig) -> None:
        self.config = config
        self.logger = MemoryLogger(config)

        # Initialize components
        self.client = GraphitiClient(config, self.logger)
        self.scorer = MemoryScorer(config, self.logger)
        self.service = MemoryService(config, self.client, self.scorer, self.logger)

        # Create MCP server
        self.server = Server("graphiti-memory-server")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="remember_architecture",
                    description="Store architectural knowledge about system components, dependencies, and design",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Brief title for this architecture"},
                            "content": {"type": "string", "description": "Detailed architecture description"},
                            "component_type": {"type": "string", "description": "Type of component (service, database, api, etc.)"},
                            "dependencies": {"type": "array", "items": {"type": "string"}, "description": "Component dependencies"},
                            "interfaces": {"type": "array", "items": {"type": "string"}, "description": "Exposed interfaces"},
                            "responsibilities": {"type": "array", "items": {"type": "string"}, "description": "Component responsibilities"},
                            "module": {"type": "string", "description": "Module path"},
                            "service": {"type": "string", "description": "Service name"},
                        },
                        "required": ["title", "content", "component_type"],
                    },
                ),
                Tool(
                    name="remember_decision",
                    description="Store a design decision with rationale and alternatives considered",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Decision title"},
                            "decision_type": {"type": "string", "description": "Type of decision (pattern, library, architecture)"},
                            "rationale": {"type": "string", "description": "Why this decision was made"},
                            "content": {"type": "string", "description": "Detailed decision description"},
                            "alternatives_considered": {"type": "array", "items": {"type": "string"}, "description": "Alternatives considered"},
                            "trade_offs": {"type": "string", "description": "Trade-offs of the decision"},
                        },
                        "required": ["title", "decision_type", "rationale", "content"],
                    },
                ),
                Tool(
                    name="remember_bug_fix",
                    description="Store a bug fix discovery with root cause and solution",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Bug fix title"},
                            "bug_type": {"type": "string", "description": "Type of bug (race condition, null pointer, logic)"},
                            "root_cause": {"type": "string", "description": "Root cause of the bug"},
                            "solution": {"type": "string", "description": "Solution implemented"},
                            "symptoms": {"type": "array", "items": {"type": "string"}, "description": "Symptoms observed"},
                            "prevention": {"type": "string", "description": "How to prevent similar bugs"},
                            "module": {"type": "string", "description": "Module path"},
                        },
                        "required": ["title", "bug_type", "root_cause", "solution"],
                    },
                ),
                Tool(
                    name="remember_convention",
                    description="Store a coding convention or best practice",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Convention title"},
                            "convention_type": {"type": "string", "description": "Type of convention (naming, structure, pattern)"},
                            "rule": {"type": "string", "description": "The convention rule"},
                            "rationale": {"type": "string", "description": "Why this convention exists"},
                            "examples": {"type": "array", "items": {"type": "string"}, "description": "Examples of the convention"},
                            "anti_patterns": {"type": "array", "items": {"type": "string"}, "description": "Anti-patterns to avoid"},
                        },
                        "required": ["title", "convention_type", "rule", "rationale"],
                    },
                ),
                Tool(
                    name="remember_relationship",
                    description="Store a relationship between entities (e.g., Service A depends on Service B)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Relationship title"},
                            "source_entity": {"type": "string", "description": "Source entity name"},
                            "target_entity": {"type": "string", "description": "Target entity name"},
                            "relation_type": {"type": "string", "description": "Relationship type (DEPENDS_ON, USES, IMPLEMENTS, etc.)"},
                            "properties": {"type": "object", "description": "Relationship properties"},
                            "module": {"type": "string", "description": "Module path"},
                        },
                        "required": ["title", "source_entity", "target_entity", "relation_type"],
                    },
                ),
                Tool(
                    name="search_memory",
                    description="Search for relevant memories using semantic search and graph traversal",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "memory_types": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["architecture", "decision", "bug_fix", "convention", "relationship", "implementation"]},
                                "description": "Filter by memory types",
                            },
                            "min_confidence": {"type": "number", "description": "Minimum confidence (0-1)"},
                            "limit": {"type": "integer", "description": "Maximum results"},
                            "module": {"type": "string", "description": "Filter by module"},
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="update_memory",
                    description="Update an existing memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uuid": {"type": "string", "description": "Memory UUID to update"},
                            "title": {"type": "string", "description": "New title"},
                            "content": {"type": "string", "description": "New content"},
                            "confidence": {"type": "number", "description": "New confidence score"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "New tags"},
                        },
                        "required": ["uuid"],
                    },
                ),
                Tool(
                    name="delete_memory",
                    description="Delete a memory by UUID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uuid": {"type": "string", "description": "Memory UUID to delete"},
                        },
                        "required": ["uuid"],
                    },
                ),
                Tool(
                    name="recent_changes",
                    description="Get recent memories within a time range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "description": "Number of days to look back"},
                            "memory_type": {"type": "string", "description": "Filter by memory type"},
                            "limit": {"type": "integer", "description": "Maximum results"},
                        },
                        "required": ["days"],
                    },
                ),
                Tool(
                    name="get_status",
                    description="Get memory system status and metrics",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Execute a tool call."""
            try:
                # Ensure client is initialized
                if not self.client.is_connected:
                    await self.client.initialize()

                result = None

                if name == "remember_architecture":
                    uuid = await self.service.remember_architecture(
                        title=arguments["title"],
                        content=arguments["content"],
                        component_type=arguments["component_type"],
                        dependencies=arguments.get("dependencies"),
                        interfaces=arguments.get("interfaces"),
                        responsibilities=arguments.get("responsibilities"),
                        module=arguments.get("module"),
                        service=arguments.get("service"),
                    )
                    result = {"uuid": str(uuid), "message": "Architecture memory stored successfully"}

                elif name == "remember_decision":
                    uuid = await self.service.remember_decision(
                        title=arguments["title"],
                        decision_type=arguments["decision_type"],
                        rationale=arguments["rationale"],
                        content=arguments["content"],
                        alternatives_considered=arguments.get("alternatives_considered"),
                        trade_offs=arguments.get("trade_offs"),
                    )
                    result = {"uuid": str(uuid), "message": "Decision memory stored successfully"}

                elif name == "remember_bug_fix":
                    uuid = await self.service.remember_bug_fix(
                        title=arguments["title"],
                        bug_type=arguments["bug_type"],
                        root_cause=arguments["root_cause"],
                        solution=arguments["solution"],
                        symptoms=arguments.get("symptoms"),
                        prevention=arguments.get("prevention"),
                        module=arguments.get("module"),
                    )
                    result = {"uuid": str(uuid), "message": "Bug fix memory stored successfully"}

                elif name == "remember_convention":
                    uuid = await self.service.remember_convention(
                        title=arguments["title"],
                        convention_type=arguments["convention_type"],
                        rule=arguments["rule"],
                        rationale=arguments["rationale"],
                        examples=arguments.get("examples"),
                        anti_patterns=arguments.get("anti_patterns"),
                    )
                    result = {"uuid": str(uuid), "message": "Convention memory stored successfully"}

                elif name == "remember_relationship":
                    uuid = await self.service.remember_relationship(
                        title=arguments["title"],
                        source_entity=arguments["source_entity"],
                        target_entity=arguments["target_entity"],
                        relation_type=arguments["relation_type"],
                        properties=arguments.get("properties"),
                        module=arguments.get("module"),
                    )
                    result = {"uuid": str(uuid), "message": "Relationship memory stored successfully"}

                elif name == "search_memory":
                    memory_types = [MemoryType(t) for t in arguments.get("memory_types", [])] or None
                    query = MemoryQuery(
                        query_text=arguments["query"],
                        memory_types=memory_types,
                        min_confidence=arguments.get("min_confidence", 0.0),
                        limit=arguments.get("limit", self.config.retrieval_limit),
                        modules=[arguments["module"]] if "module" in arguments else None,
                    )
                    results = await self.service.search_memories(query)
                    result = {
                        "results": [
                            {
                                "title": r.memory.title,
                                "content": r.memory.content,
                                "type": r.memory.memory_type.value,
                                "confidence": r.memory.confidence,
                                "score": r.score,
                                "uuid": str(r.memory.uuid),
                            }
                            for r in results
                        ],
                        "count": len(results),
                    }

                elif name == "update_memory":
                    update = MemoryUpdate(
                        uuid=UUID(arguments["uuid"]),
                        title=arguments.get("title"),
                        content=arguments.get("content"),
                        confidence=arguments.get("confidence"),
                        tags=arguments.get("tags"),
                    )
                    updated = await self.service.update_memory(update)
                    result = {
                        "uuid": str(updated.uuid),
                        "message": "Memory updated successfully",
                        "updated_at": updated.updated_at.isoformat(),
                    }

                elif name == "delete_memory":
                    deleted = await self.service.delete_memory(UUID(arguments["uuid"]))
                    result = {"deleted": deleted, "message": "Memory deleted" if deleted else "Memory not found"}

                elif name == "recent_changes":
                    query = MemoryQuery(
                        query_text="",  # Empty query for recent memories
                        time_range_days=arguments["days"],
                        memory_types=[MemoryType(arguments["memory_type"])] if "memory_type" in arguments else None,
                        limit=arguments.get("limit", 20),
                    )
                    results = await self.service.search_memories(query)
                    result = {
                        "memories": [
                            {
                                "title": r.memory.title,
                                "type": r.memory.memory_type.value,
                                "created_at": r.memory.created_at.isoformat(),
                                "uuid": str(r.memory.uuid),
                            }
                            for r in results
                        ],
                        "count": len(results),
                    }

                elif name == "get_status":
                    result = {
                        "connected": self.client.is_connected,
                        "config": {
                            "database": self.config.database_provider,
                            "repository": self.config.repository_scope,
                            "branch": self.config.branch_scope,
                            "group_id": self.config.get_scoped_group_id(),
                        },
                        "metrics": self.logger.get_metrics(),
                    }

                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


async def main() -> None:
    """Main entry point for MCP server."""
    import os

    # Load configuration from environment
    config = GraphitiConfig()

    # Create and run server
    server = GraphitiMemoryMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
