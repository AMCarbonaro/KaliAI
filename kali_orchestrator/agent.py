"""Core AI agent for orchestrating pentesting tools."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import ipaddress

from kali_orchestrator.config import OrchestratorConfig
from kali_orchestrator.hexstrike_client import HexstrikeClient
from kali_orchestrator.llm_backends import LLMBackend, create_llm_backend
from kali_orchestrator.memory import Finding, MemoryManager, ToolExecution
from kali_orchestrator.plugins import BasePlugin, create_builtin_plugins
from kali_orchestrator.tools import MetasploitWrapper, NmapWrapper, WebToolsWrapper


class SafetyError(Exception):
    """Raised when a safety check fails."""

    pass


class OrchestratorAgent:
    """Core AI agent for orchestrating pentesting operations."""

    def __init__(
        self,
        config: OrchestratorConfig,
        memory: MemoryManager,
        force_local: bool = False,
    ):
        """Initialize the orchestrator agent.

        Args:
            config: Orchestrator configuration
            memory: Memory manager instance
            force_local: Force local LLM (Ollama) only
        """
        self.config = config
        self.memory = memory
        self.logger = self._setup_logging()

        # Initialize hexstrike-ai client
        self.hexstrike = HexstrikeClient(config.hexstrike)
        if config.hexstrike.auto_start:
            self.hexstrike.start_server()

        # Initialize LLM backend
        self.llm = create_llm_backend(config.llm, force_local=force_local)

        # Initialize tool wrappers
        self.nmap = NmapWrapper(self.hexstrike)
        self.metasploit = MetasploitWrapper(self.hexstrike)
        self.web_tools = WebToolsWrapper(self.hexstrike)

        # Initialize plugins
        self.plugins = create_builtin_plugins(
            nmap_wrapper=self.nmap,
            metasploit_wrapper=self.metasploit,
            web_tools_wrapper=self.web_tools,
        )

        # Current execution context
        self.current_context: Dict[str, Any] = {}

    def _setup_logging(self) -> logging.Logger:
        """Set up logging.

        Returns:
            Logger instance
        """
        log_file = Path(self.config.logging.file).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("kali_orchestrator")
        logger.setLevel(getattr(logging, self.config.logging.level.upper()))

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        if self.config.logging.json_log:
            import json

            class JSONFormatter(logging.Formatter):
                def format(self, record):
                    log_entry = {
                        "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                    }
                    if hasattr(record, "extra"):
                        log_entry.update(record.extra)
                    return json.dumps(log_entry)

            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def process_query(self, query: str, require_confirmation: Optional[bool] = None) -> Dict[str, Any]:
        """Process a user query and execute appropriate tools.

        Args:
            query: User's natural language query
            require_confirmation: Override config confirmation setting

        Returns:
            Execution results
        """
        self.logger.info(f"Processing query: {query}")

        # Ensure we have a session
        if self.memory.current_session is None:
            self.memory.create_session()

        # Add user query to memory
        self.memory.add_conversation("user", query)

        # Extract target from query
        target = self._extract_target(query)
        if target:
            # Check scope
            if not self._check_scope(target):
                error_msg = f"Target {target} is out of scope"
                self.logger.warning(error_msg)
                self.memory.add_conversation("assistant", f"Error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "target": target,
                }

        # Check for dangerous actions
        if self._is_dangerous_action(query):
            confirm = require_confirmation
            if confirm is None:
                confirm = self.config.safety.require_confirmation

            if confirm:
                # In CLI mode, this would prompt user
                # For now, we'll log and require explicit confirmation
                self.logger.warning(f"Dangerous action detected in query: {query}")
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "action": query,
                    "message": "This action requires explicit confirmation. Please confirm to proceed.",
                }

        # Build execution context
        context = {
            "query": query,
            "target": target,
            "findings": [f.model_dump() for f in self.memory.current_session.findings],
            "open_ports": self._extract_open_ports_from_memory(),
            "conversation_history": self.memory.current_session.conversation_history[-5:],
        }
        self.current_context = context

        # Get LLM context
        llm_context = self.memory.get_context()

        # Route to LLM for planning
        try:
            planning_prompt = self._build_planning_prompt(query, context)
            llm_response = self.llm.generate(planning_prompt, llm_context)

            self.logger.debug(f"LLM planning response: {llm_response}")

            # Find matching plugins
            matching_plugins = [p for p in self.plugins if p.matches(query)]

            # Execute plugins
            results = []
            for plugin in matching_plugins:
                try:
                    plugin_result = plugin.execute(context)
                    results.append(plugin_result)

                    # Record findings
                    if "findings" in plugin_result:
                        for finding_data in plugin_result["findings"]:
                            finding = Finding(
                                id=f"{plugin.name}_{datetime.now().timestamp()}",
                                timestamp=datetime.now().isoformat(),
                                target=target or finding_data.get("target", ""),
                                type=finding_data.get("type", "unknown"),
                                severity=finding_data.get("severity", "info"),
                                description=finding_data.get("description", ""),
                                evidence=finding_data.get("evidence", {}),
                                recommendations=finding_data.get("recommendations", []),
                            )
                            self.memory.add_finding(finding)

                    # Record tool executions
                    if "raw_result" in plugin_result:
                        execution = ToolExecution(
                            timestamp=datetime.now().isoformat(),
                            tool=plugin.name,
                            command=str(plugin_result.get("raw_result", {})),
                            target=target or "",
                            output=str(plugin_result),
                            exit_code=0 if plugin_result.get("success") else 1,
                            duration_seconds=0.0,  # Would be measured in real implementation
                        )
                        self.memory.add_tool_execution(execution)

                except Exception as e:
                    self.logger.error(f"Plugin {plugin.name} execution error: {e}")
                    results.append({
                        "success": False,
                        "plugin": plugin.name,
                        "error": str(e),
                    })

            # Generate response summary
            response = self._generate_response_summary(query, results, llm_response)

            # Save to memory
            self.memory.add_conversation("assistant", response)
            self.memory.save_session()

            return {
                "success": True,
                "query": query,
                "target": target,
                "plugins_executed": [p.name for p in matching_plugins],
                "results": results,
                "response": response,
                "llm_planning": llm_response,
            }

        except Exception as e:
            error_msg = f"Error processing query: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.memory.add_conversation("assistant", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "query": query,
            }

    def _extract_target(self, query: str) -> Optional[str]:
        """Extract target IP/domain from query.

        Args:
            query: User query

        Returns:
            Target string or None
        """
        # Try to find IP addresses
        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b"
        ip_matches = re.findall(ip_pattern, query)
        if ip_matches:
            return ip_matches[0]

        # Try to find domains
        domain_pattern = r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
        domain_matches = re.findall(domain_pattern, query)
        if domain_matches:
            # Filter out common non-target domains
            excluded = ["example.com", "localhost", "127.0.0.1"]
            for domain in domain_matches:
                if domain not in excluded:
                    return domain

        return None

    def _check_scope(self, target: str) -> bool:
        """Check if target is within allowed scope.

        Args:
            target: Target IP or domain

        Returns:
            True if target is in scope
        """
        if not self.config.scope.strict_mode:
            return True

        # Check IP ranges
        for allowed_ip in self.config.scope.allowed_ips:
            try:
                if "/" in allowed_ip:
                    # CIDR range
                    network = ipaddress.ip_network(allowed_ip, strict=False)
                    if "/" in target:
                        target_net = ipaddress.ip_network(target, strict=False)
                        if target_net.subnet_of(network):
                            return True
                    else:
                        target_ip = ipaddress.ip_address(target)
                        if target_ip in network:
                            return True
                else:
                    # Single IP
                    if target == allowed_ip:
                        return True
            except ValueError:
                # Not an IP, continue
                pass

        # Check domains
        for allowed_domain in self.config.scope.allowed_domains:
            if target == allowed_domain or target.endswith(f".{allowed_domain}"):
                return True

        return False

    def _is_dangerous_action(self, query: str) -> bool:
        """Check if query contains dangerous action keywords.

        Args:
            query: User query

        Returns:
            True if dangerous action detected
        """
        query_lower = query.lower()
        for keyword in self.config.safety.dangerous_actions:
            if keyword in query_lower:
                return True
        return False

    def _extract_open_ports_from_memory(self) -> List[Dict[str, Any]]:
        """Extract open ports from memory findings.

        Returns:
            List of open port information
        """
        if not self.memory.current_session:
            return []

        open_ports = []
        for finding in self.memory.current_session.findings:
            if finding.type == "open_port":
                open_ports.append({
                    "port": finding.evidence.get("port"),
                    "service": finding.evidence.get("service", ""),
                    "version": finding.evidence.get("version", ""),
                })
        return open_ports

    def _build_planning_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build prompt for LLM planning.

        Args:
            query: User query
            context: Execution context

        Returns:
            Planning prompt
        """
        prompt_parts = [
            "You are an AI assistant helping with penetration testing operations.",
            "Analyze the user's request and determine what tools and actions are needed.",
            "",
            f"User query: {query}",
        ]

        if context.get("target"):
            prompt_parts.append(f"Target: {context['target']}")

        if context.get("findings"):
            prompt_parts.append("\nRecent findings:")
            for finding in context["findings"][:5]:
                prompt_parts.append(f"- {finding.get('type')}: {finding.get('description', '')}")

        prompt_parts.append("\nWhat tools should be executed? Provide a brief plan.")

        return "\n".join(prompt_parts)

    def _generate_response_summary(
        self, query: str, results: List[Dict[str, Any]], llm_planning: str
    ) -> str:
        """Generate user-friendly response summary.

        Args:
            query: Original user query
            results: Plugin execution results
            llm_planning: LLM planning response

        Returns:
            Response summary
        """
        summary_parts = [f"Processed query: {query}\n"]

        if results:
            summary_parts.append("Execution results:")
            for result in results:
                plugin_name = result.get("plugin", "unknown")
                success = result.get("success", False)
                status = "✓" if success else "✗"
                summary_parts.append(f"{status} {plugin_name}")

                if "findings" in result:
                    count = len(result["findings"])
                    summary_parts.append(f"  Found {count} finding(s)")

                if "suggested_exploits" in result:
                    count = len(result["suggested_exploits"])
                    summary_parts.append(f"  Suggested {count} exploit(s)")

        else:
            summary_parts.append("No matching plugins found for this query.")

        # Add next steps if findings exist
        findings_count = len(self.memory.current_session.findings) if self.memory.current_session else 0
        if findings_count > 0:
            summary_parts.append(f"\nTotal findings in session: {findings_count}")
            summary_parts.append("Consider running additional scans or generating a report.")

        return "\n".join(summary_parts)

    def confirm_action(self, action: str) -> bool:
        """Confirm a dangerous action (to be called by CLI/TUI).

        Args:
            action: Action description

        Returns:
            True if confirmed
        """
        # This would be implemented in CLI/TUI to prompt user
        # For now, return False as default
        return False

