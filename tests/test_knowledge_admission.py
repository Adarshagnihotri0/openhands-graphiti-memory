"""
Integration Tests for Knowledge Admission MVP

Tests verify:
1. Graphiti integration works
2. Repository isolation (group_id)
3. Admission filtering
4. Governance (secret detection)
5. Reliability (graceful degradation)
"""
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import pytest

# Import components
from knowledge_admission_mvp import (
    GraphitiAdapter,
    MetadataEnricher,
    AdmissionPolicy,
    ExecutionRecorder,
    BasicGovernance,
    KnowledgeAdmissionPipeline,
    ExecutionRecord,
    AdmissionDecision
)


# ============================================================================
# Test: AdmissionPolicy
# ============================================================================

def test_admission_policy_rejects_failed_tasks():
    """Failed tasks should not be admitted."""
    policy = AdmissionPolicy()
    
    decision = policy.should_admit(
        prompt="Implement OAuth",
        success=False,  # ← Failed
        changed_files=["auth.py"],
        response_summary="Created AuthService"
    )
    
    assert decision.should_admit is False
    assert "failed" in decision.reason.lower()


def test_admission_policy_rejects_trivial_actions():
    """Trivial actions should not be admitted."""
    policy = AdmissionPolicy()
    
    # Test npm install (should fail on "no outcome" since changed_files is empty)
    decision = policy.should_admit(
        prompt="npm install",
        success=True,
        changed_files=[],
        response_summary=""
    )
    
    assert decision.should_admit is False
    # Reason could be "Trivial action" or "No meaningful outcome" depending on order of checks
    assert decision.reason in ["Trivial action", "No meaningful outcome", "No knowledge value"]


def test_admission_policy_rejects_greetings():
    """Greetings should not be admitted."""
    policy = AdmissionPolicy()
    
    decision = policy.should_admit(
        prompt="Hi there",
        success=True,
        changed_files=[],
        response_summary="Hello!"
    )
    
    assert decision.should_admit is False


def test_admission_policy_accepts_valuable_knowledge():
    """Valuable architectural knowledge should be admitted."""
    policy = AdmissionPolicy()
    
    decision = policy.should_admit(
        prompt="Explain the authentication architecture",
        success=True,
        changed_files=["auth/service.py", "auth/token.py"],
        response_summary="AuthService depends on TokenService for JWT validation"
    )
    
    assert decision.should_admit is True
    assert decision.reason == "Meets admission criteria"


def test_admission_policy_rejects_no_outcome():
    """Tasks with no meaningful outcome should be rejected."""
    policy = AdmissionPolicy()
    
    decision = policy.should_admit(
        prompt="Open README",
        success=True,
        changed_files=[],  # ← No files changed
        response_summary=""  # ← No summary
    )
    
    assert decision.should_admit is False
    assert "outcome" in decision.reason.lower()


# ============================================================================
# Test: MetadataEnricher
# ============================================================================

def test_metadata_enricher_builds_group_id():
    """Should build correct group_id from repository + branch."""
    enricher = MetadataEnricher()
    
    group_id = enricher.build_group_id(
        repository="myorg/myapp",
        branch="main"
    )
    
    assert group_id == "repo_myorg_myapp_branch_main"


def test_metadata_enricher_sanitizes_special_chars():
    """Should sanitize special characters in identifiers."""
    enricher = MetadataEnricher()
    
    group_id = enricher.build_group_id(
        repository="org-name/repo_name",
        branch="feature/auth-123"
    )
    
    # Should replace / with _
    assert "/" not in group_id
    assert "repo_org-name_repo_name_branch_feature_auth-123" == group_id


# ============================================================================
# Test: ExecutionRecorder
# ============================================================================

def test_execution_recorder_creates_record():
    """Should create execution record with all fields."""
    recorder = ExecutionRecorder()
    
    record = recorder.record(
        task_id="task-123",
        prompt="Implement auth",
        response="Created AuthService",
        repository="myorg/myapp",
        branch="main",
        workspace_path="/workspace",
        success=True,
        changed_files=["auth.py"]
    )
    
    assert record.task_id == "task-123"
    assert record.repository == "myorg/myapp"
    assert record.branch == "main"
    assert record.success is True
    assert len(record.changed_files) == 1
    assert isinstance(record.timestamp, datetime)


def test_execution_recorder_truncates_long_responses():
    """Should truncate long responses."""
    recorder = ExecutionRecorder()
    
    long_response = "x" * 1000
    
    record = recorder.record(
        task_id="task-123",
        prompt="Test",
        response=long_response,
        repository="test/test",
        branch="main",
        workspace_path="/tmp",
        success=True
    )
    
    assert len(record.response_summary) <= 503  # 500 + "..."


# ============================================================================
# Test: BasicGovernance
# ============================================================================

