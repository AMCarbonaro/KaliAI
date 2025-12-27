"""Persistent session memory system with JSON storage."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Finding(BaseModel):
    """Represents a discovered vulnerability or finding."""

    id: str
    timestamp: str
    target: str
    type: str  # e.g., "open_port", "vulnerability", "service"
    severity: str  # "critical", "high", "medium", "low", "info"
    description: str
    evidence: Dict[str, Any] = {}
    recommendations: List[str] = []


class ToolExecution(BaseModel):
    """Record of a tool execution."""

    timestamp: str
    tool: str
    command: str
    target: str
    output: str
    exit_code: int
    duration_seconds: float


class SessionMemory(BaseModel):
    """Session memory structure."""

    session_id: str
    created_at: str
    updated_at: str
    conversation_history: List[Dict[str, str]] = []  # [{"role": "user|assistant", "content": "..."}]
    findings: List[Finding] = []
    tool_executions: List[ToolExecution] = []
    context: Dict[str, Any] = {}  # Additional context data


class MemoryManager:
    """Manages persistent memory across sessions."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize memory manager.

        Args:
            base_dir: Base directory for memory storage. Defaults to ~/.kali-orchestrator/memory/
        """
        if base_dir is None:
            base_dir = Path.home() / ".kali-orchestrator" / "memory"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[SessionMemory] = None

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session.

        Args:
            session_id: Optional session ID. If not provided, generates one.

        Returns:
            Session ID
        """
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{timestamp}"

        self.current_session = SessionMemory(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        return session_id

    def load_session(self, session_id: str) -> Optional[SessionMemory]:
        """Load a session from disk.

        Args:
            session_id: Session ID to load

        Returns:
            SessionMemory object or None if not found
        """
        session_file = self.base_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        try:
            with open(session_file, "r") as f:
                data = json.load(f)
            self.current_session = SessionMemory(**data)
            return self.current_session
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def save_session(self, session_id: Optional[str] = None) -> bool:
        """Save current session to disk.

        Args:
            session_id: Optional session ID. Uses current session if not provided.

        Returns:
            True if successful, False otherwise
        """
        if self.current_session is None:
            if session_id:
                self.create_session(session_id)
            else:
                return False

        if session_id:
            self.current_session.session_id = session_id

        self.current_session.updated_at = datetime.now().isoformat()
        session_file = self.base_dir / f"{self.current_session.session_id}.json"

        try:
            with open(session_file, "w") as f:
                json.dump(self.current_session.model_dump(mode="json"), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def add_conversation(self, role: str, content: str) -> None:
        """Add a conversation turn to the current session.

        Args:
            role: "user" or "assistant"
            content: Message content
        """
        if self.current_session is None:
            self.create_session()

        self.current_session.conversation_history.append({"role": role, "content": content})
        self.current_session.updated_at = datetime.now().isoformat()

    def add_finding(self, finding: Finding) -> None:
        """Add a finding to the current session.

        Args:
            finding: Finding object to add
        """
        if self.current_session is None:
            self.create_session()

        self.current_session.findings.append(finding)
        self.current_session.updated_at = datetime.now().isoformat()

    def add_tool_execution(self, execution: ToolExecution) -> None:
        """Add a tool execution record.

        Args:
            execution: ToolExecution object
        """
        if self.current_session is None:
            self.create_session()

        self.current_session.tool_executions.append(execution)
        self.current_session.updated_at = datetime.now().isoformat()

    def get_context(self, max_history: int = 10) -> Dict[str, Any]:
        """Get relevant context for LLM.

        Args:
            max_history: Maximum conversation history items to include

        Returns:
            Context dictionary
        """
        if self.current_session is None:
            return {}

        recent_history = self.current_session.conversation_history[-max_history:]
        recent_findings = self.current_session.findings[-5:]  # Last 5 findings
        recent_executions = self.current_session.tool_executions[-5:]  # Last 5 tool executions

        return {
            "conversation_history": recent_history,
            "recent_findings": [f.model_dump() for f in recent_findings],
            "recent_tool_executions": [e.model_dump() for e in recent_executions],
            "total_findings": len(self.current_session.findings),
            "session_id": self.current_session.session_id,
            "context": self.current_session.context,
        }

    def list_sessions(self) -> List[str]:
        """List all available session IDs.

        Returns:
            List of session IDs
        """
        sessions = []
        for file in self.base_dir.glob("session_*.json"):
            sessions.append(file.stem)
        return sorted(sessions, reverse=True)  # Most recent first

    def clear_session(self) -> None:
        """Clear the current session from memory (does not delete from disk)."""
        self.current_session = None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session file from disk.

        Args:
            session_id: Session ID to delete

        Returns:
            True if successful, False otherwise
        """
        session_file = self.base_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                session_file.unlink()
                if (
                    self.current_session
                    and self.current_session.session_id == session_id
                ):
                    self.clear_session()
                return True
            except Exception as e:
                print(f"Error deleting session {session_id}: {e}")
                return False
        return False

