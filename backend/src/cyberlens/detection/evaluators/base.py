# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from redis.asyncio import Redis

from cyberlens.detection.models import DetectionRule


@dataclass(slots=True)
class DetectionEvaluation:
    matched: bool
    group_value: str | None = None
    matched_events: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseEvaluator(ABC):
    rule_type = "base"

    @abstractmethod
    async def evaluate(
        self,
        redis: Redis,
        event: dict[str, Any],
        rule: DetectionRule,
    ) -> DetectionEvaluation:
        raise NotImplementedError

    def filter_matches(self, event: dict[str, Any], expected: dict[str, Any]) -> bool:
        for key, expected_value in expected.items():
            actual = event.get(key)
            if actual is None:
                return False
            if str(actual).lower() != str(expected_value).lower():
                return False
        return True
