"""Web interface for Kali AI Orchestrator using Gradio."""

import sys
import gradio as gr
from kali_orchestrator.agent import OrchestratorAgent
from kali_orchestrator.config import OrchestratorConfig
from kali_orchestrator.memory import MemoryManager
from kali_orchestrator.personas import list_personas, load_persona
from kali_orchestrator.reporting import ReportGenerator


class WebOrchestrator:
    """Web-based orchestrator interface."""

    def __init__(self):
        """Initialize web orchestrator."""
        try:
            print("Loading configuration...", file=sys.stderr)
            self.config = OrchestratorConfig.load_from_file()
            print("Initializing memory manager...", file=sys.stderr)
            self.memory = MemoryManager()
            print("Initializing agent...", file=sys.stderr)
            self.agent = OrchestratorAgent(self.config, self.memory, force_local=False)
            print("Initializing report generator...", file=sys.stderr)
            self.report_generator = ReportGenerator(self.memory)
            self.current_persona = None
            print("✅ Web orchestrator initialized successfully", file=sys.stderr)
        except Exception as e:
            print(f"❌ Error initializing orchestrator: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise

    def process_query(self, query: str, persona: str = None, history: list = None):
        """Process a user query.

        Args:
            query: User query string
            persona: Selected persona name
            history: Chat history

        Returns:
            Updated history, empty query input, formatted results
        """
        if history is None:
            history = []

        if not query.strip():
            return history, "", ""

        # Load persona if changed
        if persona and persona != "None" and persona != self.current_persona:
            persona_config = load_persona(persona)
            if persona_config and "safety" in persona_config:
                for key, value in persona_config["safety"].items():
                    setattr(self.config.safety, key, value)
            self.current_persona = persona

        # Process query
        try:
            result = self.agent.process_query(query, require_confirmation=False)

            if result.get("success"):
                response = result.get("response", "")
                history.append((query, response))
                results_text = self._format_results(result)
                return history, "", results_text
            else:
                error = result.get("error", "Unknown error")
                history.append((query, f"❌ Error: {error}"))
                return history, "", f"**Error:** {error}"
        except Exception as e:
            error_msg = f"Exception occurred: {str(e)}"
            history.append((query, f"❌ {error_msg}"))
            return history, "", f"**Error:** {error_msg}"

    def _format_results(self, result: dict) -> str:
        """Format results for display.

        Args:
            result: Agent execution result

        Returns:
            Formatted markdown string
        """
        output = []
        output.append("## Execution Results\n")

        if result.get("plugins_executed"):
            output.append("**Plugins Executed:**")
            for plugin in result["plugins_executed"]:
                output.append(f"- ✓ {plugin}")

        if result.get("results"):
            output.append("\n**Findings:**")
            for res in result["results"]:
                if res.get("findings"):
                    output.append(f"\n### {res.get('plugin', 'Unknown')}")
                    for finding in res["findings"][:5]:  # Limit to 5
                        output.append(f"- {finding.get('type', 'unknown')}: {finding.get('description', '')}")

                if res.get("suggested_exploits"):
                    output.append(f"\n### {res.get('plugin', 'Unknown')} - Exploit Suggestions")
                    for exploit in res["suggested_exploits"][:3]:  # Limit to 3
                        exploit_name = exploit.get("fullname") or exploit.get("name", "Unknown")
                        output.append(f"- {exploit_name}")

        # Update session info
        if self.memory.current_session:
            findings_count = len(self.memory.current_session.findings)
            output.append(f"\n**Session:** {self.memory.current_session.session_id}")
            output.append(f"**Total Findings:** {findings_count}")

        return "\n".join(output)

    def generate_report(self, format_type: str = "markdown"):
        """Generate a report.

        Args:
            format_type: Report format (markdown, html, pdf)

        Returns:
            Status message
        """
        try:
            report_path = self.report_generator.generate_report(format=format_type)
            return f"✅ Report generated: {report_path}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_session_info(self) -> str:
        """Get current session information.

        Returns:
            Session info string
        """
        if self.memory.current_session:
            findings_count = len(self.memory.current_session.findings)
            return f"Session: {self.memory.current_session.session_id}\nFindings: {findings_count}"
        return "No active session"

    def launch(self, share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
        """Launch Gradio interface.

        Args:
            share: Enable Gradio sharing
            server_name: Server hostname
            server_port: Server port
        """
        personas = list_personas()

        with gr.Blocks(title="Kali AI Orchestrator", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🎯 Kali AI Orchestrator")
            gr.Markdown("AI-powered pentesting tool orchestration with natural language interface")

            with gr.Row():
                with gr.Column(scale=2):
                    persona_dropdown = gr.Dropdown(
                        choices=["None"] + personas,
                        label="Agent Persona",
                        value="None",
                        info="Select an agent persona to modify behavior"
                    )

                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=400,
                        show_copy_button=True,
                        show_label=True,
                    )

                    query_input = gr.Textbox(
                        label="Enter your query",
                        placeholder="e.g., Scan 192.168.1.0/24 for open HTTP services",
                        lines=2,
                    )

                    with gr.Row():
                        submit_btn = gr.Button("Submit", variant="primary", scale=1)
                        clear_btn = gr.Button("Clear", variant="secondary", scale=1)

                with gr.Column(scale=1):
                    gr.Markdown("### Session Info")
                    session_info = gr.Textbox(
                        label="Current Session",
                        value=self.get_session_info(),
                        interactive=False,
                        lines=3,
                    )

                    findings_count = gr.Number(
                        label="Findings Count",
                        value=len(self.memory.current_session.findings) if self.memory.current_session else 0,
                        interactive=False,
                    )

                    gr.Markdown("### Reports")
                    report_format = gr.Dropdown(
                        choices=["markdown", "html", "pdf"],
                        label="Report Format",
                        value="markdown",
                    )
                    generate_report_btn = gr.Button("Generate Report", variant="primary")
                    report_output = gr.Textbox(
                        label="Report Status",
                        interactive=False,
                        lines=2,
                    )

                    gr.Markdown("### Scope")
                    scope_info = gr.Textbox(
                        label="Allowed Targets",
                        value=f"IPs: {', '.join(self.config.scope.allowed_ips[:3])}\nDomains: {', '.join(self.config.scope.allowed_domains[:3])}",
                        interactive=False,
                        lines=3,
                    )

            results_display = gr.Markdown(
                label="Execution Results",
                value="Results will appear here after executing queries.",
            )

            # Event handlers
            def submit_query(query, persona, history):
                """Handle query submission."""
                new_history, empty_query, results = self.process_query(query, persona, history)
                # Update session info
                session_text = self.get_session_info()
                findings_num = len(self.memory.current_session.findings) if self.memory.current_session else 0
                return new_history, empty_query, results, session_text, findings_num

            submit_btn.click(
                submit_query,
                inputs=[query_input, persona_dropdown, chatbot],
                outputs=[chatbot, query_input, results_display, session_info, findings_count],
            )

            query_input.submit(
                submit_query,
                inputs=[query_input, persona_dropdown, chatbot],
                outputs=[chatbot, query_input, results_display, session_info, findings_count],
            )

            clear_btn.click(
                lambda: ([], "", "Results cleared.", self.get_session_info(), 0),
                outputs=[chatbot, query_input, results_display, session_info, findings_count],
            )

            generate_report_btn.click(
                self.generate_report,
                inputs=[report_format],
                outputs=[report_output],
            )

            # Auto-refresh session info
            demo.load(
                lambda: (
                    self.get_session_info(),
                    len(self.memory.current_session.findings) if self.memory.current_session else 0,
                ),
                outputs=[session_info, findings_count],
            )

        # Ensure Gradio is accessible from outside container
        demo.launch(
            share=share,
            server_name=server_name,  # 0.0.0.0 to bind to all interfaces
            server_port=server_port,
            show_error=True,
            quiet=False,
            inbrowser=False,  # Don't try to open browser in container
            favicon_path=None,
        )


if __name__ == "__main__":
    import sys
    
    print("🚀 Starting Kali AI Orchestrator Web App...", file=sys.stderr)
    print(f"   Server: 0.0.0.0:7860", file=sys.stderr)
    print(f"   Access: http://localhost:7860", file=sys.stderr)
    sys.stderr.flush()
    
    try:
        app = WebOrchestrator()
        print("✅ Orchestrator initialized successfully", file=sys.stderr)
        sys.stderr.flush()
        app.launch()
    except Exception as e:
        print(f"❌ Error starting web app: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)

