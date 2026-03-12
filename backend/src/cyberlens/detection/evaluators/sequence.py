# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis

from cyberlens.detection.evaluators.base import BaseEvaluator, DetectionEvaluation
from cyberlens.detection.models import DetectionRule


class SequenceEvaluator(BaseEvaluator):
    rule_type = "sequence"

    async def evaluate(
        self,
        redis: Redis,
        event: dict[str, Any],
        rule: DetectionRule,
    ) -> DetectionEvaluation:
        detection = rule.rule_definition.get("detection", {})
        steps = detection.get("steps", [])
        sequence = detection.get("sequence", {})
        timeframe = int(sequence.get("timeframe", 1800))
        group_by = sequence.get("group_by", "source_ip")
        group_value = str(event.get(group_by) or "global")
        state_key = f"rule:{rule.rule_id}:sequence:{group_value}"

        current_index_raw = await redis.get(state_key)
        current_index = int(current_index_raw or 0)

        if current_index >= len(steps):
            current_index = 0

        expected_step = steps[current_index] if steps else None
        first_step = steps[0] if steps else None

        if expected_step and self.filter_matches(event, expected_step):
            current_index += 1
            await redis.set(state_key, str(current_index), ex=timeframe)
        elif first_step and self.filter_matches(event, first_step):
            current_index = 1
            await redis.set(state_key, str(current_index), ex=timeframe)
        else:
            return DetectionEvaluation(matched=False, group_value=group_value)

        if current_index < len(steps):
            return DetectionEvaluation(matched=False, group_value=group_value)

        dedup_key = f"alert:dedup:{rule.rule_id}:{group_value}"
        if await redis.exists(dedup_key):
            return DetectionEvaluation(matched=False, group_value=group_value)

        await redis.delete(state_key)
        await redis.set(dedup_key, "1", ex=300)
        return DetectionEvaluation(
            matched=True,
            group_value=group_value,
            matched_events=[{"id": event.get("id"), "event_type": event.get("event_type")}],
        )
