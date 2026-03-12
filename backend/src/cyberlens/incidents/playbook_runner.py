# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from cyberlens.config import get_settings

PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_.]+)\s*}}")


class PlaybookRunner:
    def __init__(self, playbooks_dir: Path | None = None) -> None:
        self.playbooks_dir = playbooks_dir or get_settings().resolved_playbooks_path

    def load_playbook(self, playbook_id: str) -> dict[str, Any]:
        file_path = self.playbooks_dir / f"{playbook_id}.yml"
        if not file_path.exists():
            raise FileNotFoundError(f"Playbook '{playbook_id}' was not found")

        with file_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def render_target(self, value: str, context: dict[str, Any]) -> str:
        def replace(match: re.Match[str]) -> str:
            path = match.group(1).split(".")
            current: Any = context
            for segment in path:
                if isinstance(current, dict):
                    current = current.get(segment)
                else:
                    current = getattr(current, segment, None)
                if current is None:
                    return ""
            return str(current)

        return PLACEHOLDER_PATTERN.sub(replace, value)
