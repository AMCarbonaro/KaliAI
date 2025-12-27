"""Web vulnerability scanning plugin."""

from typing import Any, Dict

from kali_orchestrator.plugins.base import BasePlugin
from kali_orchestrator.tools import WebToolsWrapper


class WebVulnPlugin(BasePlugin):
    """Plugin for web vulnerability scanning (Nikto, Nuclei)."""

    name = "web_vuln"
    description = "Web vulnerability scanning using Nikto and Nuclei"

    def __init__(self, web_tools: WebToolsWrapper):
        """Initialize web vulnerability plugin.

        Args:
            web_tools: Web tools wrapper instance
        """
        self.web_tools = web_tools

    def matches(self, query: str) -> bool:
        """Check if query requires web vulnerability scanning.

        Args:
            query: User query

        Returns:
            True if web scanning is needed
        """
        query_lower = query.lower()
        web_keywords = [
            "web",
            "http",
            "https",
            "website",
            "nikto",
            "nuclei",
            "web vuln",
            "web vulnerability",
            "web scan",
        ]
        return any(keyword in query_lower for keyword in web_keywords)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web vulnerability scan.

        Args:
            context: Execution context with target

        Returns:
            Scan results
        """
        target = context.get("target", "")
        if not target:
            return {"success": False, "error": "No target specified"}

        # Determine target URL
        if not target.startswith(("http://", "https://")):
            # Try to detect from open ports
            open_ports = context.get("open_ports", [])
            use_https = False
            for port_info in open_ports:
                port = port_info.get("port", 0)
                if port == 443:
                    use_https = True
                    break
            target = f"{'https' if use_https else 'http'}://{target}"

        # Perform scan
        result = self.web_tools.quick_web_scan(target)

        # Extract findings
        findings = []
        for finding in result.get("findings", []):
            findings.append({
                "type": "web_vulnerability",
                "target": target,
                "severity": finding.get("severity", "medium"),
                "description": finding.get("description", finding.get("name", "")),
                "evidence": finding,
            })

        return {
            "success": result.get("success", True),
            "plugin": self.name,
            "target": target,
            "findings": findings,
            "nikto_results": result.get("nikto", {}),
            "nuclei_results": result.get("nuclei", {}),
            "raw_result": result,
        }

