# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    parser_name = "generic"

    @abstractmethod
    def can_parse(self, raw_log: str, source_type: str | None = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw_log: str) -> dict[str, Any]:
        raise NotImplementedError