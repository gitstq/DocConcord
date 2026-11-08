"""Reporters are deterministic, machine-readable and gate correctly."""

import json
import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from docconcord.model import Document, Finding, Report  # noqa: E402
from docconcord.report import (  # noqa: E402
    exit_code, render_json, render_junit, render_markdown,
    render_report, render_text,
)


def sample_report():
    base = Document("/r/README.en.md", "README.en.md", "en", "README", is_base=True)
    other = Document("/r/README.zh-CN.md", "README.zh-CN.md", "zh-CN", "README")
    rep = Report(
        root="/r", base="README.en.md", documents=[base, other],
        families={"README": ["README.en.md", "README.zh-CN.md"]},
    )
    rep.findings = [
        Finding("S001", "error", "缺少章节", "README.zh-CN.md", 12, "zh-CN", "补齐章节"),
        Finding("B003", "info", "代码块无标注", "README.zh-CN.md", 30, "zh-CN", ""),
    ]
    return rep


class ReportTest(unittest.TestCase):
    def test_json_is_parseable_and_complete(self):
        data = json.loads(render_json(sample_report()))
        self.assertEqual(data["tool"], "DocConcord")
        self.assertEqual(data["summary"]["errors"], 1)
        self.assertEqual(data["summary"]["infos"], 1)
        self.assertEqual(len(data["findings"]), 2)
        self.assertIn("parity_score", data["summary"])

    def test_junit_is_valid_xml(self):
        xml = render_junit(sample_report())
        root = ET.fromstring(xml)
        self.assertEqual(root.tag, "testsuites")
        self.assertEqual(root.attrib["failures"], "1")

    def test_markdown_and_text_renderers(self):
        self.assertIn("DocConcord 审计报告", render_markdown(sample_report()))
        self.assertIn("一致性得分", render_text(sample_report()))

    def test_render_report_dispatch_and_unknown_format(self):
        self.assertTrue(render_report(sample_report(), "json").startswith("{"))
        with self.assertRaises(ValueError):
            render_report(sample_report(), "yaml")

    def test_exit_code_gate(self):
        rep = sample_report()
        self.assertEqual(exit_code(rep, "error"), 1)
        self.assertEqual(exit_code(rep, "warning"), 1)
        self.assertEqual(exit_code(rep, "never"), 0)
        rep.findings = [Finding("B003", "info", "x")]
        self.assertEqual(exit_code(rep, "error"), 0)
        self.assertEqual(exit_code(rep, "warning"), 0)
        self.assertEqual(exit_code(rep, "info"), 1)

    def test_parity_score_range(self):
        rep = sample_report()
        self.assertTrue(0 <= rep.parity_score <= 100)
        rep.findings = []
        self.assertEqual(rep.parity_score, 100)


if __name__ == "__main__":
    unittest.main()
