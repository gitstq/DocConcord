"""Pure-stdlib data model shared by the parser, rules engine and reporters.

Nothing in this module imports anything outside the standard library, and no
object here performs I/O. Keeping the model inert makes every rule trivially
testable and the whole engine deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

SEVERITY_ORDER: Dict[str, int] = {"info": 0, "warning": 1, "error": 2}
SEVERITIES = ("info", "warning", "error")


@dataclass(frozen=True)
class Block:
    """A top-level Markdown block.

    kind: heading | code | table | paragraph | list | quote | hr | html
    """

    kind: str
    line: int                 # 1-based first line
    end_line: int             # 1-based last line (inclusive)
    text: str = ""
    level: int = 0            # heading level 1..6
    lang: str = ""            # fenced code info string, lower-cased
    rows: int = 0             # table body rows
    cols: int = 0             # table column count


@dataclass(frozen=True)
class Link:
    target: str
    line: int
    kind: str                 # inline | reference | autolink | bare | image
    text: str = ""


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    norm: str                 # normalized form used for cross-language matching
    slug: str                 # GitHub-style anchor
    line: int


@dataclass(frozen=True)
class Command:
    line: int
    text: str
    lang: str


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    file: str = ""
    line: int = 0
    lang: str = ""
    suggestion: str = ""

    def as_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "lang": self.lang,
            "suggestion": self.suggestion,
        }


@dataclass
class Document:
    path: str
    relpath: str
    lang: str
    family: str
    is_base: bool = False
    lines: List[str] = field(default_factory=list)
    blocks: List[Block] = field(default_factory=list)
    headings: List[Heading] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    code_blocks: List[Block] = field(default_factory=list)
    tables: List[Block] = field(default_factory=list)
    commands: List[Command] = field(default_factory=list)
    anchors: Set[str] = field(default_factory=set)
    external_links: Set[str] = field(default_factory=set)
    local_links: Set[str] = field(default_factory=set)


@dataclass
class Report:
    root: str
    base: str
    documents: List[Document] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    families: Dict[str, List[str]] = field(default_factory=dict)
    aliases: Dict[str, str] = field(default_factory=dict)
    online: bool = False
    disabled_rules: List[str] = field(default_factory=list)

    def count(self, severity: str) -> int:
        return sum(1 for f in self.findings if f.severity == severity)

    @property
    def parity_score(self) -> int:
        """0..100 structural parity score across all non-base documents."""
        others = [d for d in self.documents if not d.is_base]
        if not others:
            return 100
        total = max(1, len(others) * 8)
        penalty = 0.0
        for f in self.findings:
            if f.severity == "error":
                penalty += 1.0
            elif f.severity == "warning":
                penalty += 0.35
        return max(0, int(round(100 * (1 - min(1.0, penalty / total)))))

    def as_dict(self) -> dict:
        return {
            "tool": "DocConcord",
            "version": "1.0.0",
            "root": self.root,
            "base": self.base,
            "online": self.online,
            "summary": {
                "documents": len(self.documents),
                "families": len(self.families),
                "findings": len(self.findings),
                "errors": self.count("error"),
                "warnings": self.count("warning"),
                "infos": self.count("info"),
                "parity_score": self.parity_score,
            },
            "families": self.families,
            "documents": [
                {
                    "file": d.relpath,
                    "lang": d.lang,
                    "family": d.family,
                    "is_base": d.is_base,
                    "headings": len(d.headings),
                    "code_blocks": len(d.code_blocks),
                    "tables": len(d.tables),
                    "commands": len(d.commands),
                    "links": len(d.links),
                }
                for d in self.documents
            ],
            "findings": [f.as_dict() for f in self.findings],
        }
