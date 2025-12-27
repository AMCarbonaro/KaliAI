"""Tests for memory persistence."""

import tempfile
from pathlib import Path

import pytest

from kali_orchestrator.memory import Finding, MemoryManager, ToolExecution


@pytest.fixture
def temp_memory():
    """Create a memory manager with temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = MemoryManager(base_dir=Path(tmpdir))
        yield memory


def test_create_session(temp_memory):
    """Test session creation."""
    session_id = temp_memory.create_session()
    assert session_id is not None
    assert temp_memory.current_session is not None
    assert temp_memory.current_session.session_id == session_id


def test_save_and_load_session(temp_memory):
    """Test saving and loading sessions."""
    session_id = temp_memory.create_session()
    temp_memory.add_conversation("user", "Test query")
    temp_memory.save_session()

    # Load session
    loaded = temp_memory.load_session(session_id)
    assert loaded is not None
    assert len(loaded.conversation_history) == 1
    assert loaded.conversation_history[0]["role"] == "user"
    assert loaded.conversation_history[0]["content"] == "Test query"


def test_add_finding(temp_memory):
    """Test adding findings."""
    temp_memory.create_session()
    finding = Finding(
        id="test_1",
        timestamp="2024-01-01T00:00:00",
        target="192.168.1.1",
        type="open_port",
        severity="info",
        description="Port 80 is open",
    )
    temp_memory.add_finding(finding)

    assert len(temp_memory.current_session.findings) == 1
    assert temp_memory.current_session.findings[0].type == "open_port"


def test_add_tool_execution(temp_memory):
    """Test adding tool executions."""
    temp_memory.create_session()
    execution = ToolExecution(
        timestamp="2024-01-01T00:00:00",
        tool="nmap",
        command="nmap -sV 192.168.1.1",
        target="192.168.1.1",
        output="Port 80 open",
        exit_code=0,
        duration_seconds=5.0,
    )
    temp_memory.add_tool_execution(execution)

    assert len(temp_memory.current_session.tool_executions) == 1
    assert temp_memory.current_session.tool_executions[0].tool == "nmap"


def test_get_context(temp_memory):
    """Test context retrieval."""
    temp_memory.create_session()
    temp_memory.add_conversation("user", "Query 1")
    temp_memory.add_conversation("assistant", "Response 1")
    temp_memory.add_conversation("user", "Query 2")

    context = temp_memory.get_context(max_history=2)
    assert len(context["conversation_history"]) == 2
    assert context["conversation_history"][-1]["content"] == "Query 2"


def test_list_sessions(temp_memory):
    """Test listing sessions."""
    session1 = temp_memory.create_session()
    temp_memory.save_session()
    temp_memory.clear_session()

    session2 = temp_memory.create_session()
    temp_memory.save_session()

    sessions = temp_memory.list_sessions()
    assert len(sessions) == 2
    assert session1 in sessions
    assert session2 in sessions

