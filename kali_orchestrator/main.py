"""Main CLI entry point for Kali AI Orchestrator."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from kali_orchestrator.agent import OrchestratorAgent
from kali_orchestrator.config import OrchestratorConfig
from kali_orchestrator.memory import MemoryManager
from kali_orchestrator.personas import load_persona, list_personas
from kali_orchestrator.reporting import ReportGenerator

app = typer.Typer(help="Kali AI Orchestrator - AI-powered pentesting tool orchestration")
console = Console()


@app.command()
def run(
    query: Optional[str] = typer.Argument(None, help="Natural language query to execute"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    persona: Optional[str] = typer.Option(None, "--persona", "-p", help="Load agent persona"),
    local: bool = typer.Option(False, "--local", help="Force local LLM (Ollama) only"),
    tui: bool = typer.Option(False, "--tui", help="Launch TUI interface"),
):
    """Run the orchestrator with a query."""
    if tui:
        launch_tui(config_path, persona, local)
        return

    # Load config
    config = OrchestratorConfig.load_from_file(config_path)

    # Load persona if specified
    if persona:
        persona_config = load_persona(persona)
        if persona_config:
            console.print(f"[green]Loaded persona: {persona}[/green]")
            # Apply persona settings to config
            if "safety" in persona_config:
                for key, value in persona_config["safety"].items():
                    setattr(config.safety, key, value)
        else:
            console.print(f"[red]Warning: Persona '{persona}' not found[/red]")

    # Initialize memory and agent
    memory = MemoryManager()
    agent = OrchestratorAgent(config, memory, force_local=local)

    # Interactive mode if no query provided
    if not query:
        console.print(Panel.fit("[bold cyan]Kali AI Orchestrator[/bold cyan]\nEnter queries or 'exit' to quit"))
        while True:
            try:
                query = Prompt.ask("\n[bold]Query[/bold]")
                if query.lower() in ["exit", "quit", "q"]:
                    break

                result = agent.process_query(query)

                if result.get("requires_confirmation"):
                    confirmed = Confirm.ask("This action requires confirmation. Proceed?")
                    if confirmed:
                        # Re-run without confirmation requirement
                        result = agent.process_query(query, require_confirmation=False)

                if result.get("success"):
                    console.print(f"\n[green]✓ Success[/green]")
                    console.print(result.get("response", ""))
                else:
                    console.print(f"\n[red]✗ Error[/red]")
                    console.print(result.get("error", "Unknown error"))

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
    else:
        # Single query mode
        result = agent.process_query(query)

        if result.get("requires_confirmation"):
            confirmed = Confirm.ask("This action requires confirmation. Proceed?")
            if confirmed:
                result = agent.process_query(query, require_confirmation=False)

        if result.get("success"):
            console.print(result.get("response", ""))
        else:
            console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            sys.exit(1)


@app.command()
def setup():
    """Set up the orchestrator (pull Ollama models, etc.)."""
    console.print("[bold]Setting up Kali AI Orchestrator...[/bold]")

    # Check for Ollama
    import subprocess

    try:
        result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
        if result.returncode != 0:
            console.print("[yellow]Ollama not found. Install from https://ollama.ai[/yellow]")
            return
    except Exception:
        console.print("[yellow]Could not check for Ollama[/yellow]")
        return

    # Pull recommended models
    recommended_models = ["llama3.2", "deepseek-coder", "mistral"]
    console.print("\n[bold]Pulling recommended Ollama models...[/bold]")

    for model in recommended_models:
        console.print(f"Pulling {model}...")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            console.print(f"[green]✓ {model} pulled successfully[/green]")
        except subprocess.CalledProcessError:
            console.print(f"[red]✗ Failed to pull {model}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    console.print("\n[green]Setup complete![/green]")


@app.command()
def report(
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID"),
    format: str = typer.Option("markdown", "--format", "-f", help="Report format (markdown, html, pdf)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate a report from a session."""
    memory = MemoryManager()
    generator = ReportGenerator(memory)

    try:
        report_path = generator.generate_report(
            session_id=session_id,
            format=format,
            output_path=output,
        )
        console.print(f"[green]Report generated: {report_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        sys.exit(1)


@app.command()
def list_sessions():
    """List all available sessions."""
    memory = MemoryManager()
    sessions = memory.list_sessions()

    if not sessions:
        console.print("[yellow]No sessions found[/yellow]")
        return

    table = Table(title="Available Sessions")
    table.add_column("Session ID", style="cyan")
    table.add_column("Actions", style="green")

    for session_id in sessions:
        table.add_row(session_id, f"kali-orchestrator report -s {session_id}")

    console.print(table)


@app.command()
def personas():
    """List available agent personas."""
    persona_list = list_personas()

    if not persona_list:
        console.print("[yellow]No personas found[/yellow]")
        return

    table = Table(title="Available Personas")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")

    for persona_name in persona_list:
        persona_config = load_persona(persona_name)
        description = persona_config.get("description", "No description") if persona_config else "Unknown"
        table.add_row(persona_name, description)

    console.print(table)


def launch_tui(config_path: Optional[Path], persona: Optional[str], local: bool):
    """Launch the TUI interface."""
    try:
        from kali_orchestrator.tui import OrchestratorTUI

        tui = OrchestratorTUI(config_path, persona, local)
        tui.run()
    except ImportError:
        console.print("[red]TUI dependencies not available. Install with: pip install textual[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error launching TUI: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()