def test_governance_detects_api_keys():
    """Should detect API keys."""
    governance = BasicGovernance()
    
    record = ExecutionRecord(
        task_id="test",
        prompt="test",
        response_summary="api_key='sk-1234567890abcdefghijklmnopqrstuvwxyz'",
        repository="test/test",
        branch="main",
        workspace_path="/tmp",
        success=True,
        duration_seconds=0,
        changed_files=[],
        tests_passed=None,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    decision = governance.check(record)
    
    assert decision.should_admit is False
    assert "secret" in decision.reason.lower()


def test_governance_detects_passwords():
    """Should detect passwords."""
    governance = BasicGovernance()
    
    record = ExecutionRecord(
        task_id="test",
        prompt="test",
        response_summary="password='my_secret_password'",
        repository="test/test",
        branch="main",
        workspace_path="/tmp",
        success=True,
        duration_seconds=0,
        changed_files=[],
        tests_passed=None,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    decision = governance.check(record)
    
    assert decision.should_admit is False


def test_governance_rejects_oversized_payloads():
    """Should reject oversized payloads."""
    governance = BasicGovernance()
    
    record = ExecutionRecord(
        task_id="test",
        prompt="test",
        response_summary="x" * 20000,  # Exceeds MAX_EPISODE_SIZE
        repository="test/test",
        branch="main",
        workspace_path="/tmp",
        success=True,
        duration_seconds=0,
        changed_files=[],
        tests_passed=None,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    decision = governance.check(record)
    
    assert decision.should_admit is False
    assert "large" in decision.reason.lower()


def test_governance_allows_clean_content():
    """Should allow clean content."""
    governance = BasicGovernance()
    
    record = ExecutionRecord(
        task_id="test",
        prompt="Implement auth",
        response_summary="Created AuthService",
        repository="test/test",
        branch="main",
        workspace_path="/tmp",
        success=True,
        duration_seconds=0,
        changed_files=["auth.py"],
        tests_passed=True,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    decision = governance.check(record)
    
    assert decision.should_admit is True


# ============================================================================
# Test: Repository Isolation (Mock Graphiti)
# ============================================================================

@pytest.mark.asyncio
async def test_repository_isolation_via_group_id():
    """Should use group_id for repository isolation."""
    
    # Mock Graphiti client
    mock_client = AsyncMock()
    mock_client.add_episode = AsyncMock()
    mock_client.search = AsyncMock(return_value=[])
    
    # Create adapter with mock
    adapter = GraphitiAdapter.__new__(GraphitiAdapter)
    adapter.client = mock_client
    
    # Submit episode with group_id
    await adapter.submit_episode(
        name="test",
        episode_body="AuthService depends on TokenService",
        source_description="test",
        reference_time=datetime.now(),
        group_id="repo_myorg_myapp_branch_main"
    )
    
    # Verify group_id was passed
    call_kwargs = mock_client.add_episode.call_args[1]
    assert call_kwargs["group_id"] == "repo_myorg_myapp_branch_main"


@pytest.mark.asyncio
async def test_search_filters_by_group_id():
    """Should filter search results by group_id."""
    
    # Mock Graphiti client
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[])
    
    # Create adapter with mock
    adapter = GraphitiAdapter.__new__(GraphitiAdapter)
    adapter.client = mock_client
    
    # Search with group_id
    await adapter.search(
        query="auth architecture",
        group_id="repo_myorg_myapp_branch_main"
    )
    
    # Verify group_id filter was passed
    call_kwargs = mock_client.search.call_args[1]
    assert call_kwargs["group_id"] == "repo_myorg_myapp_branch_main"


# ============================================================================
# Test: Full Pipeline (Mock Graphiti)
# ============================================================================

@pytest.mark.asyncio
async def test_pipeline_admits_valuable_knowledge():
    """Pipeline should admit valuable knowledge."""
    
    # Mock Graphiti adapter
    mock_adapter = AsyncMock(spec=GraphitiAdapter)
    mock_adapter.submit_episode = AsyncMock(return_value=True)
    
    # Create pipeline
    pipeline = KnowledgeAdmissionPipeline.__new__(KnowledgeAdmissionPipeline)
    pipeline.adapter = mock_adapter
    pipeline.enricher = MetadataEnricher()
    pipeline.policy = AdmissionPolicy()
    pipeline.recorder = ExecutionRecorder()
    pipeline.governance = BasicGovernance()
    
    # Create execution record
    record = ExecutionRecord(
        task_id="task-123",
        prompt="AuthService depends on TokenService",
        response_summary="Implemented JWT validation",
        repository="myorg/myapp",
        branch="main",
        workspace_path="/workspace",
        success=True,
        duration_seconds=10.0,
        changed_files=["auth/service.py"],
        tests_passed=True,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    # Process execution
    result = await pipeline.process_execution(record)
    
    # Should be admitted
    assert result is True
    
    # Verify Graphiti was called
    mock_adapter.submit_episode.assert_called_once()
    call_kwargs = mock_adapter.submit_episode.call_args[1]
    assert "repo_myorg_myapp_branch_main" == call_kwargs["group_id"]


@pytest.mark.asyncio
async def test_pipeline_rejects_trivial_actions():
    """Pipeline should reject trivial actions."""
    
    # Mock Graphiti adapter
    mock_adapter = AsyncMock(spec=GraphitiAdapter)
    
    # Create pipeline
    pipeline = KnowledgeAdmissionPipeline.__new__(KnowledgeAdmissionPipeline)
    pipeline.adapter = mock_adapter
    pipeline.enricher = MetadataEnricher()
    pipeline.policy = AdmissionPolicy()
    pipeline.recorder = ExecutionRecorder()
    pipeline.governance = BasicGovernance()
    
    # Create trivial execution
    record = ExecutionRecord(
        task_id="task-123",
        prompt="npm install",
        response_summary="",
        repository="myorg/myapp",
        branch="main",
        workspace_path="/workspace",
        success=True,
        duration_seconds=1.0,
        changed_files=[],
        tests_passed=None,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    # Process execution
    result = await pipeline.process_execution(record)
    
    # Should be rejected
    assert result is False
    
    # Verify Graphiti was NOT called
    mock_adapter.submit_episode.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_rejects_secrets():
    """Pipeline should reject content with secrets."""
    
    # Mock Graphiti adapter
    mock_adapter = AsyncMock(spec=GraphitiAdapter)
    
    # Create pipeline
    pipeline = KnowledgeAdmissionPipeline.__new__(KnowledgeAdmissionPipeline)
    pipeline.adapter = mock_adapter
    pipeline.enricher = MetadataEnricher()
    pipeline.policy = AdmissionPolicy()
    pipeline.recorder = ExecutionRecorder()
    pipeline.governance = BasicGovernance()
    
    # Create execution with secret
    record = ExecutionRecord(
        task_id="task-123",
        prompt="Configure API",
        response_summary="api_key='sk-1234567890abcdefghijklmnopqrstuvwxyz'",
        repository="myorg/myapp",
        branch="main",
        workspace_path="/workspace",
        success=True,
        duration_seconds=5.0,
        changed_files=["config.py"],
        tests_passed=True,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    # Process execution
    result = await pipeline.process_execution(record)
    
    # Should be rejected
    assert result is False
    
    # Verify Graphiti was NOT called
    mock_adapter.submit_episode.assert_not_called()


# ============================================================================
# Test: Reliability (Graceful Degradation)
# ============================================================================

@pytest.mark.asyncio
async def test_pipeline_handles_graphiti_failure():
    """Pipeline should handle Graphiti failures gracefully."""
    
    # Mock Graphiti adapter that fails
    mock_adapter = AsyncMock(spec=GraphitiAdapter)
    mock_adapter.submit_episode = AsyncMock(return_value=False)  # ← Failed
    
    # Create pipeline
    pipeline = KnowledgeAdmissionPipeline.__new__(KnowledgeAdmissionPipeline)
    pipeline.adapter = mock_adapter
    pipeline.enricher = MetadataEnricher()
    pipeline.policy = AdmissionPolicy()
    pipeline.recorder = ExecutionRecorder()
    pipeline.governance = BasicGovernance()
    
    # Create execution
    record = ExecutionRecord(
        task_id="task-123",
        prompt="Implement auth",
        response_summary="Created service",
        repository="myorg/myapp",
        branch="main",
        workspace_path="/workspace",
        success=True,
        duration_seconds=5.0,
        changed_files=["auth.py"],
        tests_passed=True,
        commands_executed=[],
        timestamp=datetime.now()
    )
    
    # Process - should not crash
    result = await pipeline.process_execution(record)
    
    # Should return False (not crash)
    assert result is False


@pytest.mark.asyncio
async def test_adapter_handles_graphiti_errors():
    """Adapter should handle Graphiti errors."""
    
    # Mock Graphiti client that raises exception
    mock_client = AsyncMock()
    mock_client.add_episode = AsyncMock(side_effect=Exception("Connection error"))
    mock_client.search = AsyncMock(side_effect=Exception("Connection error"))
    
    # Create adapter with mock
    adapter = GraphitiAdapter.__new__(GraphitiAdapter)
    adapter.client = mock_client
    
    # Submit episode - should not crash
    result = await adapter.submit_episode(
        name="test",
        episode_body="test",
        source_description="test",
        reference_time=datetime.now(),
        group_id="test"
    )
    
    # Should return False (not crash)
    assert result is False
    
    # Search - should return empty list (not crash)
    results = await adapter.search("test", "test")
    
    assert results == []


# ============================================================================
# Test: Admission Decision Table
# ============================================================================

@pytest.mark.parametrize(
    "prompt,success,changed_files,expected_admit",
    [
        ("Hi there", True, [], False),  # Greeting
        ("npm install", True, [], False),  # Trivial action
        ("Implement OAuth", False, ["auth.py"], False),  # Failed
        ("Open README", True, [], False),  # No outcome
        ("Explain architecture", True, ["auth.py"], True),  # Valuable
        ("Fix auth bug", True, ["auth.py"], True),  # Valuable
        ("Refactor service", True, ["service.py"], True),  # Valuable
    ]
)
def test_admission_decision_table(prompt, success, changed_files, expected_admit):
    """Test admission decisions for various scenarios."""
    policy = AdmissionPolicy()
    
    decision = policy.should_admit(
        prompt=prompt,
        success=success,
        changed_files=changed_files,
        response_summary=prompt  # Use prompt as summary
    )
    
    assert decision.should_admit == expected_admit


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
