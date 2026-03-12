# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

"""Log parsers for raw event sources."""

from __future__ import annotations

from cyberlens.ingestion.parsers.base import BaseParser
from cyberlens.ingestion.parsers.firewall import FirewallParser
from cyberlens.ingestion.parsers.generic_text import GenericTextParser
from cyberlens.ingestion.parsers.json_generic import JsonGenericParser
from cyberlens.ingestion.parsers.netflow import NetflowParser
from cyberlens.ingestion.parsers.syslog import SyslogParser
from cyberlens.ingestion.parsers.windows_event import WindowsEventParser


class ParserRegistry:
    def __init__(self, parsers: list[BaseParser]) -> None:
        self.parsers = parsers

    def detect(self, raw_log: str, source_type: str | None = None) -> BaseParser:
        for parser in self.parsers:
            if parser.can_parse(raw_log, source_type):
                return parser
        return GenericTextParser()


def get_default_parser_registry() -> ParserRegistry:
    return ParserRegistry(
        parsers=[
            WindowsEventParser(),
            FirewallParser(),
            NetflowParser(),
            SyslogParser(),
            JsonGenericParser(),
            GenericTextParser(),
        ]
    )


__all__ = ["ParserRegistry", "get_default_parser_registry"]
