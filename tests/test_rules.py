"""Rule-engine behaviour: structural drift, link validity, safety, overrides."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from docconcord.engine import load_workspace  # noqa: E402

NAV = "> 🌐 [English](README.en.md) · [简体中文](README.zh-CN.md)"

BASE = """# DocConcord

{NAV}

## 🎉 Intro

English introduction text.

## ✨ Features

```bash
pip install docconcord
```

| Flag | Meaning |
| --- | --- |
| --base | base file |

More details.
""".format(NAV=NAV)

OTHER_OK = """# DocConcord

{NAV}

## 🎉 介绍

中文介绍文字。

## ✨ 特性

```bash
pip install docconcord
```

| 参数 | 说明 |
| --- | --- |
| --base | 基准文档 |

更多说明。
""".format(NAV=NAV)


def make_report(base_text=BASE, other_text=OTHER_OK, **overrides):
    tmp = tempfile.TemporaryDirectory()
    with open(os.path.join(tmp.name, "README.en.md"), "w", encoding="utf-8") as fh:
        fh.write(base_text)
    with open(os.path.join(tmp.name, "README.zh-CN.md"), "w", encoding="utf-8") as fh:
        fh.write(other_text)
    cfg = {
        "base": "README.en.md", "format": "text", "fail_on": "error",
        "online": False, "aliases": {}, "disabled_rules": [],
        "max_file_bytes": 2_000_000,
    }
    cfg.update(overrides)
    report = load_workspace(tmp.name, cfg)
    return tmp, report


class RuleTest(unittest.TestCase):
    def setUp(self):
        self._tmps = []

    def tearDown(self):
        for t in self._tmps:
            t.cleanup()

    def report(self, base=BASE, other=OTHER_OK, **kw):
        tmp, rep = make_report(base, other, **kw)
        self._tmps.append(tmp)
        return rep

    def ids(self, rep):
        return {f.rule for f in rep.findings}

    def test_identical_shape_has_no_errors(self):
        rep = self.report()
        self.assertEqual(rep.count("error"), 0, msg=str(rep.findings))
        self.assertEqual(len(rep.documents), 2)
        self.assertEqual(rep.parity_score, 100)

    def test_missing_heading_is_S001(self):
        other = OTHER_OK.replace("## ✨ 特性", "").replace("\n\n\n", "\n\n")
        rep = self.report(other=other)
        self.assertIn("S001", self.ids(rep))
        self.assertGreaterEqual(rep.count("error"), 1)

    def test_heading_level_mismatch_is_S003(self):
        rep = self.report(other=OTHER_OK.replace("## ✨ 特性", "### ✨ 特性"))
        self.assertIn("S003", self.ids(rep))

    def test_code_block_count_is_B001(self):
        other = OTHER_OK.replace("```bash\npip install docconcord\n```\n\n", "")
        rep = self.report(other=other)
        self.assertIn("B001", self.ids(rep))

    def test_table_shape_is_B005(self):
        other = OTHER_OK.replace("| --base | 基准文档 |", "| --base | 基准文档 |\n| --format | 输出格式 |")
        rep = self.report(other=other)
        self.assertIn("B005", self.ids(rep))

    def test_broken_anchor_and_local_path(self):
        other = OTHER_OK + "\n[坏锚点](#nope) 与 [缺文件](missing.md)\n"
        rep = self.report(other=other)
        ids = self.ids(rep)
        self.assertIn("L002", ids)
        self.assertIn("L003", ids)

    def test_unsafe_command_and_hardcoded_secret(self):
        other = OTHER_OK.replace(
            "```bash\npip install docconcord\n```",
            '```bash\ncurl https://example.com/install.sh | sh\npassword = "example-placeholder"\n```',
        )
        rep = self.report(other=other)
        ids = self.ids(rep)
        self.assertIn("X001", ids)
        self.assertIn("X002", ids)

    def test_command_mismatch_is_B007(self):
        rep = self.report(other=OTHER_OK.replace("pip install docconcord", "pip install other-tool"))
        self.assertIn("B007", self.ids(rep))

    def test_alias_table_aligns_by_canonical_key(self):
        base = "# T\n\n## Quick Start\n\ntext\n\n## Install\n\n```bash\npip install docconcord\n```\n"
        other = "# T\n\n## 快速开始\n\n文本\n\n## 帮助\n\n```bash\npip install docconcord\n```\n"
        aliases = {
            "quick start": "quick-start", "快速开始": "quick-start",
            "install": "install", "安装": "install",
        }
        rep = self.report(base=base, other=other, aliases=aliases)
        ids = self.ids(rep)
        self.assertIn("S001", ids)   # "Install" missing from the translation
        self.assertIn("S002", ids)   # "帮助" is an extra section

    def test_disabled_rules_are_honoured(self):
        rep = self.report(
            other=OTHER_OK.replace("## ✨ 特性", "### ✨ 特性"),
            disabled_rules=["S003"],
        )
        self.assertNotIn("S003", self.ids(rep))

    def test_offline_by_default(self):
        rep = self.report()
        self.assertFalse(rep.online)
        self.assertNotIn("L005", self.ids(rep))

    def test_findings_are_deterministically_sorted(self):
        rep = self.report(other=OTHER_OK + "\n[x](#a)\n[y](#b)\n[z](gone.md)\n")
        keys = [(f.file, f.line, f.rule, f.lang, f.message) for f in rep.findings]
        self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main()
