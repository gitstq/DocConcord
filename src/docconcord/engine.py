"""Orchestration: discover -> parse -> choose base -> run rules -> report."""

from __future__ import annotations

import os
from typing import Optional

from .config import load_config
from .i18n import choose_base, discover_documents
from .model import Report
from .parser import parse_document
from .rules import run_rules


def load_workspace(root: str, config: dict) -> Report:
    """Build a fully populated :class:`Report` for *root*."""
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise NotADirectoryError(f"目录不存在: {root}")

    items = discover_documents(root)
    by_family: dict = {}
    for item in items:
        by_family.setdefault(item[3], []).append(item)

    aliases = {str(k).lower(): str(v) for k, v in (config.get("aliases") or {}).items()}
    max_bytes = int(config.get("max_file_bytes") or 2_000_000)

    report = Report(
        root=root,
        base=str(config.get("base") or ""),
        families={f: [it[1] for it in sorted(arr, key=lambda x: x[1])]
                  for f, arr in sorted(by_family.items())},
        aliases=aliases,
        online=bool(config.get("online")),
        disabled_rules=list(config.get("disabled_rules") or []),
    )

    actual_bases = []
    for fam, arr in sorted(by_family.items()):
        # Skip oversized files rather than silently reading unbounded input.
        usable = [it for it in arr if os.path.getsize(it[0]) <= max_bytes]
        if len(usable) < 2:
            continue
        base_idx = choose_base(usable, str(config.get("base") or ""))
        for idx, (path, rel, lang, family) in enumerate(usable):
            doc = parse_document(path, rel, lang, family, aliases)
            doc.is_base = idx == base_idx
            report.documents.append(doc)
            if doc.is_base:
                actual_bases.append(rel)

    report.base = str(config.get("base") or "") or ", ".join(sorted(actual_bases)) or "(auto)"
    report.findings = run_rules(report)
    return report


def audit(
    root: str = ".",
    base: Optional[str] = None,
    format: Optional[str] = None,
    fail_on: Optional[str] = None,
    online: Optional[bool] = None,
    aliases: Optional[dict] = None,
    disabled_rules: Optional[list] = None,
) -> Report:
    """Convenience API mirroring the CLI flags."""
    cfg = load_config(os.path.abspath(root), {
        "base": base, "format": format, "fail_on": fail_on, "online": online,
        "aliases": aliases, "disabled_rules": disabled_rules,
    })
    return load_workspace(root, cfg)
