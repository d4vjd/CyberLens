# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis

from cyberlens.detection.evaluators.base import BaseEvaluator, DetectionEvaluation
from cyberlens.detection.models import DetectionRule


class AggregationEvaluator(BaseEvaluator):
    rule_type = "aggregation"

    async def evaluate(
        self,
        redis: Redis,
        event: dict[str, Any],
        rule: DetectionRule,
    ) -> DetectionEvaluation:
        detection = rule.rule_definition.get("detection", {})
        filter_config = detection.get("filter", {})
        aggregation = detection.get("aggregation", {})

        if not self.filter_matches(event, filter_config):
            return DetectionEvaluation(matched=False)

        group_by = aggregation.get("group_by", "source_ip")
        distinct_field = aggregation.get("distinct_field", "dest_port")
        min_distinct = int(aggregation.get("min_distinct", 1))
        timeframe = int(aggregation.get("timeframe", 300))
        group_value = str(event.get(group_by) or "global")
        distinct_value = event.get(distinct_field)
        if distinct_value is None:
            return DetectionEvaluation(matched=False, group_value=group_value)

        key = f"rule:{rule.rule_id}:hll:{group_value}"
        await redis.pfadd(key, str(distinct_value))
        await redis.expire(key, timeframe)
        distinct_count = int(await redis.pfcount(key))

        if distinct_count < min_distinct:
            return DetectionEvaluation(matched=False, group_value=group_value)

        dedup_key = f"alert:dedup:{rule.rule_id}:{group_value}"
        if await redis.exists(dedup_key):
            return DetectionEvaluation(matched=False, group_value=group_value)

        await redis.set(dedup_key, "1", ex=300)
        return DetectionEvaluation(
            matched=True,
            group_value=group_value,
            matched_events=[
                {
                    "id": event.get("id"),
                    "event_type": event.get("event_type"),
                    "distinct_count": distinct_count,
                }
            ],
            metadata={"distinct_count": distinct_count},
        )