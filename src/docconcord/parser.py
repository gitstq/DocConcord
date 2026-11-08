"""A small, dependency-free Markdown block/link parser.

This is intentionally *not* a full CommonMark implementation. DocConcord only
needs a stable, deterministic view of the handful of constructs that matter for
cross-language parity: ATX/Setext headings, fenced code blocks, pipe tables,
links/anchors and shell commands inside code fences. Everything is read-only.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Set

from .i18n import normalize_heading, slugify
from .model import Block, Command, Document, Heading, Link

_FENCE = re.compile(r"^\s{0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})[ \t]+(?P<text>.+?)\s*#*\s*$")
_SETEXT = re.compile(r"^\s{0,3}(?P<mark>=+|-+)\s*$")
_TABLE_SEP = re.compile(
    r"^\s*\|?\s*:?-{1,}:?\s*(?:\|\s*:?-{1,}:?\s*)*\|?\s*$"
)
_HTML_COMMENT_OPEN = re.compile(r"<!--")
_INLINE_LINK = re.compile(
    r"(!?)\[([^\]]*)\]\(\s*(?:<([^>]*)>|([^)\s]+))(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
_REF_DEF = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(\S+)")
_REF_USE = re.compile(r"\[([^\]]*)\]\[([^\]]*)\]")
_AUTOLINK = re.compile(r"<((?:https?://|mailto:)[^>\s]+)>")
_BARE_URL = re.compile(r"(?<![\(\"'=<])\bhttps?://[^\s<>\"')]+")
_HTML_ID = re.compile(r"<a\s+[^>]*(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
_INLINE_CODE = re.compile(r"`[^`]*`")

SHELL_LANGS = {
    "bash", "sh", "shell", "zsh", "fish", "console", "terminal",
    "powershell", "ps1", "pwsh", "cmd", "bat", "dos",
}
_COMMAND_START = re.compile(
    r"^(?:sudo\s+)?(?:[A-Za-z_][\w.-]*=[\w./:-]*\s+)?"
    r"(?:git|pip|pip3|python|python3|node|npm|pnpm|yarn|make|cmake|go|cargo|"
    r"docker|kubectl|curl|wget|ls|cd|cp|mv|rm|mkdir|touch|cat|echo|export|"
    r"chmod|chown|tar|unzip|zip|grep|sed|awk|find|brew|apt|yum|dnf|uv|"
    r"pytest|tox|java|mvn|gradle|dotnet|ruby|gem|php|composer|sh|bash|\./|"
    r"~?/|\$|\.|source|set|env|which|command|npx)\b|"
    r"^(?:[A-Za-z_][\w]*\s*=\s*\S|export\s+\w+=|#!)",
    re.IGNORECASE,
)
_PROMPT = re.compile(r"^\s*(?:\$\s?|>\s?|PS>\s?|#\s?)+")


def _strip_code_spans(line: str) -> str:
    return _INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)


def _table_cols(line: str) -> int:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return len([c for c in s.split("|")])


def _is_pipe_row(line: str) -> bool:
    return "|" in line and not _FENCE.match(line)


def read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        return fh.read().splitlines()


def parse_document(
    path: str,
    relpath: str,
    lang: str,
    family: str,
    aliases: Dict[str, str] | None = None,
) -> Document:
    """Parse one Markdown file into a :class:`Document`."""
    lines = read_lines(path)
    doc = Document(path=path, relpath=relpath, lang=lang, family=family, lines=lines)
    aliases = aliases or {}
    seen: Dict[str, int] = {}
    ref_defs: Dict[str, str] = {}

    # First pass: collect reference-style link definitions.
    in_comment = False
    for line in lines:
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if _HTML_COMMENT_OPEN.search(line) and "-->" not in line:
            in_comment = True
            continue
        m = _REF_DEF.match(line)
        if m:
            ref_defs[m.group(1).strip().lower()] = m.group(2).strip()

    i = 0
    n = len(lines)
    in_comment = False
    while i < n:
        line = lines[i]

        if in_comment:
            if "-->" in line:
                in_comment = False
            i += 1
            continue
        if _HTML_COMMENT_OPEN.search(line) and "-->" not in line:
            in_comment = True
            i += 1
            continue

        # ---- fenced code block -------------------------------------------
        fm = _FENCE.match(line)
        if fm:
            fence_char = fm["fence"][0]
            fence_len = len(fm["fence"])
            info = fm["info"].strip().split()[0].lower() if fm["info"].strip() else ""
            content: List[str] = []
            j = i + 1
            closed = False
            while j < n:
                cm = _FENCE.match(lines[j])
                if cm and cm["fence"][0] == fence_char and len(cm["fence"]) >= fence_len:
                    closed = True
                    break
                content.append(lines[j])
                j += 1
            end = j if closed else n - 1
            block = Block(
                kind="code", line=i + 1, end_line=end + 1,
                text="\n".join(content), lang=info,
            )
            doc.blocks.append(block)
            doc.code_blocks.append(block)
            doc.commands.extend(_extract_commands(content, i + 2, info))
            i = (j + 1) if closed else n
            continue

        # ---- ATX heading --------------------------------------------------
        hm = _HEADING.match(line)
        if hm:
            level = len(hm.group(1))
            text = hm["text"].strip()
            norm = normalize_heading(text, aliases)
            slug = slugify(text, seen)
            doc.headings.append(Heading(level, text, norm, slug, i + 1))
            doc.anchors.add(slug)
            doc.blocks.append(Block("heading", i + 1, i + 1, text, level=level))
            i += 1
            continue

        # ---- Setext heading ----------------------------------------------
        if i + 1 < n and line.strip() and not _is_pipe_row(line):
            sm = _SETEXT.match(lines[i + 1])
            if sm and not _FENCE.match(lines[i + 1]) and not _HEADING.match(line):
                level = 1 if sm["mark"][0] == "=" else 2
                text = line.strip()
                norm = normalize_heading(text, aliases)
                slug = slugify(text, seen)
                doc.headings.append(Heading(level, text, norm, slug, i + 1))
                doc.anchors.add(slug)
                doc.blocks.append(Block("heading", i + 1, i + 2, text, level=level))
                i += 2
                continue

        # ---- pipe table ---------------------------------------------------
        if _is_pipe_row(line) and i + 1 < n and _TABLE_SEP.match(lines[i + 1]):
            cols = _table_cols(line)
            j = i + 2
            rows = 0
            while j < n and _is_pipe_row(lines[j]) and lines[j].strip():
                rows += 1
                j += 1
            doc.blocks.append(Block("table", i + 1, j, rows=rows, cols=cols))
            doc.tables.append(Block("table", i + 1, j, rows=rows, cols=cols))
            i = j
            continue

        # ---- plain line: links, anchors, simple block classification -----
        scan = _strip_code_spans(line)
        for m in _INLINE_LINK.finditer(scan):
            target = (m.group(3) or m.group(4) or "").strip()
            if not target:
                continue
            kind = "image" if m.group(1) == "!" else "inline"
            doc.links.append(Link(target, i + 1, kind, m.group(2).strip()))
        for m in _AUTOLINK.finditer(scan):
            doc.links.append(Link(m.group(1), i + 1, "autolink"))
        for m in _REF_USE.finditer(scan):
            key = (m.group(2) or m.group(1)).strip().lower()
            if key in ref_defs:
                doc.links.append(Link(ref_defs[key], i + 1, "reference", m.group(1)))
        for m in _BARE_URL.finditer(scan):
            doc.links.append(Link(m.group(0).rstrip(".,;"), i + 1, "bare"))
        for m in _HTML_ID.finditer(line):
            doc.anchors.add(m.group(1))

        stripped = line.strip()
        if not stripped:
            kind = "paragraph"
        elif stripped.startswith(("#", ">", "-", "*", "+")) or re.match(r"^\d+[.)]\s", stripped):
            kind = "quote" if stripped.startswith(">") else "list"
        elif re.match(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            kind = "hr"
        elif stripped.startswith("<"):
            kind = "html"
        else:
            kind = "paragraph"
        doc.blocks.append(Block(kind, i + 1, i + 1, stripped))
        i += 1

    _classify_links(doc)
    return doc


def _classify_links(doc: Document) -> None:
    for link in doc.links:
        target = link.target.strip()
        low = target.lower()
        if low.startswith(("http://", "https://")):
            doc.external_links.add(target)
        elif low.startswith(("mailto:", "tel:", "data:")):
            continue
        else:
            doc.local_links.add(target)


def _extract_commands(content: List[str], start_line: int, lang: str) -> List[Command]:
    """Extract copy-pasteable shell commands from a fenced code block."""
    shell = lang in SHELL_LANGS
    out: List[Command] = []
    pending = ""
    pending_line = 0
    for offset, raw in enumerate(content):
        line_no = start_line + offset
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#") and not stripped.startswith("#!"):
            continue
        line = _PROMPT.sub("", line.lstrip())
        if not line.strip():
            continue
        if not shell and not _COMMAND_START.match(line.strip()):
            continue
        if line.rstrip().endswith("\\"):
            if not pending:
                pending_line = line_no
            pending += line.rstrip()[:-1].rstrip() + " "
            continue
        if pending:
            out.append(Command(pending_line, (pending + line.strip()).strip(), lang or "text"))
            pending = ""
        else:
            out.append(Command(line_no, line.strip(), lang or "text"))
    if pending:
        out.append(Command(pending_line, pending.strip(), lang or "text"))
    return out


def safe_resolve(root: str, link: str, from_file: str) -> str | None:
    """Resolve a local link to an absolute path, staying inside *root*.

    Returns ``None`` when the link is external, an anchor, or escapes the root
    (path traversal). This is a hard safety boundary: DocConcord never reads
    outside the audited directory.
    """
    if not link or link.startswith(("#", "mailto:", "tel:", "data:")):
        return None
    if link.lower().startswith(("http://", "https://", "//")):
        return None
    clean = link.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return None
    base_dir = os.path.dirname(os.path.abspath(from_file))
    candidate = os.path.realpath(os.path.join(base_dir, clean))
    root_real = os.path.realpath(root)
    if candidate != root_real and not candidate.startswith(root_real + os.sep):
        return None
    return candidate
