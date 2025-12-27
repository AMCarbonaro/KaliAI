# Kali AI Orchestrator

AI-powered orchestrator for Kali Linux pentesting tools with hexstrike-ai MCP integration. This tool enables natural language control of over 150+ Kali tools through an intelligent agent that maintains context, enforces safety rails, and generates comprehensive reports.

## Features

- **🌐 Web Interface**: Beautiful, easy-to-use web UI - just download and run!
- **Natural Language Interface**: Control pentesting tools through conversational queries
- **hexstrike-ai Integration**: Seamless integration with Kali's official hexstrike-ai MCP server
- **Multiple LLM Backends**: Support for Ollama (local), gemini-cli, and Google Generative AI
- **Safety Rails**: Strict scope enforcement, confirmation prompts for dangerous actions, containerized execution
- **Persistent Memory**: Session-based memory that persists across runs
- **Extensible Plugins**: Easy-to-create plugins for custom tool integrations
- **Rich Reporting**: Generate Markdown, HTML, and PDF reports with bug bounty templates
- **Agent Personas**: Pre-configured personas for different testing scenarios
- **Docker Support**: Fully containerized deployment with docker-compose - zero installation required

## Installation

### Prerequisites

- Python 3.10+
- Kali Linux 2025.4+ (for hexstrike-ai and gemini-cli packages)
- Docker (optional, for containerized deployment)
- Ollama (optional, for local LLM)

### Install from Source

```bash
git clone <repository-url>
cd kali-ai-orchestrator
pip install -e .
```

### Install Kali Packages

```bash
sudo apt update
sudo apt install hexstrike-ai gemini-cli
```

### Setup Ollama (Optional)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models
kali-orchestrator setup
```

## Quick Start

### 🌐 Web App (Easiest - Recommended)

**True zero-install - automatically installs Docker if needed!**

```bash
# Clone the repository
git clone https://github.com/AMCarbonaro/KaliAI.git
cd KaliAI

# Make start script executable
chmod +x start.sh

# Start everything (one command - auto-installs Docker!)
./start.sh
```

**First time?** The script will automatically:
- ✅ Install Docker (if not present)
- ✅ Install docker-compose
- ✅ Set up all services
- ⚠️ **Note:** After first Docker install, log out and back in (or run `newgrp docker`), then run `./start.sh` again

Then open your browser to **http://localhost:7860** and start using the orchestrator!

The web interface provides:
- Natural language query interface
- Real-time conversation history
- Session management
- Report generation
- Agent persona selection
- Scope visualization

**That's it!** No manual installation, no Python setup, no dependency management - everything is automatic!

### CLI Usage

```bash
# Interactive mode
kali-orchestrator run

# Single query
kali-orchestrator run "Scan 192.168.1.0/24 for open HTTP services"

# TUI mode
kali-orchestrator run --tui

# With persona
kali-orchestrator run --persona web_app "Scan example.com for web vulnerabilities"
```

### Configuration

Edit `kali_orchestrator/config.yaml` to set:
- Allowed IP ranges and domains (scope)
- LLM backend preferences
- Safety settings
- Logging configuration

## Example Interactions

### Example 1: Basic Reconnaissance on a Single IP

**User Prompt:**
```
Scan 192.168.1.100 for open ports and identify services
```

**Agent Actions:**
1. Validates target is in scope (192.168.1.0/24)
2. Routes query to LLM for planning
3. Executes Nmap plugin: `nmap -sV 192.168.1.100`
4. Analyzes results and identifies services
5. Stores findings in memory

**Key Output:**
```
✓ nmap
Found 3 finding(s)

Open Ports:
- Port 22: SSH (OpenSSH 8.2)
- Port 80: HTTP (Apache 2.4.41)
- Port 445: SMB (Windows SMB)

Total findings in session: 3
Consider running additional scans or generating a report.
```

**Generated Report Snippet:**
```markdown
## Findings

### INFO Severity Findings

#### 1. Open Port
**Target:** 192.168.1.100
**Description:** Port 22 is open running SSH service
**Evidence:** {"port": 22, "service": "SSH", "version": "OpenSSH 8.2"}
```

---

### Example 2: Discovering EternalBlue (MS17-010)

**User Prompt:**
```
Scan 192.168.1.50 for MS17-010 and suggest exploits if vulnerable
```

**Agent Actions:**
1. Checks scope for 192.168.1.50
2. Executes Nmap scan to detect SMB service
3. Runs Metasploit auxiliary scanner: `auxiliary/scanner/smb/smb_ms17_010`
4. If vulnerable, searches for exploit modules
5. **Requires confirmation** before suggesting exploit execution

**Key Output:**
```
✓ nmap
✓ metasploit
Found 2 finding(s)
Suggested 1 exploit(s)

