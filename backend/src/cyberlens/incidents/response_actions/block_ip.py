# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import Any

from cyberlens.incidents.response_actions.base import BaseResponseAction


class BlockIpAction(BaseResponseAction):
    action_type = "block_ip"

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "simulated", "action": self.action_type, "payload": payload}
