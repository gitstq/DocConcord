"""Language detection, document-family grouping and heading normalization.

DocConcord never tries to *translate* anything. It aligns translated documents
structurally: by heading ordinal and, when supplied, by a user-provided alias
table that maps localized headings onto one canonical key.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Dict, Iterable, List, Tuple

# Language tag on a filename: README.zh-CN.md, guide_en_US.markdown, docs.ja.md
_LANG_SUFFIX = re.compile(
    r"^(?P<stem>.+?)[._-](?P<lang>[A-Za-z]{2}(?:[-_][A-Za-z]{2,4})?)$"
)

_LANG_ALIASES: Dict[str, str] = {
    "zh": "zh-CN", "zh-cn": "zh-CN", "zh-hans": "zh-CN", "cn": "zh-CN",
    "zh-tw": "zh-TW", "zh-hk": "zh-TW", "zh-hant": "zh-TW", "tw": "zh-TW",
    "en": "en", "en-us": "en", "en-gb": "en",
    "ja": "ja", "ja-jp": "ja", "ko": "ko", "ko-kr": "ko",
    "fr": "fr", "de": "de", "es": "es", "ru": "ru", "pt": "pt", "pt-br": "pt-BR",
}

_LANG_PRIORITY = ("en", "zh-CN", "zh-TW", "ja", "ko", "fr", "de", "es", "ru", "pt", "pt-BR")

_SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache", "site-packages",
    "vendor", "target", ".idea", ".vscode",
}

_ORDINAL = re.compile(
    r"^\s*(?:\d{1,2}\s*[.、)）]|[①-⑳]|[-*•·]|\(?(?:[a-z]|\d)\)?\.)\s+", re.IGNORECASE
)
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HTML_TAG = re.compile(r"<[^>]+>")


def canonical_language(tag: str) -> str:
    """Normalize a language tag, e.g. ``zh_hans`` -> ``zh-CN``."""
    if not tag:
        return "und"
    key = tag.strip().lower().replace("_", "-")
    return _LANG_ALIASES.get(key, tag.strip())


def detect_language(filename: str) -> Tuple[str, str]:
    """Return ``(canonical_lang, stem)`` for a Markdown filename.

    ``README.md`` -> ``("und", "README")``; ``README.zh-CN.md`` ->
    ``("zh-CN", "README")``.
    """
    base = os.path.basename(filename)
    stem, _ext = os.path.splitext(base)
    m = _LANG_SUFFIX.match(stem)
    if m:
        raw = m.group("lang")
        # Only treat it as a language tag if it looks like one we know, or a
        # plausible 2-letter tag. This avoids splitting "getting-started".
        key = raw.lower().replace("_", "-")
        if key in _LANG_ALIASES or re.fullmatch(r"[a-z]{2}(?:-[a-z]{2,4})?", key):
            return canonical_language(raw), m.group("stem")
    return "und", stem


def _strip_symbols(text: str) -> str:
    """Drop punctuation/symbols/emoji, keep letters, digits, CJK and spacing."""
    out: List[str] = []
    for ch in text:
        if ch in "-_":
            out.append(" ")
            continue
        cat = unicodedata.category(ch)
        # Punctuation / symbols / emoji become whitespace rather than being
        # deleted, so adjacent words never get glued together ("项目介绍：核心"
        # -> "项目介绍 核心").
        if cat.startswith(("P", "S", "M", "C", "Z")) or ch.isspace():
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def normalize_heading(text: str, aliases: Dict[str, str] | None = None) -> str:
    """Normalize a heading for cross-language matching.

    Removes ordinals, emoji, Markdown emphasis and punctuation, lower-cases and
    collapses whitespace. An optional alias table maps localized forms onto one
    canonical key, which is the recommended way to align semantically equal
    headings written in different languages.
    """
    s = _HTML_TAG.sub(" ", text)
    s = _MD_LINK.sub(r"\1", s)
    s = re.sub(r"[*_`~]", "", s)
    s = _ORDINAL.sub("", s.strip())
    s = _strip_symbols(s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    aliases = aliases or {}
    # Exact match first, then lower-cased key match.
    return aliases.get(s, aliases.get(text.strip().lower(), s))


def slugify(text: str, seen: Dict[str, int]) -> str:
    """GitHub-flavored anchor slug generator with duplicate suffixes."""
    s = _HTML_TAG.sub("", text.strip().lower())
    s = re.sub(r"[*_`~]", "", s)
    chars: List[str] = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_"):
            chars.append(ch)
        elif ch.isspace() or unicodedata.category(ch).startswith("Z"):
            chars.append(" ")
        elif unicodedata.category(ch).startswith(("P", "S", "M", "C")):
            continue
        else:
            chars.append(ch)
    slug = re.sub(r"\s+", "-", "".join(chars).strip())
    slug = re.sub(r"-{2,}", "-", slug).strip("-") or "section"
    n = seen.get(slug, 0)
    seen[slug] = n + 1
    return slug if n == 0 else f"{slug}-{n}"


def _iter_markdown(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if name.lower().endswith((".md", ".markdown")):
                yield os.path.join(dirpath, name)


def discover_documents(root: str) -> List[Tuple[str, str, str, str]]:
    """Find Markdown document families under *root*.

    Returns a list of ``(abs_path, relpath, lang, family)``. A family is the
    directory plus the language-stripped stem, e.g. all ``README*.md`` files in
    the repo root belong to family ``README``.
    """
    found: List[Tuple[str, str, str, str]] = []
    for path in _iter_markdown(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        lang, stem = detect_language(path)
        family = (os.path.dirname(rel) + "/" if os.path.dirname(rel) else "") + stem
        found.append((path, rel, lang, family))

    # Keep only families with at least two translated variants. A lone
    # README.md has nothing to be checked against, so it is not a family.
    by_family: Dict[str, List[Tuple[str, str, str, str]]] = {}
    for item in found:
        by_family.setdefault(item[3], []).append(item)
    result = [i for items in by_family.values() if len(items) >= 2 for i in items]
    return sorted(result, key=lambda i: (i[3], i[2], i[1]))


def choose_base(items: List[Tuple[str, str, str, str]], hint: str = "") -> int:
    """Pick the index of the base document inside one family."""
    if hint:
        for idx, item in enumerate(items):
            if item[1] == hint or os.path.basename(item[1]) == hint:
                return idx
    # Prefer the untagged canonical file (README.md), then English.
    for idx, item in enumerate(items):
        if item[2] == "und":
            return idx
    for tag in _LANG_PRIORITY:
        for idx, item in enumerate(items):
            if item[2] == tag:
                return idx
    return 0
