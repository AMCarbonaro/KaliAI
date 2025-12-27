# Multi-stage Dockerfile for Kali AI Orchestrator
# Based on kali-rolling

FROM kalilinux/kali-rolling:latest AS base

# Install system dependencies and Kali tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install hexstrike-ai and gemini-cli (Kali packages)
FROM base AS kali-tools

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    hexstrike-ai \
    gemini-cli \
    nmap \
    metasploit-framework \
    nikto \
    nuclei \
    sqlmap \
    burpsuite \
    || echo "Warning: Some packages may not be available in this Kali version" && \
    rm -rf /var/lib/apt/lists/*

# Final stage - build everything in one stage for simplicity
FROM kali-tools AS final

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY kali_orchestrator/ ./kali_orchestrator/

# Create virtual environment and install dependencies
# This avoids the externally-managed-environment error (PEP 668)
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /app/venv/bin/pip install --no-cache-dir -e . && \
    rm -rf /var/lib/apt/lists/*

# Set PATH to use venv Python
ENV PATH="/app/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 orchestrator && \
    mkdir -p /home/orchestrator/.kali-orchestrator/{memory,logs,reports} && \
    chown -R orchestrator:orchestrator /home/orchestrator/.kali-orchestrator && \
    chown -R orchestrator:orchestrator /app

# Set working directory
WORKDIR /app

# Switch to non-root user
USER orchestrator

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV KALI_ORCHESTRATOR_HOME=/home/orchestrator/.kali-orchestrator

# Expose web port
EXPOSE 7860

# Default command - run web app
CMD ["python", "-m", "kali_orchestrator.web_app"]

