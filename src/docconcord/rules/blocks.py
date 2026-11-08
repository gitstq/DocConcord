"""Content parity rules B001-B007 and safety rules X001-X002.

B-rules compare *shape* (code blocks, tables, copy-paste commands) between a
translation and its base. X-rules scan example commands in every document for
patterns that should never appear in a public README: destructive one-liners
and hard-coded credentials.
"""

from __future__ import annotations

import re
from typing import List

from ..model import Finding, Report
from .common import families

UNSAFE_PATTERNS = [
    (re.compile(r"\brm\s+-[rRfF]{1,2}\b[^\n|]*(?:/\s*$|/\*|\$HOME|\$PWD|~/?\s*$)"),
     "递归删除根目录或通配符路径"),
    (re.compile(r"(?:curl|wget)\b[^\n]*\|\s*(?:sudo\s+)?(?:ba|z|k|da)?sh\b"),
     "未校验即管道执行远程脚本"),
    (re.compile(r"\bchmod\s+(?:-R\s+)?777\b"), "将权限过度开放为 777"),
    (re.compile(r"\bdd\s+if="), "裸设备写入 dd"),
    (re.compile(r"\bmkfs(?:\.\w+)?\b"), "磁盘格式化 mkfs"),
    (re.compile(r"\beval\s*\(|\beval\s+[\"']?\$\("), "eval 动态执行外部输入"),
    (re.compile(r"(?:^|\s)>\s*/dev/(?:sda|nvme|disk)\b"), "重定向覆盖块设备"),
]

SECRET_PATTERNS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "疑似 GitHub 访问令牌"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "疑似 OpenAI 风格 API 密钥"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "疑似 AWS 访问密钥 ID"),
    (re.compile(r"(?:password|passwd|token|secret|api[_-]?key)\s*[:=]\s*[\"'][^\"'$]{8,}[\"']", re.I),
     "疑似硬编码凭据字面量"),
]


def _short(text: str, limit: int = 64) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _norm_cmd(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).rstrip(";")


def _shape(doc) -> str:
    return (f"{len(doc.code_blocks)} 个代码块 / {len(doc.tables)} 个表格 / "
            f"{len(doc.commands)} 条命令")


def check(report: Report) -> List[Finding]:
    out: List[Finding] = []

    for _fam, base, others in families(report):
        for doc in others:
            # ---- code blocks --------------------------------------------
            if len(doc.code_blocks) != len(base.code_blocks):
                out.append(Finding(
                    "B001", "error",
                    f"代码块数量 {len(doc.code_blocks)}，基准为 {len(base.code_blocks)}（形状：{_shape(doc)}）",
                    doc.relpath, 0, doc.lang,
                    "同步示例代码块；缺失的示例会让读者无法复现。",
                ))
            for idx in range(min(len(base.code_blocks), len(doc.code_blocks))):
                b, o = base.code_blocks[idx], doc.code_blocks[idx]
                if b.lang and o.lang and b.lang != o.lang:
                    out.append(Finding(
                        "B002", "warning",
                        f"第 {idx + 1} 个代码块语言标注为 `{o.lang}`，基准为 `{b.lang}`",
                        doc.relpath, o.line, doc.lang,
                        f"统一标注为 `{b.lang}`，以保证语法高亮与结构一致。",
                    ))
            for cb in doc.code_blocks:
                if not cb.lang:
                    out.append(Finding(
                        "B003", "info",
                        "代码块未标注语言，无法参与语言一致性校验",
                        doc.relpath, cb.line, doc.lang,
                        "补上语言标注，例如 ```bash 或 ```python。",
                    ))

            # ---- tables --------------------------------------------------
            if len(doc.tables) != len(base.tables):
                out.append(Finding(
                    "B004", "error",
                    f"表格数量 {len(doc.tables)}，基准为 {len(base.tables)}",
                    doc.relpath, 0, doc.lang,
                    "同步表格，参数对照表缺失是常见的文档漂移。",
                ))
            for idx in range(min(len(base.tables), len(doc.tables))):
                b, o = base.tables[idx], doc.tables[idx]
                if (b.rows, b.cols) != (o.rows, o.cols):
                    out.append(Finding(
                        "B005", "warning",
                        f"第 {idx + 1} 个表格为 {o.rows} 行 × {o.cols} 列，基准为 {b.rows} 行 × {b.cols} 列",
                        doc.relpath, o.line, doc.lang,
                        "补齐行列，避免参数说明缺项。",
                    ))

            # ---- copy-paste commands -------------------------------------
            if len(doc.commands) != len(base.commands):
                out.append(Finding(
                    "B006", "warning",
                    f"可复制命令 {len(doc.commands)} 条，基准为 {len(base.commands)} 条",
                    doc.relpath, 0, doc.lang,
                    "安装/启动命令应跨语言保持完全一致。",
                ))
            for idx in range(min(len(base.commands), len(doc.commands))):
                b, o = base.commands[idx], doc.commands[idx]
                if _norm_cmd(b.text) != _norm_cmd(o.text):
                    out.append(Finding(
                        "B007", "warning",
                        f"第 {idx + 1} 条命令与基准不同：{_short(o.text)}",
                        doc.relpath, o.line, doc.lang,
                        f"基准为：{_short(b.text)}；命令差异通常意味着版本未同步。",
                    ))

    # ---- safety rules apply to every document, including the base --------
    for doc in report.documents:
        for cmd in doc.commands:
            for pattern, why in UNSAFE_PATTERNS:
                if pattern.search(cmd.text):
                    out.append(Finding(
                        "X001", "error",
                        f"危险示例命令（{why}）：{_short(cmd.text)}",
                        doc.relpath, cmd.line, doc.lang,
                        "替换为安全等价写法，或明确标注为不可直接执行的示意。",
                    ))
                    break
            for pattern, why in SECRET_PATTERNS:
                if pattern.search(cmd.text):
                    out.append(Finding(
                        "X002", "error",
                        f"{why}，请勿把真实凭据写进公开文档：{_short(cmd.text)}",
                        doc.relpath, cmd.line, doc.lang,
                        "改用占位符（如 <YOUR_TOKEN>）并立即轮换已泄露的凭据。",
                    ))
                    break
    return out
