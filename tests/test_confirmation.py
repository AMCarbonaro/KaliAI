"""Tests for confirmation prompts."""

import pytest

from kali_orchestrator.agent import OrchestratorAgent
from kali_orchestrator.config import OrchestratorConfig, SafetyConfig
from kali_orchestrator.memory import MemoryManager


@pytest.fixture
def agent_with_confirmation():
    """Create an agent with confirmation required."""
    config = OrchestratorConfig()
    config.safety = SafetyConfig(
        require_confirmation=True,
        dangerous_actions=["exploit", "payload", "inject"],
    )
    memory = MemoryManager()
    agent = OrchestratorAgent(config, memory, force_local=True)
    return agent


def test_dangerous_action_detection(agent_with_confirmation):
    """Test detection of dangerous actions."""
    assert agent_with_confirmation._is_dangerous_action("run exploit") is True
    assert agent_with_confirmation._is_dangerous_action("inject payload") is True
    assert agent_with_confirmation._is_dangerous_action("scan port") is False


def test_confirmation_required(agent_with_confirmation):
    """Test that dangerous actions require confirmation."""
    result = agent_with_confirmation.process_query("exploit ms17-010 on 192.168.1.1")
    assert result.get("requires_confirmation") is True
    assert result.get("success") is False


def test_safe_action_no_confirmation(agent_with_confirmation):
    """Test that safe actions don't require confirmation."""
    # This would normally execute, but we'll mock it
    # For now, just check that dangerous action detection works
    assert agent_with_confirmation._is_dangerous_action("scan 192.168.1.1") is False

