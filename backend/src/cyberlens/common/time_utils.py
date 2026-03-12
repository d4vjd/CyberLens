# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)