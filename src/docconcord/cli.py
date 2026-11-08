"""Command line interface.

Exit codes
----------
0  gate passed (or an informational command such as ``scan``/``rules``)
1  gate violated by findings at/above ``--fail-on``
2  runtime/usage error (bad path, unparsable config, unreadable file)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .config import FAIL_ON, FORMATS, load_config
from .engine import load_workspace
from .fix import apply_fixes, generate_fixes
from .report import render_report, exit_code
from .rules import RULE_CATALOG


def _utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="docconcord",
        description="DocConcord · 零依赖、离线优先的多语言文档一致性契约校验引擎",
        epilog="示例: docconcord check . --base README.en.md --format markdown --fail-on warning",
    )
    p.add_argument("--version", action="version", version=f"DocConcord {__version__}")
    sub = p.add_subparsers(dest="command")

    c = sub.add_parser("check", help="审计多语言文档一致性")
    c.add_argument("path", nargs="?", default=".", help="待审计目录（默认当前目录）")
    c.add_argument("--base", "-b", default=None, help="基准文档文件名或相对路径（默认自动选择）")
    c.add_argument("--format", "-f", choices=FORMATS, default=None, help="报告格式")
    c.add_argument("--fail-on", choices=FAIL_ON, default=None, help="门禁阈值")
    c.add_argument("--online", action="store_true", default=None, help="启用外链在线探测（默认关闭）")
    c.add_argument("--aliases", default=None, help="标题别名表 JSON 文件路径")
    c.add_argument("--disable", action="append", default=None, metavar="RULE",
                   help="禁用指定规则 ID（可重复）")
    c.add_argument("--output", "-o", default=None, help="把报告写入文件而非标准输出")

    s = sub.add_parser("scan", help="列出发现的多语言文档族")
    s.add_argument("path", nargs="?", default=".")

    f = sub.add_parser("fix", help="生成可审阅的自动修复补丁")
    f.add_argument("path", nargs="?", default=".")
    f.add_argument("--base", "-b", default=None)
    f.add_argument("--apply", action="store_true", help="真正写回文件（默认仅输出 diff）")

    sub.add_parser("rules", help="列出全部规则 ID 与说明")
    sub.add_parser("version", help="显示版本")
    return p


def _overrides(args) -> dict:
    out = {
        "base": getattr(args, "base", None),
        "format": getattr(args, "format", None),
        "fail_on": getattr(args, "fail_on", None),
        "online": getattr(args, "online", None),
    }
    disabled = getattr(args, "disable", None)
    if disabled:
        out["disabled_rules"] = list(disabled)
    alias_file = getattr(args, "aliases", None)
    if alias_file:
        with open(alias_file, "r", encoding="utf-8") as fh:
            table = json.load(fh)
        if not isinstance(table, dict):
            raise ValueError("--aliases 需要是一个 JSON 对象")
        out["aliases"] = {str(k).lower(): str(v) for k, v in table.items()}
    return out


def _load(args):
    root = os.path.abspath(args.path)
    ov = _overrides(args)
    cfg = load_config(root, ov)
    # CLI alias table overrides keys from the config file, but keeps the rest.
    if ov.get("aliases"):
        merged = dict(cfg.get("aliases") or {})
        merged.update(ov["aliases"])
        cfg["aliases"] = merged
    if ov.get("disabled_rules"):
        cfg["disabled_rules"] = list(cfg.get("disabled_rules") or []) + ov["disabled_rules"]
    return root, cfg


def cmd_check(args) -> int:
    root, cfg = _load(args)
    report = load_workspace(root, cfg)
    text = render_report(report, cfg["format"])
    if getattr(args, "output", None):
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text.rstrip("\n") + "\n")
        print(f"报告已写入 {args.output}")
    else:
        print(text)
    return exit_code(report, cfg["fail_on"])


def cmd_scan(args) -> int:
    root, cfg = _load(args)
    report = load_workspace(root, cfg)
    print(f"DocConcord {__version__} · 扫描目录 {root}")
    print(f"基准文档: {report.base}")
    if not report.families:
        print("未发现多语言文档族：需要同一 stem 下至少 2 个语言版本的 Markdown 文件。")
        return 0
    for fam, rels in sorted(report.families.items()):
        print(f"\n▸ {fam}  ({len(rels)} 个语言版本)")
        for d in report.documents:
            if d.family == fam:
                flag = " ★基准" if d.is_base else ""
                print(f"    {d.lang:8s} {d.relpath}{flag}")
                print(f"             标题 {len(d.headings)} · 代码块 {len(d.code_blocks)} · "
                      f"表格 {len(d.tables)} · 命令 {len(d.commands)} · 链接 {len(d.links)}")
    return 0


def cmd_fix(args) -> int:
    root, cfg = _load(args)
    cfg["format"] = "text"
    report = load_workspace(root, cfg)
    fixes = generate_fixes(report)
    if not fixes:
        print("无需修复：所有文档已具备语言切换导航与代码块语言标注。")
        return 0
    for fix in fixes:
        print(f"--- {fix.relpath} · {fix.description}")
        print(fix.diff)
        print()
    if args.apply:
        changed = apply_fixes(root, fixes)
        print(f"已写回 {changed} 个文件，请重新执行 `docconcord check` 复核。")
    else:
        print(f"共 {len(fixes)} 个补丁（dry-run）。确认后加 --apply 写回。")
    return 0


def cmd_rules(_args) -> int:
    print(f"DocConcord {__version__} · 规则清单（{len(RULE_CATALOG)} 条）")
    for rid in sorted(RULE_CATALOG):
        print(f"  {rid}  {RULE_CATALOG[rid]}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    _utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    handlers = {
        "check": cmd_check, "scan": cmd_scan, "fix": cmd_fix,
        "rules": cmd_rules, "version": lambda _a: (print(f"DocConcord {__version__}"), 0)[1],
    }
    try:
        return handlers[args.command](args)
    except (OSError, ValueError, json.JSONDecodeError, NotADirectoryError) as exc:
        print(f"docconcord: 错误: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("docconcord: 已中断", file=sys.stderr)
        return 2
