# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from cyberlens.config import get_settings
from cyberlens.detection.models import DetectionRule, RuleType
from cyberlens.detection.schemas import RuleSyncResponse
from cyberlens.ingestion.models import SeverityLevel


class RuleLoader:
    def __init__(self, rules_dir: Path | None = None) -> None:
        settings = get_settings()
        self.rules_dir = rules_dir or settings.resolved_rules_path

    def load_rule_files(self) -> list[dict[str, Any]]:
        rules: list[dict[str, Any]] = []
        if not self.rules_dir.exists():
            return rules

        for file_path in sorted(self.rules_dir.glob("*.yml")):
            with file_path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
            payload["_file_path"] = str(file_path)
            rules.append(payload)
        return rules

    def parse_rule_yaml(self, yaml_content: str) -> dict[str, Any]:
        payload = yaml.safe_load(yaml_content) or {}
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Rule YAML must deserialize into an object.")
        return self.normalize_rule_payload(payload)

    def normalize_rule_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ("id", "title", "severity", "type", "detection")
        missing = [field for field in required if field not in payload]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Rule YAML is missing required fields: {', '.join(missing)}.",
            )

        try:
            SeverityLevel(str(payload["severity"]))
            RuleType(str(payload["type"]))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        normalized = dict(payload)
        normalized["id"] = str(payload["id"])
        normalized["title"] = str(payload["title"])
        normalized["severity"] = str(payload["severity"])
        normalized["type"] = str(payload["type"])
        normalized["detection"] = payload.get("detection") or {}
        return normalized

    def dump_rule_yaml(self, payload: dict[str, Any]) -> str:
        clean_payload = {key: value for key, value in payload.items() if not key.startswith("_")}
        return yaml.safe_dump(clean_payload, sort_keys=False, allow_unicode=False)

    def resolve_rule_file_path(self, payload: dict[str, Any], existing: DetectionRule | None = None) -> Path:
        existing_path = None
        if existing is not None:
            existing_path = (existing.rule_definition or {}).get("_file_path")
        if existing_path:
            return Path(str(existing_path))
        return self.rules_dir / f"{payload['id']}.yml"

    def save_rule_file(self, payload: dict[str, Any], existing: DetectionRule | None = None) -> Path:
        file_path = self.resolve_rule_file_path(payload, existing)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.dump_rule_yaml(payload), encoding="utf-8")
        return file_path

    def delete_rule_file(self, rule: DetectionRule) -> Path:
        file_path = self.resolve_rule_file_path(rule.rule_definition or {"id": rule.rule_id}, existing=rule)
        if file_path.exists():
            file_path.unlink()
        return file_path

    async def sync_to_database(self, session: AsyncSession) -> RuleSyncResponse:
        loaded_rule_ids: list[str] = []

        for payload in self.load_rule_files():
            rule_id = str(payload["id"])
            existing = await session.scalar(
                select(DetectionRule).where(DetectionRule.rule_id == rule_id)
            )

            values = {
                "title": payload["title"],
                "description": payload.get("description"),
                "severity": SeverityLevel(payload["severity"]),
                "rule_type": RuleType(payload["type"]),
                "rule_definition": payload,
                "mitre_tactic": (payload.get("mitre") or {}).get("tactic"),
                "mitre_technique_id": (payload.get("mitre") or {}).get("technique_id"),
                "enabled": bool(payload.get("enabled", True)),
            }

            if existing is None:
                session.add(DetectionRule(rule_id=rule_id, **values))
            else:
                for key, value in values.items():
                    setattr(existing, key, value)
            loaded_rule_ids.append(rule_id)

        await session.commit()
        return RuleSyncResponse(
            loaded_count=len(loaded_rule_ids),
            loaded_rule_ids=loaded_rule_ids,
        )