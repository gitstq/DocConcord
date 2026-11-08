# 🤝 贡献指南 · Contributing

感谢你愿意让 DocConcord 变得更好。这份指南适用于所有语言版本的文档与代码。

## 提交信息规范

遵循 [Angular Commit Message Convention](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#-commit-message-format)：

| 前缀 | 用途 |
| --- | --- |
| `feat:` | 新增规则、命令或报告格式 |
| `fix:` | 修复解析或判定错误 |
| `docs:` | 文档变更（**必须同步三个语言版本**） |
| `test:` | 新增或调整单元测试 |
| `refactor:` | 不改变外部行为的重构 |
| `chore:` | 构建、CI、依赖与发布配置 |

示例：`feat(rules): add S005 heading-depth drift rule`

## 新增一条规则

1. 在 `RULE_CATALOG`（`src/docconcord/rules/__init__.py`）登记唯一编号与说明。
2. 在对应规则模块里实现，返回 `Finding(rule, severity, message, file, line, lang, suggestion)`。
3. 规则必须是**纯函数**：只读 `Report`，不访问文件系统（在线探针例外且需显式开启）。
4. 在 `tests/test_rules.py` 补一个能稳定触发该规则的用例，以及一个不触发的对照用例。
5. 在 `docs/RULES.md` 补齐说明，并同步检查三个语言版本的 README 是否受影响。

## 修改文档

三份 README 由同一套结构模板生成，任何一处的**标题层级、代码块数量、表格行列、命令行内容**发生变化，都必须同步另外两份，否则 `docconcord check . --fail-on error` 会直接失败。建议本地先跑：

```bash
python -m docconcord check . --format markdown
```

## 本地开发

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m docconcord check . --fail-on error
bash scripts/selftest.sh
```

## Issue 反馈

请附上：操作系统与 Python 版本、最小可复现的 Markdown 片段、`docconcord scan .` 的输出、以及期望与实际行为。**请不要在 Issue 里粘贴任何真实凭据。**

## 行为准则

保持友善、就事论事。本项目不接受用于骚扰、攻击或规避平台规则的用途。
