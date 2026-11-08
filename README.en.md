# 🧭 DocConcord · A Parity Contract for Multilingual Docs

> 🌐 语言 / Languages: [简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

Writing one README in three languages is easy; keeping the three in sync is not. The real risk is not awkward phrasing, but a **section that quietly drifted out of alignment**. DocConcord turns "are these translations still structurally the same document?" into a deterministic CI check.

**Zero dependencies** · **Offline first** · **Deterministic output** · **CI-ready** · Python >= 3.9

## 1. 🎉 Project Overview

DocConcord is a Python library and CLI built entirely on the standard library. It audits **structural drift across the translated variants of one document**. It never translates or rewrites prose; it answers a single question: are the Simplified Chinese, Traditional Chinese and English READMEs still the same document?

**The pain it removes:**

- 🧩 English gained a Troubleshooting section while Chinese still shows the old outline, so readers follow steps that no longer match
- 🔗 An install command, a parameter table or a link quietly disappears from one locale and only surfaces as a user-reported issue
- 🧪 Diffing three long documents by hand is expensive, and most repos have no CI check that can actually fail a build

Most existing tools score a **single** README; translation tools **generate** the other locales. DocConcord fills the gap in between: a **parity contract check run after generation**, plus reviewable fix patches. Its unit of comparison is a *set of documents*, not one file - that is the fundamental difference.

The idea came from this week's GitHub Trending, where Agent Skills and reliable documentation context dominated the charts. Before committing, we ran a similarity check over all **1766 existing repositories** in the target account: context compression / token optimisation already had 50+ near-duplicates and was rejected outright. That left multilingual documentation parity as an open niche; every line of code here was written from scratch, with only the product logic and pain points as reference.

## 2. ✨ Key Features

- 🔍 **Cross-locale structure alignment**: compare section count, heading levels and order by ordinal or via an alias table
- 🧱 **Content shape checks**: fenced code blocks and their language tags, table dimensions, and copy-paste commands compared one by one
- 🔗 **Link and anchor health**: local paths, cross-file anchors and divergent external link sets in a single pass
- 🛡️ **Documentation safety sentinel**: flags destructive example commands and hard-coded credentials before a real key lands in a public README
- 📤 **Four report formats**: text / json / markdown / junit, with an exit code that works as a CI gate
- 🩹 **Reviewable auto-fix**: emits unified diffs by default; only `--apply` writes to disk

| Family | IDs | Coverage |
| --- | --- | --- |
| Structure S | S001–S004 | Missing sections, levels, order |
| Content B | B001–B007 | Code blocks, tables, commands |
| Links L | L001–L005 | Link sets, anchors, paths |
| Safety X | X001–X002 | Unsafe commands, secrets |

## 3. 🚀 Quick Start

Requirements are deliberately minimal: **Python 3.9+**, **no third-party runtime dependencies**, and Windows / macOS / Linux all work out of the box. You can run it straight from a clone without creating a virtual environment.

Install (or skip this and use `python -m docconcord` directly):

```bash
python -m pip install .
python -m docconcord --version
python -m docconcord rules
```

Three commands for a first audit: `scan` lists the discovered locales, `check` renders the report, and `--format json` makes it machine-readable.

```bash
python -m docconcord scan .
python -m docconcord check . --format text
python -m docconcord check . --format json --fail-on warning
```

When everything aligns, the output looks roughly like this (`Gate: PASS` means the check passed):

```text
DocConcord v1.0.0 - Multilingual documentation parity audit
Documents: 3   Families: 1   Findings: 0
Parity score: 100 / 100   Gate: PASS
```

## 4. 📖 Detailed Usage

| Flag | Purpose | Default |
| --- | --- | --- |
| `--base` | Base document filename or relative path | auto |
| `--format` | Report format text / json / markdown / junit | text |
| `--fail-on` | Gate threshold error / warning / info / never | error |
| `--online` | Enable online probing of external links | off |

Drop `.docconcord.json` at the repository root; CLI flags take precedence. `aliases` is an optional heading alias table, and `disabled_rules` explicitly exempts individual rules:

```json
{
  "base": "README.en.md",
  "format": "text",
  "fail_on": "error",
  "online": false,
  "aliases": {},
  "disabled_rules": [],
  "max_file_bytes": 2000000
}
```

Going further: an alias table maps localized headings onto one canonical key, so a missing section can be named precisely instead of being reported as "the Nth heading". `fix` stays deliberately conservative - it only adds a language-switch navigation line and language tags on untagged fences.

```bash
python -m docconcord check . --aliases docs/aliases.example.json --format markdown
python -m docconcord fix .
python -m docconcord fix . --apply
```

**Typical scenarios:**

- 📌 Maintain multilingual READMEs and run the gate before every release
- 📌 Accept human- or AI-produced translations against a parity report
- 📌 Emit JUnit XML in CI so failures surface directly on the pull request

> 🎬 Demo animation placeholder: `docs/assets/demo.gif` will ship in a later release; the CLI output above is the current reference.

## 5. 💡 Design & Roadmap

The engine is built around three principles, and every new rule has to satisfy all of them:

- **Deterministic**: identical input always yields a byte-identical report; documents and findings are sorted before rendering
- **Read-only first**: no network, no execution of documented commands, no writes by default - `fix --apply` is the sole exception
- **Zero dependencies**: parser, rules, reporters and CLI use only the standard library, so there is no supply-chain surface to audit

Under the hood: `dataclasses` for the model, `argparse` for the CLI, `unittest` for tests. The Markdown parser covers only what the audit actually needs - headings, fenced code, pipe tables, links and anchors - and deliberately does not attempt full CommonMark. That trade buys predictable behaviour, identical results across platforms, and a very small attack surface.

**Roadmap:**

- 🗺️ Broader language-tag detection and RTL document support
- 🗺️ SARIF output for GitHub Code Scanning
- 🗺️ An official GitHub Action and finer per-rule configuration

Community contributions are most welcome in three areas: new rules, additional language tags, and improved reporters. See the [contributing guide](CONTRIBUTING.md) and the [architecture notes](docs/ARCHITECTURE.md).

## 6. 📦 Packaging & Deployment

DocConcord is a **library / CLI tool**, so the release policy does not require Windows, macOS and Linux native binaries. We ship the source repository plus wheel and sdist artifacts; the Python interpreter itself provides cross-platform portability, and there are no platform-specific packaging traps.

Build, install the artifact and emit a CI report:

```bash
bash scripts/build.sh
python -m pip install dist/docconcord-1.0.0-py3-none-any.whl
python -m docconcord check . --format junit --output docconcord.xml
```

Add one step to any pipeline (use `scripts/build.ps1` on Windows and `scripts/build.sh` elsewhere):

```yaml
- name: Audit multilingual docs
  run: python -m docconcord check . --format junit --output docconcord.xml
```

- ✅ Supported: Python 3.9 / 3.10 / 3.11 / 3.12 / 3.13
- ✅ Encoding: UTF-8 end to end, including Simplified / Traditional Chinese, Japanese and emoji headings
- ✅ Path safety: local link resolution is confined to the audit root; out-of-tree targets are ignored

## 7. 🤝 Contributing

PRs and issues are welcome. Commit messages follow the Angular convention (`feat:` / `fix:` / `docs:` / `test:` / `refactor:`); new rules should ship with unit tests and be registered in the [rule catalog](docs/RULES.md). For issues, please include a minimal reproducible document snippet and the expected behaviour.

The local development loop:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m docconcord check . --fail-on error
```

## 8. 📄 License

This project is released under the **MIT License**: commercial use, modification, distribution and sublicensing are all permitted, provided the copyright and permission notices are retained. The full text lives in [LICENSE](LICENSE).

The license text is also available on the [MIT License site](https://opensource.org/license/mit). Changes are tracked in the [changelog](CHANGELOG.md); please report problems via [GitHub Issues](https://github.com/gitstq/DocConcord/issues).

Engineering docs: [architecture notes](docs/ARCHITECTURE.md) · [rule catalog](docs/RULES.md) · [environment guide](docs/ENVIRONMENT.md) · [contributing guide](CONTRIBUTING.md) · [changelog](CHANGELOG.md) · [license](LICENSE)

Thanks to the [GitHub repository](https://github.com/gitstq/DocConcord) and the [Python project](https://www.python.org/downloads/) for the ecosystem this builds on. DocConcord collects no telemetry and never uploads the documents it audits.

[GitHub repository](https://github.com/gitstq/DocConcord) · [Python project](https://www.python.org/downloads/) · [MIT License](https://opensource.org/license/mit) · [GitHub Issues](https://github.com/gitstq/DocConcord/issues) · [changelog](https://github.com/gitstq/DocConcord/blob/main/CHANGELOG.md)

