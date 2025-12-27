"""Nmap port scanning plugin."""

import re
from typing import Any, Dict

from kali_orchestrator.plugins.base import BasePlugin
from kali_orchestrator.tools import NmapWrapper


class NmapPlugin(BasePlugin):
    """Plugin for Nmap port scanning and service detection."""

    name = "nmap"
    description = "Port scanning and service detection using Nmap"

    def __init__(self, nmap_wrapper: NmapWrapper):
        """Initialize Nmap plugin.

        Args:
            nmap_wrapper: Nmap wrapper instance
        """
        self.nmap = nmap_wrapper

    def matches(self, query: str) -> bool:
        """Check if query requires Nmap scanning.

        Args:
            query: User query

        Returns:
            True if Nmap is needed
        """
        query_lower = query.lower()
        nmap_keywords = ["scan", "port", "nmap", "service", "open port", "port scan"]
        return any(keyword in query_lower for keyword in nmap_keywords)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Nmap scan.

        Args:
            context: Execution context with target and options

        Returns:
            Scan results
        """
        target = context.get("target", "")
        if not target:
            return {"success": False, "error": "No target specified"}

        # Extract scan type from context or query
        query = context.get("query", "").lower()
        scan_type = "quick"

        if "full" in query or "all ports" in query:
            scan_type = "full"
        elif "http" in query or "web" in query:
            scan_type = "http"

        # Perform scan
        if scan_type == "full":
            result = self.nmap.full_scan(target)
        elif scan_type == "http":
            result = self.nmap.scan_http_services(target)
        else:
            result = self.nmap.quick_scan(target)

        # Extract findings
        findings = []
        if "open_ports" in result:
            for port_info in result["open_ports"]:
                findings.append({
                    "type": "open_port",
                    "target": target,
                    "port": port_info.get("port"),
                    "service": port_info.get("service", ""),
                    "version": port_info.get("version", ""),
                    "severity": "info",
                })

        return {
            "success": result.get("success", True),
            "plugin": self.name,
            "target": target,
            "scan_type": scan_type,
            "open_ports": result.get("open_ports", []),
            "findings": findings,
            "raw_result": result,
        }