Vulnerability Check:
- Target: 192.168.1.50
- Service: SMB
- Status: VULNERABLE to MS17-010

Suggested Exploits:
- exploit/windows/smb/ms17_010_eternalblue

⚠ This action requires confirmation. Use /confirm to proceed.
```

**Generated Report Snippet:**
```markdown
### HIGH Severity Findings

#### 1. Vulnerability
**Target:** 192.168.1.50
**Description:** System is vulnerable to MS17-010 (EternalBlue)
**Severity:** High
**Evidence:** {"cve": "CVE-2017-0144", "service": "SMB", "version": "Windows 7"}

**Recommendations:**
- Apply Microsoft Security Update MS17-010 immediately
- Disable SMBv1 if not required
- Implement network segmentation
```

---

### Example 3: Web Application Reconnaissance

**User Prompt:**
```
Perform a comprehensive web vulnerability scan on https://example.com
```

**Agent Actions:**
1. Validates domain is in scope
2. Executes web vulnerability plugin
3. Runs Nikto scan: `nikto -h https://example.com`
4. Runs Nuclei scan: `nuclei -u https://example.com -t cves,vulnerabilities`
5. Aggregates findings and prioritizes by severity

**Key Output:**
```
✓ web_vuln
Found 5 finding(s)

Web Vulnerability Scan Results:
- Nikto: 12 issues found
- Nuclei: 3 vulnerabilities detected

Findings:
1. [HIGH] SQL Injection vulnerability in /login.php
2. [MEDIUM] XSS in search parameter
3. [MEDIUM] Missing security headers
4. [LOW] Directory listing enabled
5. [INFO] Server version disclosure

Total findings in session: 5
```

**Generated Report Snippet:**
```markdown
### HIGH Severity Findings

#### 1. Web Vulnerability
**Target:** https://example.com
**Description:** SQL Injection vulnerability in /login.php
**Severity:** High
**Evidence:** {"url": "/login.php?id=1'", "parameter": "id", "type": "SQL Injection"}

**Reproduction Steps:**
1. Navigate to https://example.com/login.php?id=1'
2. Observe SQL error in response
3. Confirm injection point with payload: `1' OR '1'='1`

**Impact:**
Potential for complete database compromise, authentication bypass, and data exfiltration.
```

---

### Example 4: Multi-Stage Test with Persistent Memory

**Day 1 - Initial Reconnaissance:**

**User Prompt:**
```
Scan 192.168.1.0/24 for open HTTP services and identify web servers
```

**Agent Actions:**
- Performs network scan
- Identifies 3 web servers
- Stores findings in session memory

**Day 2 - Follow-up Exploitation:**

**User Prompt:**
```
Based on yesterday's scan, check the web servers for common vulnerabilities
```

**Agent Actions:**
1. Loads previous session from memory
2. Retrieves context: 3 web servers identified
3. Executes web vulnerability scans on each target
4. Chains findings from both sessions

**Key Output:**
```
Loaded session: session_20240115_143022
Context: 3 web servers identified from previous scan

✓ web_vuln (executed 3 times)
Found 8 finding(s)

Previous Findings:
- 192.168.1.10: Apache 2.4.41
- 192.168.1.25: Nginx 1.18.0
- 192.168.1.50: IIS 10.0

New Findings:
- 192.168.1.10: 2 vulnerabilities (XSS, Directory Traversal)
- 192.168.1.25: 1 vulnerability (Missing security headers)
- 192.168.1.50: 5 vulnerabilities (SQL Injection, XSS, etc.)

Total findings across sessions: 11
```

**Generated Report Snippet:**
```markdown
## Methodology

**Test Duration:** 2 days
**Sessions:** 
- session_20240115_143022 (Day 1: Reconnaissance)
- session_20240116_091545 (Day 2: Vulnerability Assessment)

**Tools Used:**
- nmap
- nikto
- nuclei

## Findings Summary

**Total Findings:** 11
- Critical: 0
- High: 2
- Medium: 5
- Low: 3
- Info: 1
```

---

### Example 5: Bug Bounty-Style Scoped Testing

**User Prompt:**
```
Test example.com for bug bounty. Focus on subdomain enumeration and web vulnerabilities. Generate a report-ready summary.
```

**Agent Actions:**
1. Loads bug_bounty persona (subdomain enum, screenshots, report-ready)
2. Validates example.com is in scope
3. Executes subdomain enumeration
4. Performs web vulnerability scans on discovered subdomains
5. Captures screenshots (if tools support it)
6. Generates bug bounty formatted report

