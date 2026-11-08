"""Parser correctness: blocks, headings, links, anchors, commands, path safety."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from docconcord.i18n import slugify  # noqa: E402
from docconcord.parser import parse_document, safe_resolve  # noqa: E402


SAMPLE = """# DocConcord Demo

> 🌐 [English](README.en.md) · [简体中文](README.zh-CN.md)

## 🎉 项目介绍

Some prose with an [inline link](https://example.com/guide), an
<https://example.com/auto> autolink, a bare https://example.com/bare URL
and a [reference link][ref].

```bash
pip install docconcord
$ docconcord check . --format json
```

| 参数 | 说明 |
| --- | --- |
| --base | 基准文档 |
| --fail-on | 门禁阈值 |

Intro
=====

See [本地文档](docs/ARCHITECTURE.md#design) and [不存在的锚点](#nope).

[ref]: https://example.com/ref
"""


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "README.zh-CN.md")
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(SAMPLE)
        self.doc = parse_document(self.path, "README.zh-CN.md", "zh-CN", "README")

    def tearDown(self):
        self.tmp.cleanup()

    def test_headings_atx_and_setext(self):
        levels = [h.level for h in self.doc.headings]
        self.assertIn(1, levels)
        self.assertIn(2, levels)
        self.assertTrue(any(h.text == "Intro" and h.level == 1 for h in self.doc.headings))

    def test_slug_and_duplicates(self):
        seen = {}
        self.assertEqual(slugify("Hello World", seen), "hello-world")
        self.assertEqual(slugify("Hello World", seen), "hello-world-1")
        self.assertEqual(slugify("🎉 快速开始", seen), "快速开始")

    def test_fenced_code_and_commands(self):
        self.assertEqual(len(self.doc.code_blocks), 1)
        self.assertEqual(self.doc.code_blocks[0].lang, "bash")
        self.assertEqual(len(self.doc.commands), 2)
        self.assertEqual(self.doc.commands[0].text, "pip install docconcord")
        self.assertTrue(self.doc.commands[1].text.startswith("docconcord check"))

    def test_table_shape(self):
        self.assertEqual(len(self.doc.tables), 1)
        self.assertEqual((self.doc.tables[0].rows, self.doc.tables[0].cols), (2, 2))

    def test_links_and_anchors(self):
        targets = {link.target for link in self.doc.links}
        self.assertIn("https://example.com/guide", targets)
        self.assertIn("https://example.com/auto", targets)
        self.assertIn("https://example.com/bare", targets)
        self.assertIn("https://example.com/ref", targets)
        self.assertIn("docs/ARCHITECTURE.md#design", targets)
        self.assertIn("项目介绍", self.doc.anchors)

    def test_classified_link_sets(self):
        self.assertTrue(all(x.startswith("http") for x in self.doc.external_links))
        self.assertIn("#nope", self.doc.local_links)

    def test_code_fence_content_is_not_parsed_as_headings(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            p = os.path.join(tmp.name, "x.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("# Real\n\n```\n# Not a heading\n[not a link](x)\n```\n")
            d = parse_document(p, "x.md", "und", "x")
            self.assertEqual(len(d.headings), 1)
            self.assertEqual(d.headings[0].text, "Real")
        finally:
            tmp.cleanup()

    def test_safe_resolve_blocks_path_traversal(self):
        root = self.tmp.name
        self.assertIsNone(safe_resolve(root, "../../etc/passwd", self.path))
        self.assertIsNone(safe_resolve(root, "#anchor", self.path))
        self.assertIsNone(safe_resolve(root, "https://example.com", self.path))
        resolved = safe_resolve(root, "docs/a.md", self.path)
        self.assertIsNotNone(resolved)
        self.assertTrue(resolved.startswith(os.path.realpath(root)))


if __name__ == "__main__":
    unittest.main()
