# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from enum import Enum as PyEnum
from typing import TypeVar

from sqlalchemy import Enum

EnumType = TypeVar("EnumType", bound=PyEnum)


def enum_column(enum_cls: type[EnumType]) -> Enum:
    return Enum(
        enum_cls,
        values_callable=lambda members: [member.value for member in members],
        native_enum=True,
    )