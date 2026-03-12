# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from cyberlens.db.base import Base
from cyberlens.db.session import SessionLocal


def test_session_import_registers_foreign_key_targets() -> None:
    assert SessionLocal is not None

    alerts_table = Base.metadata.tables["alerts"]
    case_foreign_key = next(
        foreign_key
        for foreign_key in alerts_table.c.case_id.foreign_keys
        if foreign_key.target_fullname == "cases.id"
    )

    assert case_foreign_key.column.table.name == "cases"
