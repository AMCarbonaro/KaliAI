"""Report generation module for findings and test results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from kali_orchestrator.memory import MemoryManager


class ReportGenerator:
    """Generate reports in multiple formats (Markdown, HTML, PDF)."""

    def __init__(self, memory: MemoryManager):
        """Initialize report generator.

        Args:
            memory: Memory manager instance
        """
        self.memory = memory

    def generate_report(
        self,
        session_id: Optional[str] = None,
        format: str = "markdown",
        output_path: Optional[Path] = None,
        bug_bounty_template: bool = True,
    ) -> Path:
        """Generate a report for a session.

        Args:
            session_id: Session ID to report on. Uses current session if None.
            format: Report format (markdown, html, pdf)
            output_path: Output file path. Auto-generated if None.
            bug_bounty_template: Use bug bounty template format

        Returns:
            Path to generated report
        """
        # Load session
        if session_id:
            session = self.memory.load_session(session_id)
        else:
            session = self.memory.current_session

        if not session:
            raise ValueError("No session available for reporting")

        # Generate markdown content
        markdown_content = self._generate_markdown(session, bug_bounty_template)

        # Determine output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path.home() / ".kali-orchestrator" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"report_{session.session_id}_{timestamp}.{format}"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate in requested format
        if format == "markdown":
            output_path.write_text(markdown_content)
        elif format == "html":
            html_content = self._markdown_to_html(markdown_content)
            output_path.write_text(html_content)
        elif format == "pdf":
            html_content = self._markdown_to_html(markdown_content)
            self._html_to_pdf(html_content, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return output_path

    def _generate_markdown(self, session, bug_bounty_template: bool) -> str:
        """Generate Markdown report content.

        Args:
            session: Session memory object
            bug_bounty_template: Use bug bounty template

        Returns:
            Markdown content
        """
        lines = []

        # Title
        lines.append("# Penetration Test Report")
        lines.append("")
        lines.append(f"**Session ID:** {session.session_id}")
        lines.append(f"**Date:** {session.created_at}")
        lines.append(f"**Last Updated:** {session.updated_at}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        findings_count = len(session.findings)
        critical_count = sum(1 for f in session.findings if f.severity == "critical")
        high_count = sum(1 for f in session.findings if f.severity == "high")
        medium_count = sum(1 for f in session.findings if f.severity == "medium")
        low_count = sum(1 for f in session.findings if f.severity == "low")

        lines.append(f"This report summarizes {findings_count} finding(s) discovered during the penetration test.")
        lines.append("")
        lines.append("**Risk Summary:**")
        lines.append(f"- Critical: {critical_count}")
        lines.append(f"- High: {high_count}")
        lines.append(f"- Medium: {medium_count}")
        lines.append(f"- Low: {low_count}")
        lines.append("")

        # Scope
        lines.append("## Scope")
        lines.append("")
        # Extract unique targets from findings
        targets = set()
        for finding in session.findings:
            if finding.target:
                targets.add(finding.target)
        if targets:
            lines.append("**Tested Targets:**")
            for target in sorted(targets):
                lines.append(f"- {target}")
        else:
            lines.append("No specific targets identified.")
        lines.append("")

        # Methodology
        lines.append("## Methodology")
        lines.append("")
        tools_used = set()
        for execution in session.tool_executions:
            tools_used.add(execution.tool)
        if tools_used:
            lines.append("**Tools Used:**")
            for tool in sorted(tools_used):
                lines.append(f"- {tool}")
        lines.append("")
        lines.append("All tools were executed in isolated, containerized environments for safety.")
        lines.append("")

        # Findings
        lines.append("## Findings")
        lines.append("")

        if not session.findings:
            lines.append("No findings to report.")
        else:
            # Group by severity
            by_severity = {
                "critical": [],
                "high": [],
                "medium": [],
                "low": [],
                "info": [],
            }
            for finding in session.findings:
                severity = finding.severity.lower()
                if severity not in by_severity:
                    severity = "info"
                by_severity[severity].append(finding)

            # Output by severity order
            for severity in ["critical", "high", "medium", "low", "info"]:
                findings_list = by_severity[severity]
                if not findings_list:
                    continue

                lines.append(f"### {severity.upper()} Severity Findings")
                lines.append("")

                for idx, finding in enumerate(findings_list, 1):
                    lines.append(f"#### {idx}. {finding.type.replace('_', ' ').title()}")
                    lines.append("")
                    lines.append(f"**Target:** {finding.target}")
                    lines.append(f"**Description:** {finding.description}")
                    lines.append("")

                    if finding.evidence:
                        lines.append("**Evidence:**")
                        lines.append("```json")
                        lines.append(json.dumps(finding.evidence, indent=2))
                        lines.append("```")
                        lines.append("")

                    if finding.recommendations:
                        lines.append("**Recommendations:**")
                        for rec in finding.recommendations:
                            lines.append(f"- {rec}")
                        lines.append("")

                    if bug_bounty_template:
                        lines.append("**Reproduction Steps:**")
                        lines.append("1. [Steps to reproduce]")
                        lines.append("")
                        lines.append("**Impact:**")
                        lines.append("[Describe the security impact]")
                        lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        if session.findings:
            lines.append("Based on the findings, the following recommendations are made:")
            lines.append("")
            # Generate recommendations from findings
            recommendations = set()
            for finding in session.findings:
                recommendations.update(finding.recommendations)
            if recommendations:
                for rec in sorted(recommendations):
                    lines.append(f"- {rec}")
            else:
                lines.append("- Review and remediate all identified vulnerabilities")
                lines.append("- Implement regular security scanning")
                lines.append("- Keep systems and software up to date")
        else:
            lines.append("No specific recommendations at this time.")
        lines.append("")

        # Appendices
        lines.append("## Appendices")
        lines.append("")

        # Tool Execution Logs
        if session.tool_executions:
            lines.append("### Tool Execution Logs")
            lines.append("")
            for execution in session.tool_executions:
                lines.append(f"**{execution.tool}** - {execution.timestamp}")
                lines.append(f"- Command: `{execution.command[:100]}...`")
                lines.append(f"- Exit Code: {execution.exit_code}")
                lines.append("")
        lines.append("")

        # Raw Data
        lines.append("### Raw Session Data")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(session.model_dump(mode="json"), indent=2))
        lines.append("```")

        return "\n".join(lines)

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML.

        Args:
            markdown: Markdown content

        Returns:
            HTML content
        """
        # Simple markdown to HTML conversion
        # In production, use a library like markdown or mistune
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Penetration Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .severity-critical {{ color: #e74c3c; font-weight: bold; }}
        .severity-high {{ color: #e67e22; font-weight: bold; }}
        .severity-medium {{ color: #f39c12; }}
        .severity-low {{ color: #3498db; }}
    </style>
</head>
<body>
{self._simple_markdown_to_html(markdown)}
</body>
</html>"""
        return html

    def _simple_markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML converter.

        Args:
            markdown: Markdown text

        Returns:
            HTML text
        """
        html = markdown
        # Headers
        html = html.replace("#### ", "<h4>").replace("\n", "</h4>\n", 1) if "#### " in html else html
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1) if "### " in html else html
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1) if "## " in html else html
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1) if "# " in html else html

        # Bold
        html = html.replace("**", "<strong>").replace("**", "</strong>")

        # Code blocks
        import re

        html = re.sub(r"```(\w+)?\n(.*?)```", r"<pre><code>\2</code></pre>", html, flags=re.DOTALL)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

        # Lists
        lines = html.split("\n")
        in_list = False
        result_lines = []
        for line in lines:
            if line.strip().startswith("- "):
                if not in_list:
                    result_lines.append("<ul>")
                    in_list = True
                result_lines.append(f"<li>{line.strip()[2:]}</li>")
            else:
                if in_list:
                    result_lines.append("</ul>")
                    in_list = False
                result_lines.append(line)
        if in_list:
            result_lines.append("</ul>")
        html = "\n".join(result_lines)

        # Paragraphs
        html = html.replace("\n\n", "</p><p>")
        html = f"<p>{html}</p>"

        return html

    def _html_to_pdf(self, html_content: str, output_path: Path) -> None:
        """Convert HTML to PDF using WeasyPrint.

        Args:
            html_content: HTML content
            output_path: Output PDF path
        """
        try:
            from weasyprint import HTML

            HTML(string=html_content).write_pdf(output_path)
        except ImportError:
            raise ImportError(
                "WeasyPrint not installed. Install with: pip install weasyprint"
            )
        except Exception as e:
            raise RuntimeError(f"PDF generation error: {e}")

