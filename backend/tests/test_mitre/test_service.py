# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from cyberlens.mitre.service import MitreAttackService


def test_mitre_bundle_loads_seed_subset() -> None:
    service = MitreAttackService()
    service.load_bundle()

    assert service.technique_count >= 9
    assert "T1110.001" in service.techniques