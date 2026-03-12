# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseResponseAction(ABC):
    action_type = "base"

    @abstractmethod
    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
