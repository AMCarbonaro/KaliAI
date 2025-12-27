"""Metasploit tool wrapper for safe execution."""

from typing import Any, Dict, List, Optional

from kali_orchestrator.hexstrike_client import HexstrikeClient


class MetasploitWrapper:
    """Wrapper for Metasploit module execution."""

    def __init__(self, hexstrike_client: HexstrikeClient):
        """Initialize Metasploit wrapper.

        Args:
            hexstrike_client: hexstrike-ai MCP client
        """
        self.hexstrike = hexstrike_client

    def search_modules(self, search_term: str, module_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for Metasploit modules.

        Args:
            search_term: Search term (e.g., "eternalblue", "ms17-010")
            module_type: Optional module type filter (exploit, auxiliary, payload, etc.)

        Returns:
            List of matching modules
        """
        params = {
            "search": search_term,
        }
        if module_type:
            params["type"] = module_type

        try:
            result = self.hexstrike.execute_tool("metasploit", {"action": "search", **params})
            if isinstance(result, dict) and "modules" in result:
                return result["modules"]
            if isinstance(result, list):
                return result
            return []
        except Exception:
            return []

    def get_module_info(self, module_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific module.

        Args:
            module_path: Full module path (e.g., "exploit/windows/smb/ms17_010_eternalblue")

        Returns:
            Module information dictionary or None
        """
        params = {
            "action": "info",
            "module": module_path,
        }

        try:
            result = self.hexstrike.execute_tool("metasploit", params)
            return result if isinstance(result, dict) else None
        except Exception:
            return None

    def suggest_exploits(self, service: str, version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Suggest Metasploit exploits for a detected service.

        Args:
            service: Service name (e.g., "SMB", "HTTP", "SSH")
            version: Optional service version

        Returns:
            List of suggested exploit modules
        """
        search_terms = [service]
        if version:
            search_terms.append(f"{service} {version}")

        all_modules = []
        for term in search_terms:
            modules = self.search_modules(term, module_type="exploit")
            all_modules.extend(modules)

        # Deduplicate
        seen = set()
        unique_modules = []
        for module in all_modules:
            module_path = module.get("fullname") or module.get("path", "")
            if module_path and module_path not in seen:
                seen.add(module_path)
                unique_modules.append(module)

        return unique_modules

    def check_vulnerability(self, target: str, module_path: str) -> Dict[str, Any]:
        """Check if a target is vulnerable using an auxiliary module.

        Args:
            target: Target IP
            module_path: Auxiliary module path (e.g., "auxiliary/scanner/smb/smb_ms17_010")

        Returns:
            Vulnerability check results
        """
        params = {
            "action": "run",
            "module": module_path,
            "target": target,
            "mode": "check",  # Safe check mode
        }

        try:
            result = self.hexstrike.execute_tool("metasploit", params)
            return {
                "success": True,
                "vulnerable": result.get("vulnerable", False),
                "details": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "vulnerable": False,
            }

