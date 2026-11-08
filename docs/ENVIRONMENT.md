# ⚙️ 环境与配置 · Environment & Configuration

## 运行时要求

- Python **3.9+**（已在 3.9 / 3.10 / 3.11 / 3.12 / 3.13 的 CI 矩阵中验证）
- 操作系统：Windows / macOS / Linux，无平台专属依赖
- **零第三方运行时依赖**：不需要 `pip install` 任何包即可 `python -m docconcord`
- 编码：全程 UTF-8，源码以 `utf-8-sig` 读取，兼容带 BOM 的 Markdown

## 无需任何密钥

DocConcord 完全离线运行，**不需要 API Key、Token 或任何凭据**。请勿在配置文件中写入敏感信息；`.gitignore` 已排除 `.env` 与 `*.local.json`。

## 可选环境变量

环境变量仅作为便捷覆盖，优先级低于命令行参数：

| 变量 | 对应参数 | 示例 |
| --- | --- | --- |
| `DOCCONCORD_BASE` | `--base` | `README.en.md` |
| `DOCCONCORD_FORMAT` | `--format` | `junit` |
| `DOCCONCORD_FAIL_ON` | `--fail-on` | `warning` |

## 配置文件 `.docconcord.json`

放在待审计目录的根目录。完整字段与默认值：

```json
{
  "base": "",
  "format": "text",
  "fail_on": "error",
  "online": false,
  "aliases": {},
  "disabled_rules": [],
  "max_file_bytes": 2000000
}
```

| 字段 | 说明 |
| --- | --- |
| `base` | 留空则自动选择：优先无语言标签的文件（如 `README.md`），其次 English |
| `format` | `text` / `json` / `markdown` / `junit` |
| `fail_on` | `error` / `warning` / `info` / `never` |
| `online` | 是否启用外链在线探测，默认 `false` |
| `aliases` | 标题别名表，把各语言标题映射到同一个 canonical key |
| `disabled_rules` | 要豁免的规则 ID 列表 |
| `max_file_bytes` | 单个文档大小上限，超限跳过 |

优先级：**内置默认值 < `.docconcord.json` < 环境变量 < CLI 参数**。

## 别名表示例

见 [`aliases.example.json`](aliases.example.json)。键为归一化后的标题（小写、无序号、无 emoji 与标点），值为 canonical key：

```json
{
  "quick start": "quick-start",
  "快速开始": "quick-start",
  "installation": "install"
}
```

未配置别名表时，工具按**标题序号**对齐，适合「三语结构相同、标题文字不同」的常规场景；配置后可精确报告「缺少哪一节」。

## CI 集成

```yaml
- name: Audit multilingual docs
  run: python -m docconcord check . --format junit --output docconcord.xml --fail-on error
```

`.github/workflows/ci.yml` 中已包含三平台 × 五个 Python 版本的完整矩阵。
