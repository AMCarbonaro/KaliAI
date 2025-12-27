"""hexstrike-ai MCP client integration."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from kali_orchestrator.config import HexstrikeConfig


class HexstrikeClient:
    """Client for interacting with hexstrike-ai MCP server."""

    def __init__(self, config: HexstrikeConfig):
        """Initialize hexstrike client.

        Args:
            config: Hexstrike configuration
        """
        self.config = config
        self.server_url = config.server_url
        self.server_process: Optional[subprocess.Popen] = None

    def is_server_running(self) -> bool:
        """Check if hexstrike-ai MCP server is running.

        Returns:
            True if server is accessible, False otherwise
        """
        try:
            # Try to connect to the server
            response = httpx.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            # Try alternative endpoint or just check if port is open
            try:
                response = httpx.get(f"{self.server_url}/", timeout=5)
                return True
            except Exception:
                return False

    def start_server(self) -> bool:
        """Start hexstrike-ai MCP server if not running.

        Returns:
            True if server started successfully, False otherwise
        """
        if self.is_server_running():
            return True

        if not self.config.auto_start:
            return False

        try:
            # Try to start hexstrike_server
            # Check common locations
            possible_paths = [
                "/usr/bin/hexstrike_server",
                "/usr/local/bin/hexstrike_server",
                "hexstrike_server",  # In PATH
            ]

            server_path = None
            for path in possible_paths:
                if path == "hexstrike_server":
                    # Check if in PATH
                    result = subprocess.run(
                        ["which", "hexstrike_server"],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        server_path = result.stdout.strip()
                        break
                elif Path(path).exists():
                    server_path = path
                    break

            if not server_path:
                print("Warning: hexstrike_server not found. Please install hexstrike-ai package.")
                return False

            # Start server in background
            self.server_process = subprocess.Popen(
                [server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for server to start (poll health endpoint)
            max_attempts = 30
            for _ in range(max_attempts):
                time.sleep(1)
                if self.is_server_running():
                    print(f"hexstrike-ai MCP server started at {self.server_url}")
                    return True

            print("Warning: hexstrike_server started but not responding")
            return False

        except Exception as e:
            print(f"Error starting hexstrike_server: {e}")
            return False

    def stop_server(self) -> None:
        """Stop the hexstrike-ai MCP server if we started it."""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            except Exception as e:
                print(f"Error stopping hexstrike_server: {e}")
            finally:
                self.server_process = None

    def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a tool via hexstrike-ai MCP.

        Args:
            tool_name: Name of the tool to execute (e.g., "nmap", "metasploit")
            parameters: Tool parameters
            timeout: Request timeout in seconds

        Returns:
            Tool execution result
        """
        if not self.is_server_running():
            if not self.start_server():
                raise RuntimeError("hexstrike-ai MCP server is not running and could not be started")

        timeout = timeout or self.config.timeout

        try:
            # MCP protocol: POST to /tools/{tool_name}/execute
            url = f"{self.server_url}/tools/{tool_name}/execute"
            response = httpx.post(
                url,
                json={"parameters": parameters},
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            # Fallback: try alternative MCP endpoint format
            try:
                url = f"{self.server_url}/mcp/tools/call"
                response = httpx.post(
                    url,
                    json={"name": tool_name, "arguments": parameters},
                    timeout=timeout,
                )
                response.raise_for_status()
                result = response.json()
                # Normalize response format
                if "result" in result:
                    return result["result"]
                return result
            except httpx.HTTPError:
                raise RuntimeError(f"Failed to execute tool {tool_name} via hexstrike-ai: {e}")

    def list_tools(self) -> list[str]:
        """List available tools from hexstrike-ai MCP server.

        Returns:
            List of available tool names
        """
        if not self.is_server_running():
            if not self.start_server():
                return []

        try:
            # Try MCP tools list endpoint
            url = f"{self.server_url}/tools"
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "tools" in data:
                return [tool.get("name", tool) for tool in data["tools"]]
            return []
        except Exception:
            # Fallback: return common tools that hexstrike-ai typically supports
            return [
                "nmap",
                "metasploit",
                "nikto",
                "nuclei",
                "sqlmap",
                "burp",
                "ghidra",
                "wireshark",
            ]

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool information dictionary or None
        """
        if not self.is_server_running():
            return None

        try:
            url = f"{self.server_url}/tools/{tool_name}"
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