**Key Output:**
```
Persona: bug_bounty loaded
✓ subdomain_enum
✓ web_vuln
Found 15 finding(s)

Subdomain Discovery:
- api.example.com
- admin.example.com
- staging.example.com
- dev.example.com

Vulnerability Summary:
- api.example.com: 3 vulnerabilities (2 HIGH, 1 MEDIUM)
- admin.example.com: 1 vulnerability (CRITICAL - Authentication Bypass)
- staging.example.com: 2 vulnerabilities (1 HIGH, 1 MEDIUM)
- dev.example.com: 1 vulnerability (MEDIUM)

Report generated: ~/.kali-orchestrator/reports/report_session_20240117_120000_markdown.md
```

**Generated Report Snippet:**
```markdown
# Penetration Test Report

**Session ID:** session_20240117_120000
**Date:** 2024-01-17T12:00:00
**Scope:** example.com and subdomains

## Executive Summary

This report summarizes 15 finding(s) discovered during the penetration test.

**Risk Summary:**
- Critical: 1
- High: 3
- Medium: 3
- Low: 5
- Info: 3

## Findings

### CRITICAL Severity Findings

#### 1. Authentication Bypass
**Target:** admin.example.com
**Description:** Authentication bypass vulnerability allows unauthorized access to admin panel
**Severity:** Critical

**Reproduction Steps:**
1. Navigate to https://admin.example.com/login
2. Enter username: `admin'--`
3. Leave password empty
4. Observe successful login

**Impact:**
Complete administrative access without valid credentials, enabling full system compromise.

**Recommendations:**
- Implement parameterized queries
- Add input validation and sanitization
- Enable WAF rules for SQL injection prevention
```

## Architecture

```
User Input → CLI/TUI → Agent → LLM Backend → hexstrike-ai MCP → Kali Tools (containerized)
                ↓           ↓
            Memory    Safety Rails
                ↓           ↓
            Plugins    Reporting
```

## Configuration

Edit `kali_orchestrator/config.yaml`:

```yaml
scope:
  allowed_ips: ["192.168.1.0/24"]
  allowed_domains: ["example.com"]
  strict_mode: true

llm:
  primary_llm: "ollama"  # ollama | gemini-cli | google-generativeai
  ollama:
    model: "llama3.2"
    base_url: "http://localhost:11434"

safety:
  require_confirmation: true
  dangerous_actions: ["exploit", "payload", "inject"]
  containerized_execution: true
```

## Agent Personas

- **recon_only**: Passive reconnaissance only
- **web_app**: Web application focused testing
- **bug_bounty**: Bug bounty hunter persona
- **red_team**: Red team simulation

Load with: `kali-orchestrator run --persona web_app`

## Docker Deployment

### Web App Deployment (Recommended)

```bash
# One-command start
./start.sh

# Or manually with docker-compose
docker-compose up -d

# Access web interface at http://localhost:7860
```

### CLI Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# Run orchestrator CLI in container
docker exec -it kali-orchestrator kali-orchestrator run --tui
```

## Safety Features

- **Scope Enforcement**: Only allows actions on pre-configured targets
- **Confirmation Prompts**: Requires explicit confirmation for dangerous actions
- **Containerized Execution**: All tools run in isolated containers via hexstrike-ai
- **Comprehensive Logging**: All actions logged with structured JSON format
- **No Destructive Actions**: Exploits and payloads require explicit approval

## Plugin System

Create custom plugins by extending `BasePlugin`:

```python
from kali_orchestrator.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    description = "My custom plugin"
    
    def matches(self, query: str) -> bool:
        return "my keyword" in query.lower()
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Your plugin logic
        return {"success": True, "result": "..."}
```

Place in `kali_orchestrator/plugins/` and it will be auto-loaded.

## Reporting

Generate reports in multiple formats:

```bash
# Markdown (default)
kali-orchestrator report

# HTML
kali-orchestrator report --format html

# PDF
kali-orchestrator report --format pdf --output report.pdf
```

Reports include:
- Executive summary with risk ratings
- Detailed findings with evidence
- Recommendations
- Tool execution logs
- Bug bounty templates (HackerOne-style)

## Testing

Run the test suite:

```bash
pytest tests/
```

Tests cover:
- Scope enforcement
- Memory persistence
- Confirmation prompts
- Tool chaining
- LLM fallback behavior

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License

## Disclaimer

This tool is for authorized security testing only. Users are responsible for ensuring they have proper authorization before testing any systems. The authors are not responsible for any misuse of this software.

