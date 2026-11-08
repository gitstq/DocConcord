"""Link rules L001-L005: link-set divergence, broken anchors and missing paths.

Offline by default. ``--online`` enables an opt-in HEAD probe for external
URLs; nothing else in DocConcord ever opens a network connection.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from ..model import Document, Finding, Report
from ..parser import parse_document, safe_resolve
from .common import families


def _short(text: str, limit: int = 72) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _anchors_of(path: str, root: str, cache: Dict[str, object]) -> set:
    """Parse a linked Markdown file once and return its anchor set."""
    key = os.path.realpath(path)
    if key not in cache:
        try:
            doc = parse_document(path, os.path.relpath(path, root).replace(os.sep, "/"),
                                 "und", "_link_target_")
            cache[key] = doc.anchors
        except OSError:
            cache[key] = set()
    return cache[key]  # type: ignore[return-value]


def _online_probe(url: str, timeout: float = 5.0) -> Optional[str]:
    """Return an error description, or ``None`` when the URL responds 2xx/3xx."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DocConcord/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status >= 400:
                return f"HTTP {resp.status}"
        return None
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - network failures are findings, not crashes
        return type(exc).__name__


def check(report: Report) -> List[Finding]:
    out: List[Finding] = []
    cache: Dict[str, object] = {}

    # ---- cross-language link-set divergence ------------------------------
    for _fam, base, others in families(report):
        for doc in others:
            only_base = sorted(base.external_links - doc.external_links)
            only_doc = sorted(doc.external_links - base.external_links)
            for link in only_base:
                out.append(Finding(
                    "L001", "warning",
                    f"基准文档中的外部链接在本语言版本缺失：{_short(link)}",
                    doc.relpath, 0, doc.lang,
                    "补齐链接，或确认该资源确实不适用于本语言（可用 disabled_rules 豁免）。",
                ))
            for link in only_doc:
                out.append(Finding(
                    "L001", "warning",
                    f"本语言版本独有外部链接：{_short(link)}",
                    doc.relpath, 0, doc.lang,
                    "同步到基准文档，避免读者错过资源。",
                ))

            loc_base = {x for x in base.local_links if not x.startswith("#")}
            loc_doc = {x for x in doc.local_links if not x.startswith("#")}
            for link in sorted(loc_doc - loc_base):
                out.append(Finding(
                    "L004", "info",
                    f"本语言版本独有的本地链接：{_short(link)}",
                    doc.relpath, 0, doc.lang,
                    "信息项：本地化资源链接属于正常差异，确认目标存在即可。",
                ))

    # ---- per-document link validity --------------------------------------
    for doc in report.documents:
        for link in doc.links:
            target = link.target.strip()
            if link.kind == "image":
                # Images are checked for local existence below, same as links.
                pass
            low = target.lower()

            if low.startswith(("http://", "https://")):
                if report.online:
                    err = _online_probe(target)
                    if err:
                        out.append(Finding(
                            "L005", "warning",
                            f"在线探测失败（{err}）：{_short(target)}",
                            doc.relpath, link.line, doc.lang,
                            "确认链接是否永久失效；注意在线探测结果受网络环境影响。",
                        ))
                continue
            if low.startswith(("mailto:", "tel:", "data:")):
                continue

            if target.startswith("#"):
                slug = target[1:]
                if slug and slug not in doc.anchors:
                    out.append(Finding(
                        "L002", "error",
                        f"锚点 #{_short(slug)} 在本文档中不存在",
                        doc.relpath, link.line, doc.lang,
                        "修正锚点，或补上对应的标题 / 显式 HTML id。",
                    ))
                continue

            file_part, _, anchor = target.partition("#")
            resolved = safe_resolve(report.root, file_part or target, doc.path)
            if resolved is None:
                continue  # external / out-of-root: never touch it
            if not os.path.exists(resolved):
                out.append(Finding(
                    "L003", "error",
                    f"本地链接目标不存在：{_short(file_part or target)}",
                    doc.relpath, link.line, doc.lang,
                    "修正路径或补建文件；DocConcord 不会读取审计根目录之外的路径。",
                ))
                continue
            if anchor and resolved.lower().endswith((".md", ".markdown")):
                anchors = _anchors_of(resolved, report.root, cache)
                if anchors and anchor not in anchors:
                    out.append(Finding(
                        "L002", "error",
                        f"跨文件锚点 #{_short(anchor)} 在 {_short(os.path.basename(resolved))} 中不存在",
                        doc.relpath, link.line, doc.lang,
                        "修正目标文件中的标题或锚点。",
                    ))
    return out
