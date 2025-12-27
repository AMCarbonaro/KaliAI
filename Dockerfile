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

# Python dependencies stage
FROM kali-tools AS python-deps

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -e .

# Final stage
FROM python-deps AS final

# Create non-root user
RUN useradd -m -u 1000 orchestrator && \
    mkdir -p /home/orchestrator/.kali-orchestrator/{memory,logs,reports} && \
    chown -R orchestrator:orchestrator /home/orchestrator/.kali-orchestrator

# Copy application code
COPY --chown=orchestrator:orchestrator . /app

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
CMD ["python3", "-m", "kali_orchestrator.web_app"]

