"""Plugin system for extensible tool integration."""

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List

from kali_orchestrator.plugins.base import BasePlugin


def load_plugins(plugins_dir: Path) -> List[BasePlugin]:
    """Auto-load all plugins from the plugins directory.

    Args:
        plugins_dir: Directory containing plugin modules

    Returns:
        List of loaded plugin instances
    """
    plugins = []

    if not plugins_dir.exists():
        return plugins

    # Import built-in plugins
    try:
        from kali_orchestrator.plugins import metasploit_plugin, nmap_plugin, web_vuln_plugin

        # Get plugin classes and instantiate them
        # Note: These will need tool wrappers, so we'll handle them separately
        pass
    except ImportError:
        pass

    # Scan for additional plugin files
    for plugin_file in plugins_dir.glob("*_plugin.py"):
        try:
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find all BasePlugin subclasses
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BasePlugin)
                        and obj != BasePlugin
                    ):
                        # Try to instantiate (may need dependencies)
                        try:
                            plugin = obj()
                            plugins.append(plugin)
                        except Exception as e:
                            print(f"Warning: Could not instantiate plugin {name}: {e}")
        except Exception as e:
            print(f"Warning: Could not load plugin {plugin_file}: {e}")

    return plugins


def create_builtin_plugins(
    nmap_wrapper=None,
    metasploit_wrapper=None,
    web_tools_wrapper=None,
) -> List[BasePlugin]:
    """Create built-in plugin instances with their dependencies.

    Args:
        nmap_wrapper: Nmap wrapper instance
        metasploit_wrapper: Metasploit wrapper instance
        web_tools_wrapper: Web tools wrapper instance

    Returns:
        List of plugin instances
    """
    plugins = []

    if nmap_wrapper:
        from kali_orchestrator.plugins.nmap_plugin import NmapPlugin

        plugins.append(NmapPlugin(nmap_wrapper))

    if metasploit_wrapper:
        from kali_orchestrator.plugins.metasploit_plugin import MetasploitPlugin

        plugins.append(MetasploitPlugin(metasploit_wrapper))

    if web_tools_wrapper:
        from kali_orchestrator.plugins.web_vuln_plugin import WebVulnPlugin

        plugins.append(WebVulnPlugin(web_tools_wrapper))

    return plugins
