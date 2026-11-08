"""Shared helpers for rule modules (kept separate to avoid circular imports)."""

from __future__ import annotations

from typing import Iterator, Tuple

from ..model import Document, Report


def families(report: Report) -> Iterator[Tuple[str, Document, list]]:
    """Yield ``(family, base_document, [other_documents])`` triples."""
    for fam in sorted(report.families):
        docs = [d for d in report.documents if d.family == fam]
        base = next((d for d in docs if d.is_base), None)
        others = [d for d in docs if not d.is_base]
        if base is not None and others:
            yield fam, base, others
