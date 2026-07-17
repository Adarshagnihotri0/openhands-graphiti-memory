"""
Knowledge Admission MVP - Graphiti Integration

Implementation based on architecture audit findings:
- Graphiti handles all graph mechanics
- We handle admission decisions
- Repository isolation via group_id
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import re

# Graphiti imports
try:
    from graphiti_core import Graphiti
    from graphiti_core.driver.neo4j import Neo4jDriver
    from graphiti_core.nodes import EntityNode
    from graphiti_core.edges import EntityEdge
    from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF
except ImportError:
    logging.warning("graphiti-core not installed. Install with: pip install graphiti-core")
    Graphiti = None

logger = logging.getLogger(__name__)


# ============================================================================
# Component 1: Graphiti Adapter
# ============================================================================

class GraphitiAdapter:
    """
    Thin wrapper around Graphiti SDK.
    
    Responsibilities:
    - Initialize Graphiti client
    - Submit episodes to knowledge graph
    - Retrieve knowledge via search
    - Health checks
    - Error handling
    
    Does NOT:
    - Extract entities (Graphiti does this)
    - Extract relationships (Graphiti does this)
    - Perform deduplication (Graphiti does this)
    """
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Initialize Graphiti adapter.
        
        Args:
            uri: Neo4j URI (bolt://localhost:7687)
            user: Neo4j username
            password: Neo4j password
            database: Database name (default: neo4j)
        """
        if Graphiti is None:
            raise ImportError("graphiti-core not installed. Install with: pip install graphiti-core")
        
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        
        try:
            # Initialize Graphiti client
            # Graphiti handles LLM client, embedder internally by default
            self.client = Graphiti(
                uri=uri,
                user=user,
                password=password,
                database=database
            )
            logger.info(f"✅ Graphiti client initialized: {uri}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Graphiti: {e}")
            raise
    
    async def submit_episode(
        self,
        name: str,
        episode_body: str,
        source_description: str,
        reference_time: datetime,
        group_id: str
    ) -> bool:
        """
        Submit episode to Graphiti knowledge graph.
        
        Graphiti automatically:
        - Extracts entities from episode_body
        - Extracts relationships between entities
        - Generates embeddings
        - Deduplicates entities
        - Updates temporal graph
        
        Args:
            name: Episode identifier
            episode_body: Content (text or JSON)
            source_description: Where this came from
            reference_time: When this occurred
            group_id: Namespace for repository isolation
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.client.add_episode(
                name=name,
                episode_body=episode_body,
                source_description=source_description,
                reference_time=reference_time,
                group_id=group_id  # ← NAMESPACING (CRITICAL)
            )
            logger.info(f"✅ Episode submitted: {name} (group: {group_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to submit episode {name}: {e}")
            return False
    
    async def search(
        self,
        query: str,
        group_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge graph within namespace.
        
        Graphiti automatically:
        - Performs hybrid search (semantic + keyword)
        - Reranks results (RRF by default)
        - Returns most relevant facts
        
        Args:
            query: Search query
            group_id: Namespace (repository + branch)
            limit: Maximum results
        
        Returns:
            List of search results (edges/facts)
        """
        try:
            # Use Graphiti's search (hybrid + reranking)
            results = await self.client.search(
                query=query,
                group_id=group_id,  # ← Filter by namespace
                limit=limit
            )
            logger.info(f"✅ Search found {len(results)} results for: {query[:50]}")
            return results
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """
        Check if Graphiti is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a minimal search operation
            await self.client.search(query="_health_check_", limit=0)
            return True
        except Exception as e:
            logger.warning(f"⚠️  Graphiti health check failed: {e}")
            return False
    
    async def close(self):
        """Close Graphiti client connection."""
        try:
            await self.client.close()
            logger.info("✅ Graphiti client closed")
        except Exception as e:
            logger.warning(f"⚠️  Failed to close Graphiti: {e}")


# ============================================================================
# Component 2: Metadata Enricher
# ============================================================================

class MetadataEnricher:
    """
    Construct group_id for Graphiti namespacing.
    
    Responsibilities:
    - Build group_id from repository + branch
    - Extract git context
    - Add task-specific metadata
    
    Uses Graphiti's built-in namespacing (group_id).
    """
    
    def build_group_id(self, repository: str, branch: str) -> str:
        """
        Build Graphiti group_id for repository isolation.
        
        Args:
            repository: Repository identifier (e.g., "myorg/myapp")
            branch: Branch name (e.g., "main")
        
        Returns:
            Namespace identifier for Graphiti's group_id
        """
        # Format: repo_{sanitized_repo}_branch_{sanitized_branch}
        # Replace special characters with underscores
        safe_repo = self._sanitize_identifier(repository)
        safe_branch = self._sanitize_identifier(branch)
        
        group_id = f"repo_{safe_repo}_branch_{safe_branch}"
        return group_id
    
    def _sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize identifier for Graphiti group_id.
        
        Args:
            identifier: String to sanitize
        
        Returns:
            Safe identifier (alphanumeric + underscore + hyphen)
        """
        # Replace / with _ (for repo org/repo format)
        # Replace other special chars with _
        safe = re.sub(r'[^a-zA-Z0-9_-]', '_', identifier)
        return safe
    
    def enrich_episode(
        self,
        repository: str,
        branch: str,
        task_id: str,
        timestamp: datetime
    ) -> Dict[str, str]:
        """
        Prepare metadata for episode.
        
        Note: Graphiti uses group_id for primary isolation.
        Additional metadata can be embedded in episode_body.
        
        Args:
            repository: Repository identifier
            branch: Branch name
            task_id: Task identifier
            timestamp: When this occurred
        
        Returns:
            Metadata dictionary (for reference/debugging)
        """
        return {
            "repository": repository,
            "branch": branch,
            "task_id": task_id,
            "timestamp": timestamp.isoformat(),
        }


