"""Base plugin class for extensible tool integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePlugin(ABC):
    """Base class for all plugins."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def matches(self, query: str) -> bool:
        """Check if this plugin should handle the given query.

        Args:
            query: User query string

        Returns:
            True if plugin should handle this query
        """
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin with the given context.

        Args:
            context: Execution context (target, tools, memory, etc.)

        Returns:
            Execution results
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """Get plugin information.

        Returns:
            Plugin info dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
        }

