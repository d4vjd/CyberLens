# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis

from cyberlens.detection.evaluators.base import BaseEvaluator, DetectionEvaluation
from cyberlens.detection.models import DetectionRule


class PatternEvaluator(BaseEvaluator):
    rule_type = "pattern"

    async def evaluate(
        self,
        redis: Redis,
        event: dict[str, Any],
        rule: DetectionRule,
    ) -> DetectionEvaluation:
        del redis

        detection = rule.rule_definition.get("detection", {})
        filter_config = detection.get("filter", {})
        pattern = detection.get("pattern", {})

        if not self.filter_matches(event, filter_config):
            return DetectionEvaluation(matched=False)

        field_name = pattern.get("field", "message")
        contains = str(pattern.get("contains", "")).lower()
        haystack = str(event.get(field_name) or "").lower()

        if not contains or contains not in haystack:
            return DetectionEvaluation(matched=False)

        return DetectionEvaluation(
            matched=True,
            group_value=str(event.get("source_ip") or event.get("username") or "global"),
            matched_events=[self._event_summary(event)],
        )

    def _event_summary(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": event.get("id"),
            "timestamp": event.get("timestamp"),
            "message": event.get("message"),
            "event_type": event.get("event_type"),
        }