# ============================================================================
# Component 3: Admission Policy
# ============================================================================

@dataclass
class AdmissionDecision:
    """Result of admission policy check."""
    should_admit: bool
    reason: str


class AdmissionPolicy:
    """
    Decide whether execution should become knowledge.
    
    Responsibilities:
    - Check task success/failure
    - Filter trivial actions
    - Assess knowledge value
    - Reject noise
    
    Does NOT:
    - Extract entities (Graphiti does this)
    - Determine relationships (Graphiti does this)
    """
    
    # Trivial action keywords (not worth remembering)
    TRIVIAL_KEYWORDS = [
        "npm install",
        "pip install",
        "run tests",
        "create file",
        "delete file",
        "fix typo",
        "open file",
    ]
    
    # Greeting keywords
    GREETING_KEYWORDS = [
        "hi",
        "hello",
        "thanks",
        "please",
        "help me",
    ]
    
    # Valuable knowledge keywords
    VALUABLE_KEYWORDS = [
        "architecture",
        "depends on",
        "implementation",
        "bug fix",
        "refactor",
        "feature",
        "api",
        "service",
        "module",
        "component",
        "pattern",
        "convention",
        "deployment",
        "configuration",
        "auth",
    ]
    
    def should_admit(
        self,
        prompt: str,
        success: bool,
        changed_files: List[str],
        response_summary: str
    ) -> AdmissionDecision:
        """
        Determine if execution should be admitted to knowledge graph.
        
        Args:
            prompt: User's original request
            success: Did task complete successfully?
            changed_files: List of files modified
            response_summary: Summary of what happened
        
        Returns:
            AdmissionDecision with should_admit and reason
        """
        # Rule 1: Task must succeed
        if not success:
            return AdmissionDecision(False, "Task failed")
        
        # Rule 2: Not a greeting
        if self._is_greeting(prompt):
            return AdmissionDecision(False, "Greeting or conversation")
        
        # Rule 3: Must have meaningful outcome
        if not changed_files and not response_summary:
            return AdmissionDecision(False, "No meaningful outcome")
        
        # Rule 4: Not a trivial action
        if self._is_trivial_action(prompt):
            return AdmissionDecision(False, "Trivial action")
        
        # Rule 5: Should have some knowledge value
        if not self._has_knowledge_value(prompt, response_summary):
            return AdmissionDecision(False, "No knowledge value")
        
        return AdmissionDecision(True, "Meets admission criteria")
    
    def _is_greeting(self, prompt: str) -> bool:
        """Check if this is a greeting."""
        prompt_lower = prompt.lower().strip()
        # Check if prompt starts with greeting
        return any(kw in prompt_lower.split()[:3] for kw in self.GREETING_KEYWORDS)
    
    def _is_trivial_action(self, prompt: str) -> bool:
        """Check if this is a trivial action not worth remembering."""
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in self.TRIVIAL_KEYWORDS)
    
    def _has_knowledge_value(self, prompt: str, response: str) -> bool:
        """Check if this execution contains valuable knowledge."""
        combined = f"{prompt} {response}".lower()
        return any(kw in combined for kw in self.VALUABLE_KEYWORDS)


