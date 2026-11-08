"""Pluggable rule engine.

Every rule module exposes ``check(report) -> list[Finding]``. Rules are pure
functions over the parsed :class:`~docconcord.model.Report`; they never read
files (except the explicitly opted-in online link probe) and never write.
"""

from __future__ import annotations

from typing import Callable, List

from ..model import Finding, Report
from .common import families
from .blocks import check as check_blocks
from .links import check as check_links
from .structure import check as check_structure

RULE_FUNCTIONS: List[Callable[[Report], List[Finding]]] = [
    check_structure,
    check_blocks,
    check_links,
]

RULE_CATALOG = {
    "S001": "缺失章节 (missing_section)",
    "S002": "多余章节 (extra_section)",
    "S003": "标题层级不一致 (heading_level_mismatch)",
    "S004": "章节顺序不一致 (heading_order_mismatch)",
    "B001": "代码块数量不一致 (code_block_count_mismatch)",
    "B002": "代码块语言标注不一致 (code_lang_mismatch)",
    "B003": "代码块缺少语言标注 (missing_code_lang)",
    "B004": "表格数量不一致 (table_count_mismatch)",
    "B005": "表格形状不一致 (table_shape_mismatch)",
    "B006": "可复制命令数量不一致 (command_count_mismatch)",
    "B007": "可复制命令内容不一致 (command_mismatch)",
    "L001": "外部链接集合不一致 (external_link_set_mismatch)",
    "L002": "锚点不存在 (broken_anchor)",
    "L003": "本地链接目标不存在 (broken_local_path)",
    "L004": "本地链接集合不一致 (local_link_set_mismatch)",
    "L005": "在线链接不可达 (online_unreachable)",
    "X001": "危险示例命令 (unsafe_command)",
    "X002": "疑似硬编码凭据 (hardcoded_secret)",
}


def run_rules(report: Report) -> List[Finding]:
    findings: List[Finding] = []
    for fn in RULE_FUNCTIONS:
        findings.extend(fn(report))
    disabled = set(report.disabled_rules)
    if disabled:
        findings = [f for f in findings if f.rule not in disabled]
    # Deterministic ordering is part of the contract (byte-identical reports).
    findings.sort(key=lambda f: (f.file, f.line, f.rule, f.lang, f.message))
    return findings
