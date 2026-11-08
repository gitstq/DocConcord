"""Four deterministic renderers (text / json / markdown / junit) + exit codes."""

from __future__ import annotations

import json
import xml.sax.saxutils as saxutils
from typing import Dict

from .model import Finding, Report, SEVERITY_ORDER

_SEV_MARK = {"error": "✖", "warning": "⚠", "info": "ℹ"}
_SEV_LABEL = {"error": "ERROR", "warning": "WARN", "info": "INFO"}
_RULE_GATE = {"error": 2, "warning": 1, "info": 0}


def _group(findings) -> Dict[str, list]:
    out: Dict[str, list] = {}
    for f in findings:
        out.setdefault(f.file or "(全局)", []).append(f)
    return out


def render_text(report: Report) -> str:
    s = report.as_dict()["summary"]
    lines = [
        "DocConcord v1.0.0 · 多语言文档一致性契约校验",
        "=" * 56,
        f"审计根目录 : {report.root}",
        f"基准文档   : {report.base}",
        f"文档族     : {s['families']}   参与文档: {s['documents']}",
        f"在线探测   : {'开启' if report.online else '关闭（离线优先）'}",
        "-" * 56,
        f"发现项     : {s['findings']}  "
        f"(错误 {s['errors']} / 警告 {s['warnings']} / 提示 {s['infos']})",
        f"一致性得分 : {s['parity_score']} / 100",
        "-" * 56,
    ]
    if not report.families:
        lines += ["未发现多语言文档族（需要同一 stem 下至少 2 个语言版本的 .md 文件）。", ""]
    if not report.findings:
        lines += ["✅ 全部校验通过，未发现结构漂移。", ""]
    else:
        for file, group in _group(report.findings).items():
            lines.append(f"▸ {file}")
            for f in sorted(group, key=lambda x: (x.line, x.rule)):
                loc = f":{f.line}" if f.line else ""
                lines.append(f"    {_SEV_MARK[f.severity]} [{f.rule}] {f.message}{loc}")
                if f.suggestion:
                    lines.append(f"       ↳ 建议: {f.suggestion}")
            lines.append("")
    lines.append("提示: 使用 --format json|markdown|junit 可生成 CI 可直接消费的报告。")
    return "\n".join(lines)


def render_json(report: Report) -> str:
    return json.dumps(report.as_dict(), ensure_ascii=False, indent=2)


def render_markdown(report: Report) -> str:
    s = report.as_dict()["summary"]
    out = [
        "# DocConcord 审计报告",
        "",
        "| 指标 | 值 |",
        "| --- | --- |",
        f"| 审计根目录 | `{report.root}` |",
        f"| 基准文档 | `{report.base}` |",
        f"| 文档族 / 参与文档 | {s['families']} / {s['documents']} |",
        f"| 错误 / 警告 / 提示 | {s['errors']} / {s['warnings']} / {s['infos']} |",
        f"| 一致性得分 | **{s['parity_score']} / 100** |",
        "",
        "## 发现项",
        "",
    ]
    if not report.findings:
        out += ["✅ 全部校验通过，未发现结构漂移。", ""]
    else:
        out += [
            "| 级别 | 规则 | 文件 | 行 | 说明 |",
            "| --- | --- | --- | --- | --- |",
        ]
        for f in report.findings:
            msg = f.message.replace("|", "\\|").replace("\n", " ")
            out.append(
                f"| {_SEV_LABEL[f.severity]} | `{f.rule}` | `{f.file}` | "
                f"{f.line or '-'} | {msg} |"
            )
        out.append("")
    return "\n".join(out)


def render_junit(report: Report) -> str:
    by_file = _group(report.findings)
    cases = []
    for file, group in by_file.items():
        failures = sum(1 for f in group if f.severity in ("error", "warning"))
        body = []
        for f in group:
            body.append(
                f'    <testcase classname="{saxutils.escape(f.rule)}" '
                f'name="{saxutils.escape(file)}:{f.line}">'
            )
            if f.severity in ("error", "warning"):
                body.append(
                    f'      <failure message="{saxutils.escape(f.message)}">'
                    f'{saxutils.escape(f.suggestion)}</failure>'
                )
            body.append("    </testcase>")
        cases.append(
            f'  <testsuite name="{saxutils.escape(file)}" tests="{len(group)}" '
            f'failures="{failures}">\n' + "\n".join(body) + "\n  </testsuite>"
        )
    total = len(report.findings)
    failures = sum(1 for f in report.findings if f.severity in ("error", "warning"))
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    head += f'<testsuites name="DocConcord" tests="{total}" failures="{failures}">\n'
    return head + "\n".join(cases) + "\n</testsuites>\n"


RENDERERS = {
    "text": render_text,
    "json": render_json,
    "markdown": render_markdown,
    "junit": render_junit,
}


def render_report(report: Report, fmt: str = "text") -> str:
    fn = RENDERERS.get(fmt)
    if fn is None:
        raise ValueError(f"未知输出格式: {fmt}")
    return fn(report)


def exit_code(report: Report, fail_on: str = "error") -> int:
    """0 = passed, 1 = gate violated. Runtime errors use 2 (handled by CLI)."""
    if fail_on == "never":
        return 0
    threshold = SEVERITY_ORDER[fail_on]
    return 1 if any(SEVERITY_ORDER[f.severity] >= threshold for f in report.findings) else 0
