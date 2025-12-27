"""Tests for scope enforcement."""

import pytest

from kali_orchestrator.agent import OrchestratorAgent, SafetyError
from kali_orchestrator.config import OrchestratorConfig, ScopeConfig
from kali_orchestrator.memory import MemoryManager


@pytest.fixture
def strict_config():
    """Create a config with strict scope enforcement."""
    config = OrchestratorConfig()
    config.scope = ScopeConfig(
        allowed_ips=["192.168.1.0/24", "10.0.0.0/8"],
        allowed_domains=["example.com"],
        strict_mode=True,
    )
    return config


@pytest.fixture
def agent(strict_config):
    """Create an agent with strict config."""
    memory = MemoryManager()
    # Mock hexstrike and LLM to avoid actual connections
    agent = OrchestratorAgent(strict_config, memory, force_local=True)
    return agent


def test_in_scope_ip(agent):
    """Test that in-scope IPs are allowed."""
    assert agent._check_scope("192.168.1.10") is True
    assert agent._check_scope("192.168.1.100") is True
    assert agent._check_scope("10.0.0.1") is True


def test_out_of_scope_ip(agent):
    """Test that out-of-scope IPs are rejected."""
    assert agent._check_scope("192.168.2.10") is False
    assert agent._check_scope("172.16.0.1") is False


def test_in_scope_domain(agent):
    """Test that in-scope domains are allowed."""
    assert agent._check_scope("example.com") is True
    assert agent._check_scope("subdomain.example.com") is True


def test_out_of_scope_domain(agent):
    """Test that out-of-scope domains are rejected."""
    assert agent._check_scope("other.com") is False
    assert agent._check_scope("example.org") is False


def test_cidr_range(agent):
    """Test CIDR range matching."""
    assert agent._check_scope("192.168.1.0/24") is True
    assert agent._check_scope("192.168.1.50") is True


def test_non_strict_mode():
    """Test that non-strict mode allows all targets."""
    config = OrchestratorConfig()
    config.scope = ScopeConfig(strict_mode=False)
    memory = MemoryManager()
    agent = OrchestratorAgent(config, memory, force_local=True)

    assert agent._check_scope("192.168.2.10") is True
    assert agent._check_scope("any-domain.com") is True

