"""Agent personas for different pentesting scenarios."""

import yaml
from pathlib import Path
from typing import Dict, Optional


def load_persona(persona_name: str) -> Optional[Dict]:
    """Load a persona configuration.

    Args:
        persona_name: Name of the persona (without .yaml extension)

    Returns:
        Persona configuration dictionary or None
    """
    # Try multiple locations
    possible_paths = [
        Path(__file__).parent / f"{persona_name}.yaml",
        Path(f"kali_orchestrator/personas/{persona_name}.yaml"),
        Path(f"personas/{persona_name}.yaml"),
    ]

    for path in possible_paths:
        if path.exists():
            with open(path, "r") as f:
                return yaml.safe_load(f)

    return None


def list_personas() -> list[str]:
    """List available personas.

    Returns:
        List of persona names
    """
    personas_dir = Path(__file__).parent
    personas = []
    for yaml_file in personas_dir.glob("*.yaml"):
        personas.append(yaml_file.stem)
    return personas