# ============================================================================
# Component 4: Execution Recorder
# ============================================================================

@dataclass
class ExecutionRecord:
    """Record of a completed task execution."""
    
    # Identity
    task_id: str
    timestamp: datetime
    
    # Context
    repository: str
    branch: str
    workspace_path: str
    
    # Execution
    prompt: str
    success: bool
    duration_seconds: float
    
    # Outcomes
    changed_files: List[str]
    response_summary: str
    
    # Optional fields (must come after required fields)
    commit_sha: Optional[str] = None
    tests_passed: Optional[bool] = None
    commands_executed: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.commands_executed is None:
            self.commands_executed = []


class ExecutionRecorder:
    """
    Capture execution outcomes for admission.
    
    Responsibilities:
    - Record task execution details
    - Extract changed files, success/failure
    - Track repository context
    
    Does NOT:
    - Analyze code (Graphiti will extract entities)
    - Determine relationships (Graphiti will extract)
    """
    
    def record(
        self,
        task_id: str,
        prompt: str,
        response: str,
        repository: str,
        branch: str,
        workspace_path: str,
        success: bool,
        changed_files: Optional[List[str]] = None,
        tests_passed: Optional[bool] = None,
        commit_sha: Optional[str] = None,
        duration_seconds: float = 0.0,
        commands_executed: Optional[List[str]] = None
    ) -> ExecutionRecord:
        """
        Create execution record.
        
        Args:
            task_id: Unique task identifier
            prompt: User's original request
            response: Agent's response
            repository: Repository identifier
            branch: Branch name
            workspace_path: Path to workspace
            success: Did task succeed?
            changed_files: Files modified (optional)
            tests_passed: Did tests pass? (optional)
            commit_sha: Git commit SHA (optional)
            duration_seconds: Task duration (optional)
            commands_executed: Commands run (optional)
        
        Returns:
            ExecutionRecord ready for admission
        """
        return ExecutionRecord(
            task_id=task_id,
            timestamp=datetime.now(),
            repository=repository,
            branch=branch,
            commit_sha=commit_sha,
            workspace_path=workspace_path,
            prompt=prompt,
            success=success,
            duration_seconds=duration_seconds,
            changed_files=changed_files or [],
            tests_passed=tests_passed,
            commands_executed=commands_executed or [],
            response_summary=self._extract_summary(response)
        )
    
    def _extract_summary(self, response: str, max_length: int = 500) -> str:
        """Extract summary from agent response."""
        # Simple truncation for MVP
        # Could integrate with LLM for better summarization
        if len(response) <= max_length:
            return response
        return response[:max_length] + "..."


# ============================================================================
# Component 5: Basic Governance
# ============================================================================

