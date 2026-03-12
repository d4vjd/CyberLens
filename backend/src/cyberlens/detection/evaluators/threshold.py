# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis

from cyberlens.detection.evaluators.base import BaseEvaluator, DetectionEvaluation
from cyberlens.detection.models import DetectionRule


class ThresholdEvaluator(BaseEvaluator):
    rule_type = "threshold"

    async def evaluate(
        self,
        redis: Redis,
        event: dict[str, Any],
        rule: DetectionRule,
    ) -> DetectionEvaluation:
        detection = rule.rule_definition.get("detection", {})
        filter_config = detection.get("filter", {})
        threshold = detection.get("threshold", {})

        if not self.filter_matches(event, filter_config):
            return DetectionEvaluation(matched=False)

        group_by = threshold.get("group_by", "source_ip")
        group_value = str(event.get(group_by) or "global")
        timeframe = int(threshold.get("timeframe", 300))
        required_count = int(threshold.get("count", 1))
        counter_key = f"rule:{rule.rule_id}:counter:{group_value}"

        count = await redis.incr(counter_key)
        if count == 1:
            await redis.expire(counter_key, timeframe)

        if count < required_count:
            return DetectionEvaluation(matched=False, group_value=group_value)

        dedup_key = f"alert:dedup:{rule.rule_id}:{group_value}"
        if await redis.exists(dedup_key):
            return DetectionEvaluation(matched=False, group_value=group_value)

        await redis.set(dedup_key, "1", ex=300)
        return DetectionEvaluation(
            matched=True,
            group_value=group_value,
            matched_events=[self._event_summary(event)],
            metadata={"count": count, "timeframe": timeframe},
        )

    def _event_summary(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": event.get("id"),
            "timestamp": event.get("timestamp"),
            "source_ip": event.get("source_ip"),
            "dest_ip": event.get("dest_ip"),
            "action": event.get("action"),
            "event_type": event.get("event_type"),
        }
