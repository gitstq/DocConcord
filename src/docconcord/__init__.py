"""DocConcord - 零依赖、离线优先的多语言文档一致性契约校验引擎。

DocConcord audits a *set* of translated Markdown documents (for example
README.en.md / README.zh-CN.md / README.zh-TW.md) against one designated base
document and reports structural drift: missing sections, heading level changes,
code block / table / command / link divergence, broken anchors and unsafe
copy-paste commands.

Public API
----------
    from docconcord import audit, load_workspace, render_report

    report = audit("path/to/repo", base="README.en.md")
    print(render_report(report, "json"))

Design constraints (deliberate):
    * Python standard library only - no runtime dependencies, ever.
    * Offline first - no network access unless ``--online`` is explicitly set.
    * Deterministic - same input always produces byte-identical reports.
    * Read only by default - ``fix --apply`` is the only command that writes.
"""

from .model import Block, Command, Document, Finding, Heading, Link, Report
from .parser import parse_document
from .i18n import detect_language, discover_documents, normalize_heading
from .report import render_report, exit_code
from .engine import audit, load_workspace

__version__ = "1.0.0"
__all__ = [
    "__version__",
    "Block", "Command", "Document", "Finding", "Heading", "Link", "Report",
    "parse_document", "detect_language", "discover_documents", "normalize_heading",
    "render_report", "exit_code", "audit", "load_workspace",
]
