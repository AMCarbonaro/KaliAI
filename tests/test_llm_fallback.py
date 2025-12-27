"""Tests for LLM backend fallback behavior."""

import pytest

from kali_orchestrator.config import LLMConfig, OllamaConfig
from kali_orchestrator.llm_backends import (
    OllamaBackend,
    create_llm_backend,
)


def test_ollama_backend_creation():
    """Test Ollama backend creation."""
    config = LLMConfig(primary_llm="ollama", ollama=OllamaConfig())
    backend = create_llm_backend(config, force_local=False)
    assert isinstance(backend, OllamaBackend)


def test_force_local_creates_ollama():
    """Test that force_local always creates Ollama backend."""
    config = LLMConfig(primary_llm="google-generativeai")
    backend = create_llm_backend(config, force_local=True)
    assert isinstance(backend, OllamaBackend)


def test_invalid_backend_raises_error():
    """Test that invalid backend type raises error."""
    config = LLMConfig(primary_llm="invalid-backend")
    with pytest.raises(ValueError):
        create_llm_backend(config)

