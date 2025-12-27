"""Web vulnerability scanning tool wrappers."""

from typing import Any, Dict, List, Optional

from kali_orchestrator.hexstrike_client import HexstrikeClient


class WebToolsWrapper:
    """Wrapper for web vulnerability scanning tools (Nikto, Nuclei, etc.)."""

    def __init__(self, hexstrike_client: HexstrikeClient):
        """Initialize web tools wrapper.

        Args:
            hexstrike_client: hexstrike-ai MCP client
        """
        self.hexstrike = hexstrike_client

    def nikto_scan(self, target: str, port: int = 80, ssl: bool = False) -> Dict[str, Any]:
        """Run Nikto web server scanner.

        Args:
            target: Target hostname or IP
            port: Target port
            ssl: Use SSL/TLS

        Returns:
            Scan results
        """
        params = {
            "target": target,
            "port": port,
            "ssl": ssl,
        }

        try:
            result = self.hexstrike.execute_tool("nikto", params)
            return self._parse_nikto_output(result)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "target": target,
                "findings": [],
            }

    def nuclei_scan(self, target: str, templates: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run Nuclei vulnerability scanner.

        Args:
            target: Target URL or IP
            templates: Optional list of template tags/categories

        Returns:
            Scan results
        """
        params = {
            "target": target,
        }
        if templates:
            params["templates"] = templates

        try:
            result = self.hexstrike.execute_tool("nuclei", params)
            return self._parse_nuclei_output(result)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "target": target,
                "findings": [],
            }

    def quick_web_scan(self, target: str) -> Dict[str, Any]:
        """Perform a quick web vulnerability scan (Nikto + Nuclei basic).

        Args:
            target: Target URL or IP

        Returns:
            Combined scan results
        """
        results = {
            "target": target,
            "nikto": {},
            "nuclei": {},
            "findings": [],
        }

        # Determine if HTTPS
        if target.startswith("https://"):
            url = target
            ssl = True
            port = 443
        elif target.startswith("http://"):
            url = target
            ssl = False
            port = 80
        else:
            # Assume HTTP by default
            url = f"http://{target}"
            ssl = False
            port = 80

        # Run Nikto
        results["nikto"] = self.nikto_scan(target.replace("http://", "").replace("https://", ""), port, ssl)

        # Run Nuclei with common templates
        results["nuclei"] = self.nuclei_scan(url, templates=["cves", "vulnerabilities", "exposures"])

        # Combine findings
        if "findings" in results["nikto"]:
            results["findings"].extend(results["nikto"]["findings"])
        if "findings" in results["nuclei"]:
            results["findings"].extend(results["nuclei"]["findings"])

        return results

    def _parse_nikto_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Nikto output.

        Args:
            raw_output: Raw output from hexstrike-ai

        Returns:
            Parsed results
        """
        result = {
            "success": raw_output.get("success", True),
            "target": raw_output.get("target", ""),
            "findings": [],
        }

        if "findings" in raw_output:
            result["findings"] = raw_output["findings"]
        elif "vulnerabilities" in raw_output:
            result["findings"] = raw_output["vulnerabilities"]

        result["raw_output"] = raw_output
        return result

    def _parse_nuclei_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Nuclei output.

        Args:
            raw_output: Raw output from hexstrike-ai

        Returns:
            Parsed results
        """
        result = {
            "success": raw_output.get("success", True),
            "target": raw_output.get("target", ""),
            "findings": [],
        }

        if "matches" in raw_output:
            result["findings"] = raw_output["matches"]
        elif "results" in raw_output:
            result["findings"] = raw_output["results"]
        elif "findings" in raw_output:
            result["findings"] = raw_output["findings"]

        result["raw_output"] = raw_output
        return result

