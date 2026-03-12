# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from pathlib import Path

from cyberlens.detection.rule_loader import RuleLoader


def test_rule_loader_reads_seed_rules() -> None:
    rules_dir = Path(__file__).resolve().parents[3] / "rules"
    loader = RuleLoader(rules_dir=rules_dir)

    rules = loader.load_rule_files()

    assert len(rules) == 9
    assert any(rule["id"] == "brute_force_ssh" for rule in rules)
