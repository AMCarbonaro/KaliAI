"""LLM backend integrations: Ollama, gemini-cli, google-generativeai."""

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

import httpx

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from kali_orchestrator.config import LLMConfig


class LLMBackend:
    """Base class for LLM backends."""

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: User prompt
            context: Additional context (conversation history, findings, etc.)

        Returns:
            LLM response text
        """
        raise NotImplementedError

    def generate_with_tools(
        self, prompt: str, tools: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response with tool calling support.

        Args:
            prompt: User prompt
            tools: Available tools (MCP tools from hexstrike-ai)
            context: Additional context

        Returns:
            Dictionary with 'response' and 'tool_calls' keys
        """
        # Default implementation: just generate text
        response = self.generate(prompt, context)
        return {"response": response, "tool_calls": []}


class OllamaBackend(LLMBackend):
    """Ollama LLM backend via HTTP API."""

    def __init__(self, config: LLMConfig):
        """Initialize Ollama backend.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.model = config.ollama.model
        # Check environment variable first (for Docker)
        env_url = os.getenv("KALI_ORCHESTRATOR_LLM__OLLAMA__BASE_URL")
        if env_url:
            self.base_url = env_url.rstrip("/")
            print(f"Using Ollama URL from environment: {self.base_url}", file=sys.stderr)
        else:
            self.base_url = config.ollama.base_url.rstrip("/")
            print(f"Using Ollama URL from config: {self.base_url}", file=sys.stderr)

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using Ollama API.

        Args:
            prompt: User prompt
            context: Additional context

        Returns:
            LLM response text
        """
        # Build full prompt with context
        full_prompt = self._build_prompt(prompt, context)

        # Retry logic for connection issues
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # First, check if Ollama is reachable
                try:
                    health_check = httpx.get(f"{self.base_url}/api/tags", timeout=5)
                    health_check.raise_for_status()
                except httpx.HTTPError:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"Ollama not ready, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                        time.sleep(wait_time)
                        continue
                    else:
                        raise RuntimeError(
                            f"Cannot connect to Ollama at {self.base_url}. "
                            f"Make sure Ollama is running and the model '{self.model}' is pulled. "
                            f"Run: docker exec kali-orchestrator-ollama ollama pull {self.model}"
                        )

                # Now try the actual request
                response = httpx.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
            except httpx.ConnectError as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Connection refused, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Connection refused to Ollama at {self.base_url}. "
                        f"Check: 1) Ollama container is running: docker ps | grep ollama "
                        f"2) Model is pulled: docker exec kali-orchestrator-ollama ollama list "
                        f"3) If no models, pull it: docker exec kali-orchestrator-ollama ollama pull {self.model}"
                    )
            except httpx.HTTPError as e:
                if "404" in str(e) or "model" in str(e).lower():
                    raise RuntimeError(
                        f"Model '{self.model}' not found. Pull it first: "
                        f"docker exec kali-orchestrator-ollama ollama pull {self.model}"
                    )
                raise RuntimeError(f"Ollama API error: {e}")

    def _build_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Build full prompt with context.

        Args:
            prompt: Base prompt
            context: Context dictionary

        Returns:
            Full prompt string
        """
        if not context:
            return prompt

        context_parts = []
        if "conversation_history" in context:
            history = context["conversation_history"]
            if history:
                context_parts.append("Previous conversation:")
                for msg in history[-5:]:  # Last 5 messages
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    context_parts.append(f"{role}: {content}")

        if "recent_findings" in context:
            findings = context["recent_findings"]
            if findings:
                context_parts.append("\nRecent findings:")
                for finding in findings:
                    context_parts.append(f"- {finding.get('type', 'unknown')}: {finding.get('description', '')}")

        if context_parts:
            return "\n\n".join(context_parts) + "\n\n" + prompt
        return prompt


class GeminiCLIBackend(LLMBackend):
    """gemini-cli backend via subprocess calls."""

    def __init__(self, config: LLMConfig):
        """Initialize gemini-cli backend.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.mcp_enabled = True

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using gemini-cli.

        Args:
            prompt: User prompt
            context: Additional context

        Returns:
            LLM response text
        """
        # Build full prompt
        full_prompt = self._build_prompt(prompt, context)

        try:
            # Check if gemini-cli is available
            result = subprocess.run(
                ["which", "gemini-cli"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError("gemini-cli not found. Please install: sudo apt install gemini-cli")

            # Build command
            cmd = ["gemini-cli", "--prompt", full_prompt]

            # Enable MCP if configured
            if self.mcp_enabled:
                # Try to add hexstrike-ai MCP server
                try:
                    subprocess.run(
                        ["gemini", "mcp", "add", "http://127.0.0.1:8888"],
                        capture_output=True,
                        check=False,  # Don't fail if MCP already added
                    )
                except Exception:
                    pass  # MCP might already be configured

            # Execute gemini-cli
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(f"gemini-cli error: {result.stderr}")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise RuntimeError("gemini-cli timeout")
        except FileNotFoundError:
            raise RuntimeError("gemini-cli not found. Please install: sudo apt install gemini-cli")

    def _build_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Build full prompt with context.

        Args:
            prompt: Base prompt
            context: Context dictionary

        Returns:
            Full prompt string
        """
        if not context:
            return prompt

        context_parts = []
        if "conversation_history" in context:
            history = context["conversation_history"]
            if history:
                context_parts.append("Previous conversation:")
                for msg in history[-5:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    context_parts.append(f"{role}: {content}")

        if "recent_findings" in context:
            findings = context["recent_findings"]
            if findings:
                context_parts.append("\nRecent findings:")
                for finding in findings:
                    context_parts.append(f"- {finding.get('type', 'unknown')}: {finding.get('description', '')}")

        if context_parts:
            return "\n\n".join(context_parts) + "\n\n" + prompt
        return prompt


class GoogleGenerativeAIBackend(LLMBackend):
    """Google Generative AI (Gemini) backend via Python SDK."""

    def __init__(self, config: LLMConfig):
        """Initialize Google Generative AI backend.

        Args:
            config: LLM configuration
        """
        if genai is None:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")

        self.config = config
        api_key = config.gemini.api_key
        if not api_key:
            raise ValueError("Gemini API key not configured. Set it in config.yaml or KALI_ORCHESTRATOR_LLM__GEMINI__API_KEY")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using Google Generative AI.

        Args:
            prompt: User prompt
            context: Additional context

        Returns:
            LLM response text
        """
        # Build full prompt
        full_prompt = self._build_prompt(prompt, context)

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Google Generative AI error: {e}")

    def _build_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Build full prompt with context.

        Args:
            prompt: Base prompt
            context: Context dictionary

        Returns:
            Full prompt string
        """
        if not context:
            return prompt

        context_parts = []
        if "conversation_history" in context:
            history = context["conversation_history"]
            if history:
                context_parts.append("Previous conversation:")
                for msg in history[-5:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    context_parts.append(f"{role}: {content}")

        if "recent_findings" in context:
            findings = context["recent_findings"]
            if findings:
                context_parts.append("\nRecent findings:")
                for finding in findings:
                    context_parts.append(f"- {finding.get('type', 'unknown')}: {finding.get('description', '')}")

        if context_parts:
            return "\n\n".join(context_parts) + "\n\n" + prompt
        return prompt


def create_llm_backend(config: LLMConfig, force_local: bool = False) -> LLMBackend:
    """Create an LLM backend based on configuration.

    Args:
        config: LLM configuration
        force_local: If True, force Ollama backend regardless of config

    Returns:
        LLMBackend instance

    Raises:
        ValueError: If backend type is invalid or misconfigured
    """
    if force_local:
        return OllamaBackend(config)

    backend_type = config.primary_llm.lower()

    if backend_type == "ollama":
        return OllamaBackend(config)
    elif backend_type == "gemini-cli":
        return GeminiCLIBackend(config)
    elif backend_type == "google-generativeai":
        return GoogleGenerativeAIBackend(config)
    else:
        raise ValueError(f"Unknown LLM backend: {backend_type}")

