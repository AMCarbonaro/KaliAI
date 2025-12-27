"""Tests for tool chaining (nmap -> metasploit)."""

from unittest.mock import MagicMock, patch

import pytest

from kali_orchestrator.agent import OrchestratorAgent
from kali_orchestrator.config import OrchestratorConfig
from kali_orchestrator.memory import MemoryManager


@pytest.fixture
def agent():
    """Create an agent with mocked dependencies."""
    config = OrchestratorConfig()
    memory = MemoryManager()
    agent = OrchestratorAgent(config, memory, force_local=True)

    # Mock hexstrike client
    agent.hexstrike = MagicMock()
    agent.hexstrike.execute_tool = MagicMock(return_value={
        "success": True,
        "open_ports": [{"port": 445, "service": "SMB", "version": "Windows"}],
    })

    # Mock LLM
    agent.llm = MagicMock()
    agent.llm.generate = MagicMock(return_value="Run nmap scan and check for SMB vulnerabilities")

    return agent


def test_nmap_scan_triggers_plugin(agent):
    """Test that nmap scan query triggers nmap plugin."""
    query = "Scan 192.168.1.1 for open ports"
    matching_plugins = [p for p in agent.plugins if p.matches(query)]
    assert len(matching_plugins) > 0
    assert any(p.name == "nmap" for p in matching_plugins)


def test_metasploit_suggest_triggers_plugin(agent):
    """Test that metasploit suggestion query triggers metasploit plugin."""
    query = "suggest exploits for SMB service"
    matching_plugins = [p for p in agent.plugins if p.matches(query)]
    assert len(matching_plugins) > 0
    assert any(p.name == "metasploit" for p in matching_plugins)


def test_web_vuln_triggers_plugin(agent):
    """Test that web vulnerability query triggers web plugin."""
    query = "scan website for vulnerabilities"
    matching_plugins = [p for p in agent.plugins if p.matches(query)]
    assert len(matching_plugins) > 0
    assert any(p.name == "web_vuln" for p in matching_plugins)

