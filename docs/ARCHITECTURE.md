# 🏗️ 架构设计 · Architecture

## 1. 设计目标

| 目标 | 实现手段 |
| --- | --- |
| 零依赖 | 仅标准库；`pyproject.toml` 中 `dependencies = []` |
| 确定性 | 文件与发现项全排序后再渲染；不依赖时间戳、随机源、网络状态 |
| 离线优先 | 默认零网络；`--online` 才做外链 HEAD 探测 |
| 只读优先 | 规则不写文件；唯一写操作是 `fix --apply` |
| 可测试 | 规则为纯函数，模型为惰性 dataclass |

## 2. 数据流

```
discover_documents()  →  (path, relpath, lang, family)
        ↓
parse_document()      →  Document(blocks / headings / links / commands / anchors)
        ↓
choose_base()         →  标记 is_base
        ↓
run_rules()           →  List[Finding]  (排序 + disabled_rules 过滤)
        ↓
render_report()       →  text | json | markdown | junit
        ↓
exit_code()           →  0 / 1
```

## 3. 模块拆分

| 模块 | 职责 |
| --- | --- |
| `model.py` | `Block` / `Heading` / `Link` / `Command` / `Document` / `Finding` / `Report` |
| `i18n.py` | 语言标签识别、文档族分组、标题归一化、GitHub 风格 slug |
| `parser.py` | 轻量 Markdown 块/链接解析、命令提取、`safe_resolve` 路径边界 |
| `config.py` | 默认值 + `.docconcord.json` + 环境变量 + CLI 覆盖，四级优先级 |
| `rules/common.py` | 族迭代辅助（独立模块，避免循环导入） |
| `rules/structure.py` | S001–S004 章节结构、层级、顺序 |
| `rules/blocks.py` | B001–B007 内容形状、X001–X002 安全哨兵 |
| `rules/links.py` | L001–L005 链接集合、锚点、本地路径、在线探针 |
| `report.py` | 四种渲染器与门禁退出码 |
| `fix.py` | 保守补丁生成与 `--apply` 写回 |
| `cli.py` | `check` / `scan` / `fix` / `rules` / `version` |
| `engine.py` | 编排：发现 → 解析 → 选基准 → 跑规则 |

## 4. 对齐算法

- **默认（无别名表）**：标题按**序号**对齐，比较数量与层级。译文标题文字天然不同，比较文本只会制造误报。
- **启用别名表**：`normalize_heading` 先去序号、emoji、强调与标点，再查 `aliases` 映射到 canonical key；此后按 key 比对缺失章节、多余章节、顺序与层级，能精确点名「Install 章节缺失」。

## 5. 安全边界

1. `safe_resolve()` 用 `os.path.realpath` 校验解析结果必须位于审计根目录内，越界链接直接忽略（防路径穿越）。
2. 文档中的命令**只被当成文本分析**，从不执行；`X001` 反而会拦截 `curl | sh`、`rm -rf /`、`dd if=` 等危险示例。
3. `X002` 扫描疑似 GitHub / OpenAI / AWS 凭据字面量并提示立即轮换。
4. `max_file_bytes` 默认 2 MB，避免读取超大文件。
5. 在线探测仅支持 `http/https`，5 秒超时，失败记为 warning 而非崩溃。

## 6. 技术选型理由

| 选择 | 理由 |
| --- | --- |
| 不实现完整 CommonMark | 审计只需 5 类构造；行为可预测、跨平台一致、审计面极小 |
| `unittest` 而非 `pytest` | 零依赖自测，`python -m unittest discover` 开箱即用 |
| `src/` 布局 + PEP 621 | 避免导入路径污染，元数据单一来源 |
| 报告排序后渲染 | 保证字节一致，便于 CI 缓存与 diff |
