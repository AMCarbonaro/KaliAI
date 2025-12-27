"""Text User Interface for Kali AI Orchestrator."""

from pathlib import Path
from typing import Optional

from rich.console import RenderableType
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Log, Static

from kali_orchestrator.agent import OrchestratorAgent
from kali_orchestrator.config import OrchestratorConfig
from kali_orchestrator.memory import MemoryManager
from kali_orchestrator.personas import load_persona
from kali_orchestrator.reporting import ReportGenerator


class ChatPanel(Container):
    """Chat panel for user input and agent responses."""

    def compose(self) -> ComposeResult:
        yield Static("Chat", id="chat_title")
        yield Log(id="chat_log", wrap=True)
        yield Input(placeholder="Enter your query...", id="chat_input")


class Sidebar(Container):
    """Sidebar showing scope, targets, and memory summary."""

    def compose(self) -> ComposeResult:
        yield Static("Scope & Status", id="sidebar_title")
        yield Static(id="scope_info")
        yield Static(id="targets_info")
        yield Static(id="memory_summary")


class LogPanel(Container):
    """Log panel for tool output and agent reasoning."""

    def compose(self) -> ComposeResult:
        yield Static("Tool Output & Logs", id="log_title")
        yield Log(id="tool_log", wrap=True)


class OrchestratorTUI(App):
    """Main TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    #chat_panel {
        width: 2fr;
        border: solid $primary;
    }
    
    #sidebar {
        width: 1fr;
        border: solid $secondary;
    }
    
    #log_panel {
        height: 30%;
        border: solid $accent;
    }
    
    .warning {
        color: $warning;
    }
    
    .error {
        color: $error;
    }
    
    .success {
        color: $success;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "report", "Generate Report"),
        ("s", "scope", "Update Scope"),
        ("m", "memory", "View Memory"),
    ]

    def __init__(
        self,
        config_path: Optional[Path] = None,
        persona: Optional[str] = None,
        local: bool = False,
    ):
        """Initialize TUI.

        Args:
            config_path: Path to config file
            persona: Persona name to load
            local: Force local LLM only
        """
        super().__init__()
        self.config = OrchestratorConfig.load_from_file(config_path)
        self.memory = MemoryManager()
        self.agent = OrchestratorAgent(self.config, self.memory, force_local=local)
        self.report_generator = ReportGenerator(self.memory)

        # Load persona if specified
        if persona:
            persona_config = load_persona(persona)
            if persona_config and "safety" in persona_config:
                for key, value in persona_config["safety"].items():
                    setattr(self.config.safety, key, value)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Horizontal():
            with Vertical():
                yield ChatPanel(id="chat_panel")
                yield LogPanel(id="log_panel")
            yield Sidebar(id="sidebar")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.update_sidebar()
        self.query_one("#chat_log", Log).write("[bold cyan]Kali AI Orchestrator[/bold cyan]")
        self.query_one("#chat_log", Log).write("Enter your queries below. Type /help for commands.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        query = event.value
        input_widget = event.input
        input_widget.value = ""

        # Handle commands
        if query.startswith("/"):
            self.handle_command(query)
            return

        # Display user query
        self.query_one("#chat_log", Log).write(f"[bold]You:[/bold] {query}")

        # Process query
        self.query_one("#tool_log", Log).write(f"[dim]Processing query: {query}[/dim]")

        try:
            result = self.agent.process_query(query)

            if result.get("requires_confirmation"):
                self.query_one("#chat_log", Log).write(
                    "[yellow]⚠ This action requires confirmation. Use /confirm to proceed.[/yellow]"
                )
                self.pending_confirmation = query
                return

            if result.get("success"):
                response = result.get("response", "")
                self.query_one("#chat_log", Log).write(f"[bold]Agent:[/bold] {response}")

                # Log tool executions
                for plugin_name in result.get("plugins_executed", []):
                    self.query_one("#tool_log", Log).write(f"[green]✓ Executed: {plugin_name}[/green]")
            else:
                error = result.get("error", "Unknown error")
                self.query_one("#chat_log", Log).write(f"[red]Error: {error}[/red]")

            self.update_sidebar()

        except Exception as e:
            self.query_one("#chat_log", Log).write(f"[red]Error: {e}[/red]")
            self.query_one("#tool_log", Log).write(f"[red]Exception: {e}[/red]")

    def handle_command(self, command: str) -> None:
        """Handle TUI commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/help":
            help_text = """
[bold]Commands:[/bold]
/scope - Update allowed targets
/report - Generate report
/memory - View/clear persistent context
/persona <name> - Load agent persona
/exit - Exit TUI
            """
            self.query_one("#chat_log", Log).write(help_text)

        elif cmd == "/scope":
            self.query_one("#chat_log", Log).write("[yellow]Scope update not yet implemented in TUI[/yellow]")

        elif cmd == "/report":
            try:
                report_path = self.report_generator.generate_report()
                self.query_one("#chat_log", Log).write(f"[green]Report generated: {report_path}[/green]")
            except Exception as e:
                self.query_one("#chat_log", Log).write(f"[red]Error: {e}[/red]")

        elif cmd == "/memory":
            session = self.memory.current_session
            if session:
                findings_count = len(session.findings)
                self.query_one("#chat_log", Log).write(f"Session: {session.session_id}")
                self.query_one("#chat_log", Log).write(f"Findings: {findings_count}")
            else:
                self.query_one("#chat_log", Log).write("[yellow]No active session[/yellow]")

        elif cmd == "/persona" and len(parts) > 1:
            persona_name = parts[1]
            persona_config = load_persona(persona_name)
            if persona_config:
                self.query_one("#chat_log", Log).write(f"[green]Loaded persona: {persona_name}[/green]")
            else:
                self.query_one("#chat_log", Log).write(f"[red]Persona not found: {persona_name}[/red]")

        elif cmd == "/exit":
            self.exit()

        else:
            self.query_one("#chat_log", Log).write(f"[yellow]Unknown command: {cmd}[/yellow]")

    def update_sidebar(self) -> None:
        """Update sidebar information."""
        scope_widget = self.query_one("#scope_info", Static)
        targets_widget = self.query_one("#targets_info", Static)
        memory_widget = self.query_one("#memory_summary", Static)

        # Scope info
        allowed_ips = ", ".join(self.config.scope.allowed_ips[:3])
        if len(self.config.scope.allowed_ips) > 3:
            allowed_ips += "..."
        scope_text = f"Allowed IPs: {allowed_ips}\nStrict Mode: {self.config.scope.strict_mode}"
        scope_widget.update(scope_text)

        # Targets info
        session = self.memory.current_session
        if session:
            targets = set(f.target for f in session.findings if f.target)
            targets_text = f"Active Targets: {len(targets)}\n" + "\n".join(list(targets)[:3])
        else:
            targets_text = "No active targets"
        targets_widget.update(targets_text)

        # Memory summary
        if session:
            findings_count = len(session.findings)
            memory_text = f"Findings: {findings_count}\nSession: {session.session_id[:20]}..."
        else:
            memory_text = "No active session"
        memory_widget.update(memory_text)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_report(self) -> None:
        """Generate report."""
        self.handle_command("/report")

    def action_scope(self) -> None:
        """Update scope."""
        self.handle_command("/scope")

    def action_memory(self) -> None:
        """View memory."""
        self.handle_command("/memory")

