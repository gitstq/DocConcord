"""Structural parity rules S001-S004: heading sections, levels and order.

Alignment strategy
------------------
* Default (no alias table): headings are aligned **by ordinal**. Translated
  headings naturally have different text, so comparing text would produce
  nothing but false positives; we compare the *shape* (count + level) instead.
* With an alias table (``aliases`` maps normalized localized headings to one
  canonical key): headings are aligned **by canonical key**, which additionally
  detects genuinely missing / extra sections and order drift.
"""

from __future__ import annotations

from typing import List

from ..model import Finding, Report
from .common import families


def _short(text: str, limit: int = 48) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def check(report: Report) -> List[Finding]:
    out: List[Finding] = []
    aliases = report.aliases or {}
    by_key = bool(aliases)

    for _fam, base, others in families(report):
        base_keys = [h.norm for h in base.headings]
        base_count = len(base_keys)

        for doc in others:
            keys = [h.norm for h in doc.headings]
            count = len(keys)

            if by_key:
                missing = [k for k in base_keys if k not in keys]
                extra = [k for k in keys if k not in base_keys]
                for key in missing:
                    out.append(Finding(
                        "S001", "error",
                        f"缺少基准章节「{_short(key)}」（基准文件 {base.relpath} 中存在）",
                        doc.relpath, 0, doc.lang,
                        "补齐该章节，或在 .docconcord.json 的 disabled_rules 中显式豁免。",
                    ))
                for key in extra:
                    out.append(Finding(
                        "S002", "warning",
                        f"存在基准文件没有的额外章节「{_short(key)}」",
                        doc.relpath, 0, doc.lang,
                        "同步到基准文档，或确认这是该语言版本的合理增补。",
                    ))

                common_base = [k for k in base_keys if k in keys]
                common_doc = [k for k in keys if k in base_keys]
                if common_base != common_doc:
                    out.append(Finding(
                        "S004", "warning",
                        "共有章节的相对顺序与基准文档不一致",
                        doc.relpath, 0, doc.lang,
                        "按基准文档顺序重排章节，便于读者跨语言对照。",
                    ))

                base_levels = {}
                for h in base.headings:
                    base_levels.setdefault(h.norm, h.level)
                for h in doc.headings:
                    lvl = base_levels.get(h.norm)
                    if lvl is not None and lvl != h.level:
                        out.append(Finding(
                            "S003", "error",
                            f"章节「{_short(h.norm)}」层级为 H{h.level}，基准为 H{lvl}",
                            doc.relpath, h.line, doc.lang,
                            f"将该标题调整为 H{lvl}。",
                        ))
            else:
                if count != base_count:
                    rule = "S001" if count < base_count else "S002"
                    sev = "error" if count < base_count else "warning"
                    out.append(Finding(
                        rule, sev,
                        f"标题数量 {count}，基准文档为 {base_count}（按第 N 个标题对齐）",
                        doc.relpath, 0, doc.lang,
                        "补齐缺失章节；若各语言标题文字不同，建议配置 aliases 表做语义对齐。",
                    ))
                for idx in range(min(count, base_count)):
                    b, o = base.headings[idx], doc.headings[idx]
                    if b.level != o.level:
                        out.append(Finding(
                            "S003", "error",
                            f"第 {idx + 1} 个标题「{_short(o.text)}」层级 H{o.level}，基准 H{b.level}",
                            doc.relpath, o.line, doc.lang,
                            f"将该标题调整为 H{b.level}。",
                        ))
    return out
