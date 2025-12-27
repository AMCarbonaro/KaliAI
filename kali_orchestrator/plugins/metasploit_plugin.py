"""Metasploit module search and exploit suggestion plugin."""

from typing import Any, Dict

from kali_orchestrator.plugins.base import BasePlugin
from kali_orchestrator.tools import MetasploitWrapper


class MetasploitPlugin(BasePlugin):
    """Plugin for searching Metasploit modules and suggesting exploits."""

    name = "metasploit"
    description = "Search Metasploit modules and suggest exploits for detected services"

    def __init__(self, metasploit_wrapper: MetasploitWrapper):
        """Initialize Metasploit plugin.

        Args:
            metasploit_wrapper: Metasploit wrapper instance
        """
        self.metasploit = metasploit_wrapper

    def matches(self, query: str) -> bool:
        """Check if query requires Metasploit search.

        Args:
            query: User query

        Returns:
            True if Metasploit search is needed
        """
        query_lower = query.lower()
        metasploit_keywords = [
            "exploit",
            "metasploit",
            "msf",
            "vulnerability",
            "cve",
            "eternalblue",
            "suggest exploit",
        ]
        return any(keyword in query_lower for keyword in metasploit_keywords)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Metasploit search.

        Args:
            context: Execution context with services, findings, etc.

        Returns:
            Search results and exploit suggestions
        """
        query = context.get("query", "")
        findings = context.get("findings", [])
        open_ports = context.get("open_ports", [])

        # Extract services from findings and open ports
        services = set()
        for finding in findings:
            if "service" in finding:
                services.add(finding["service"].lower())

        for port_info in open_ports:
            if "service" in port_info:
                services.add(port_info["service"].lower())

        # Search for exploits
        suggested_exploits = []
        for service in services:
            exploits = self.metasploit.suggest_exploits(service)
            suggested_exploits.extend(exploits)

        # Also search based on query terms
        if "eternalblue" in query.lower() or "ms17-010" in query.lower():
            modules = self.metasploit.search_modules("ms17-010", module_type="exploit")
            suggested_exploits.extend(modules)

        # Deduplicate
        seen = set()
        unique_exploits = []
        for exploit in suggested_exploits:
            module_path = exploit.get("fullname") or exploit.get("path", "")
            if module_path and module_path not in seen:
                seen.add(module_path)
                unique_exploits.append(exploit)

        return {
            "success": True,
            "plugin": self.name,
            "services_detected": list(services),
            "suggested_exploits": unique_exploits,
            "count": len(unique_exploits),
        }

