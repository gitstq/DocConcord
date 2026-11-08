"""Conservative, reviewable auto-fixes.

DocConcord is read-only by default. ``fix`` produces unified diffs; only
``fix --apply`` writes, and it only ever performs two safe edits:

1. insert a language-switch navigation line when it is missing;
2. add a language tag to an untagged fenced code block.

It never deletes content, never reformats prose and never touches links.
"""

from __future__ import annotations

import difflib
import os
from dataclasses import dataclass, field
from typing import List

from .model import Report
from .rules import families

_LANG_LABEL = {
    "en": "English", "zh-CN": "简体中文", "zh-TW": "繁體中文", "und": "Default",
    "ja": "日本語", "ko": "한국어", "fr": "Français", "de": "Deutsch",
    "es": "Español", "ru": "Русский", "pt": "Português", "pt-BR": "Português (BR)",
}


@dataclass
class Fix:
    relpath: str
    description: str
    diff: str
    new_lines: List[str] = field(default_factory=list)


def _has_nav(lines: List[str], siblings: List[str]) -> bool:
    head = "\n".join(lines[:15])
    return sum(1 for s in siblings if s in head) >= max(1, len(siblings) - 1)


def _guess_lang(text: str) -> str:
    commandish = ("pip ", "git ", "npm ", "python ", "make ", "$ ", "curl ", "apt ")
    return "bash" if any(c in text for c in commandish) else "text"


def _diff(original: List[str], new: List[str], rel: str) -> str:
    return "\n".join(difflib.unified_diff(
        original, new, fromfile=rel, tofile=rel, lineterm="",
    ))


def generate_fixes(report: Report) -> List[Fix]:
    """Compute (but do not write) the set of safe fixes for this report."""
    fixes: List[Fix] = []
    siblings_by_family = {
        fam: [d.relpath for d in report.documents if d.family == fam]
        for fam in report.families
    }

    for doc in report.documents:
        original = list(doc.lines)
        new = list(original)
        descriptions: List[str] = []

        # Code-fence edits use original 1-based line numbers, so they must run
        # BEFORE any insertion shifts the line array. Walk bottom-up.
        for cb in sorted(doc.code_blocks, key=lambda b: b.line, reverse=True):
            if cb.lang:
                continue
            fence_idx = cb.line - 1
            if fence_idx >= len(new):
                continue
            raw = new[fence_idx]
            stripped = raw.lstrip()
            if not (stripped.startswith("```") or stripped.startswith("~~~")):
                continue
            indent = raw[: len(raw) - len(stripped)]
            marker = stripped[:3]
            lang = _guess_lang(cb.text)
            new[fence_idx] = f"{indent}{marker}{lang}"
            descriptions.append("为未标注代码块补充语言标记")

        siblings = sorted(siblings_by_family.get(doc.family, []))
        if len(siblings) >= 2 and not _has_nav(original, siblings):
            parts = []
            for d in report.documents:
                if d.family == doc.family:
                    label = _LANG_LABEL.get(d.lang, d.lang)
                    parts.append(f"[{label}]({os.path.basename(d.relpath)})")
            nav = "> 🌐 " + " · ".join(parts)
            insert_at = 0
            for idx, line in enumerate(original):
                if line.lstrip().startswith("# "):
                    insert_at = idx + 1
                    break
            new.insert(insert_at, "")
            new.insert(insert_at + 1, nav)
            descriptions.append("补充语言切换导航")

        if descriptions and new != original:
            fixes.append(Fix(
                relpath=doc.relpath,
                description="；".join(descriptions),
                diff=_diff(original, new, doc.relpath),
                new_lines=new,
            ))
    return fixes


def apply_fixes(root: str, fixes: List[Fix]) -> int:
    """Write the computed fixes. Returns the number of files changed."""
    for fix in fixes:
        target = os.path.join(root, fix.relpath)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(fix.new_lines) + "\n")
    return len(fixes)
