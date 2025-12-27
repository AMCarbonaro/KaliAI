"""Nmap tool wrapper for safe execution."""

import json
import time
from typing import Any, Dict, List, Optional

from kali_orchestrator.hexstrike_client import HexstrikeClient


class NmapWrapper:
    """Wrapper for Nmap port scanning and service detection."""

    def __init__(self, hexstrike_client: HexstrikeClient):
        """Initialize Nmap wrapper.

        Args:
            hexstrike_client: hexstrike-ai MCP client
        """
        self.hexstrike = hexstrike_client

    def scan(
        self,
        target: str,
        ports: Optional[str] = None,
        scan_type: str = "syn",
        service_detection: bool = True,
        version_detection: bool = True,
    ) -> Dict[str, Any]:
        """Perform an Nmap scan.

        Args:
            target: Target IP or CIDR range
            ports: Port specification (e.g., "80,443", "1-1000", "22")
            scan_type: Scan type (syn, tcp, udp, etc.)
            service_detection: Enable service detection (-sV)
            version_detection: Enable version detection (-sV)

        Returns:
            Scan results dictionary
        """
        # Build nmap command parameters
        params = {
            "target": target,
        }

        if ports:
            params["ports"] = ports

        if scan_type:
            params["scan_type"] = scan_type

        if service_detection or version_detection:
            params["service_detection"] = True

        # Execute via hexstrike-ai
        try:
            result = self.hexstrike.execute_tool("nmap", params)
            return self._parse_nmap_output(result)
        except Exception as e:
            # Fallback: return error
            return {
                "success": False,
                "error": str(e),
                "target": target,
                "open_ports": [],
            }

    def quick_scan(self, target: str) -> Dict[str, Any]:
        """Perform a quick scan (top 1000 ports, service detection).

        Args:
            target: Target IP or CIDR range

        Returns:
            Scan results
        """
        return self.scan(target, ports="1-1000", service_detection=True)

    def full_scan(self, target: str) -> Dict[str, Any]:
        """Perform a full port scan (all 65535 ports).

        Args:
            target: Target IP or CIDR range

        Returns:
            Scan results
        """
        return self.scan(target, ports="1-65535", service_detection=True, version_detection=True)

    def scan_http_services(self, target: str) -> Dict[str, Any]:
        """Scan for HTTP/HTTPS services specifically.

        Args:
            target: Target IP or CIDR range

        Returns:
            Scan results filtered for HTTP services
        """
        result = self.scan(target, ports="80,443,8080,8443,8000,8888", service_detection=True)
        # Filter for HTTP services
        if "open_ports" in result:
            http_ports = []
            for port_info in result["open_ports"]:
                service = port_info.get("service", "").lower()
                if "http" in service or port_info.get("port") in [80, 443, 8080, 8443, 8000, 8888]:
                    http_ports.append(port_info)
            result["open_ports"] = http_ports
        return result

    def _parse_nmap_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Nmap output into structured format.

        Args:
            raw_output: Raw output from hexstrike-ai

        Returns:
            Parsed results
        """
        # Handle different output formats
        if isinstance(raw_output, str):
            try:
                raw_output = json.loads(raw_output)
            except json.JSONDecodeError:
                # Try to extract key information from text
                return {
                    "success": True,
                    "raw_output": raw_output,
                    "open_ports": [],
                }

        # Normalize output structure
        result = {
            "success": raw_output.get("success", True),
            "target": raw_output.get("target", ""),
            "open_ports": [],
            "scan_stats": raw_output.get("scan_stats", {}),
        }

        # Extract open ports
        if "open_ports" in raw_output:
            result["open_ports"] = raw_output["open_ports"]
        elif "ports" in raw_output:
            result["open_ports"] = [
                p for p in raw_output["ports"] if p.get("state") == "open"
            ]

        # Extract host information
        if "hosts" in raw_output:
            result["hosts"] = raw_output["hosts"]

        # Store raw output for reference
        result["raw_output"] = raw_output

        return result

