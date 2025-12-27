"""Integration tests for agent flow."""

from unittest.mock import MagicMock, patch

import pytest

from kali_orchestrator.agent import OrchestratorAgent
from kali_orchestrator.config import OrchestratorConfig
from kali_orchestrator.memory import MemoryManager


@pytest.fixture
def mocked_agent():
    """Create an agent with all external dependencies mocked."""
    config = OrchestratorConfig()
    config.scope.allowed_ips = ["192.168.1.0/24"]
    memory = MemoryManager()
    agent = OrchestratorAgent(config, memory, force_local=True)

    # Mock hexstrike
    agent.hexstrike = MagicMock()
    agent.hexstrike.is_server_running = MagicMock(return_value=True)
    agent.hexstrike.execute_tool = MagicMock(return_value={
        "success": True,
        "open_ports": [{"port": 80, "service": "HTTP"}],
    })

    # Mock LLM
    agent.llm = MagicMock()
    agent.llm.generate = MagicMock(return_value="I'll scan the target for open ports.")

    return agent


def test_end_to_end_scan_flow(mocked_agent):
    """Test end-to-end flow: query -> scope check -> plugin execution -> response."""
    query = "Scan 192.168.1.10 for open HTTP services"

    result = mocked_agent.process_query(query, require_confirmation=False)

    # Should succeed
    assert result.get("success") is True

    # Should have executed plugins
    assert len(result.get("plugins_executed", [])) > 0

    # Should have response
    assert result.get("response") is not None

    # Memory should have conversation
    assert len(mocked_agent.memory.current_session.conversation_history) >= 2


def test_out_of_scope_rejection(mocked_agent):
    """Test that out-of-scope targets are rejected."""
    query = "Scan 10.0.0.1 for open ports"

    result = mocked_agent.process_query(query)

    # Should fail due to scope
    assert result.get("success") is False
    assert "out of scope" in result.get("error", "").lower()


def test_dangerous_action_confirmation(mocked_agent):
    """Test that dangerous actions require confirmation."""
    query = "exploit ms17-010 on 192.168.1.10"

    result = mocked_agent.process_query(query)

    # Should require confirmation
    assert result.get("requires_confirmation") is True
    assert result.get("success") is False