class BasicGovernance:
    """
    Prevent unsafe writes to knowledge graph.
    
    Responsibilities:
    - Detect secrets (API keys, passwords)
    - Reject oversized payloads
    - Basic security checks
    
    Does NOT:
    - Do complex policy enforcement
    - PII classification (can add later if needed)
    """
    
    # Secret patterns to detect
    SECRET_PATTERNS = [
        r"api[_-]?key\s*=\s*['\"][^'\"]{10,}['\"]",
        r"secret[_-]?key\s*=\s*['\"][^'\"]{10,}['\"]",
        r"password\s*=\s*['\"][^'\"]{5,}['\"]",
        r"token\s*=\s*['\"][^'\"]{10,}['\"]",
        r"-----BEGIN.*KEY-----",
        r"aws_access_key_id\s*=\s*['\"][^'\"]+['\"]",
        r"aws_secret_access_key\s*=\s*['\"][^'\"]+['\"]",
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
    ]
    
    # Maximum episode size (characters)
    MAX_EPISODE_SIZE = 10000
    
    def check(self, record: ExecutionRecord) -> AdmissionDecision:
        """
        Check if episode passes governance.
        
        Args:
            record: Execution record to check
        
        Returns:
            AdmissionDecision (approved/rejected with reason)
        """
        # Check for secrets
        secret_check = self._check_secrets(record)
        if not secret_check.should_admit:
            return secret_check
        
        # Check size limits
        size_check = self._check_size(record)
        if not size_check.should_admit:
            return size_check
        
        return AdmissionDecision(True, "Passed governance checks")
    
    def _check_secrets(self, record: ExecutionRecord) -> AdmissionDecision:
        """Check for secret patterns."""
        # Combine all text fields
        text_to_check = " ".join([
            record.prompt,
            record.response_summary,
            " ".join(record.changed_files),
            " ".join(record.commands_executed)
        ])
        
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return AdmissionDecision(
                    False,
                    f"Contains potential secret (pattern: {pattern[:20]}...)"
                )
        
        return AdmissionDecision(True, "No secrets detected")
    
    def _check_size(self, record: ExecutionRecord) -> AdmissionDecision:
        """Check size limits."""
        total_size = len(record.response_summary)
        
        if total_size > self.MAX_EPISODE_SIZE:
            return AdmissionDecision(
                False,
                f"Episode too large: {total_size} > {self.MAX_EPISODE_SIZE}"
            )
        
        return AdmissionDecision(True, "Size within limits")


# ============================================================================
# Knowledge Admission Pipeline (Integration)
# ============================================================================

class KnowledgeAdmissionPipeline:
    """
    Minimal admission pipeline.
    
    Flow:
    ExecutionRecorder → AdmissionPolicy → Governance → MetadataEnricher → Graphiti
    
    Graphiti handles:
    - Entity extraction
    - Relationship extraction
    - Embedding generation
    - Semantic search
    - Deduplication
    - Temporal tracking
    """
    
    def __init__(self, graphiti_adapter: GraphitiAdapter):
        """Initialize pipeline with Graphiti adapter."""
        self.adapter = graphiti_adapter
        self.enricher = MetadataEnricher()
        self.policy = AdmissionPolicy()
        self.recorder = ExecutionRecorder()
        self.governance = BasicGovernance()
    
    async def process_execution(self, record: ExecutionRecord) -> bool:
        """
        Process execution for knowledge admission.
        
        Args:
            record: Execution record to process
        
        Returns:
            True if admitted to graph, False otherwise
        """
        logger.info(f"Processing execution: {record.task_id}")
        
        # Step 1: Check admission policy
        decision = self.policy.should_admit(
            prompt=record.prompt,
            success=record.success,
            changed_files=record.changed_files,
            response_summary=record.response_summary
        )
        
        if not decision.should_admit:
            logger.info(f"⏭️  Not admitted: {decision.reason}")
            return False
        
        # Step 2: Check governance
        governance_result = self.governance.check(record)
        
        if not governance_result.should_admit:
            logger.warning(f"🚫 Governance rejected: {governance_result.reason}")
            return False
        
        # Step 3: Enrich metadata (build group_id)
        group_id = self.enricher.build_group_id(
            repository=record.repository,
            branch=record.branch
        )
        
        # Step 4: Build episode body
        episode_body = self._build_episode_body(record)
        
        # Step 5: Submit to Graphiti
        success = await self.adapter.submit_episode(
            name=f"task_{record.task_id}",
            episode_body=episode_body,
            source_description=f"OpenHands execution: {record.prompt[:100]}",
            reference_time=record.timestamp,
            group_id=group_id
        )
        
        if success:
            logger.info(f"✅ Knowledge admitted: {record.task_id}")
        else:
            logger.error(f"❌ Failed to admit: {record.task_id}")
        
        return success
    
    def _build_episode_body(self, record: ExecutionRecord) -> str:
        """
        Build episode content from execution record.
        
        Graphiti will extract entities and relationships from this text.
        """
        parts = [
            f"Task: {record.prompt}",
            f"Result: {record.response_summary}",
        ]
        
        if record.changed_files:
            parts.append(f"Files: {', '.join(record.changed_files)}")
        
        if record.tests_passed is not None:
            status = "passed" if record.tests_passed else "failed"
            parts.append(f"Tests: {status}")
        
        return "\n".join(parts)
