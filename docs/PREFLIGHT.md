# 🔭 项目预研简报 · Preflight Brief

> 对应「每日 GitHub 项目孵化」流程第一步（挖掘与合规筛选）与第二步（方案设计）的产出记录。

## 1. 数据源与热度观察（2026-11-09）

| 来源 | 观察对象 | 信号 |
| --- | --- | --- |
| GitHub Trending 日榜 | `anthropics/skills`、`vercel-labs/agent-browser`、`ranxianglei/billion-context` | Agent 工具链与「可靠上下文」主题集中爆发 |
| GitHub Trending Python 周榜 | `NVIDIA/auto-ontology`、`github/spec-kit`、`Graphify-Labs/graphify` | 结构化/可校验上下文、规范驱动文档 |
| 技术社区热议 | Agent Skills 多仓库爆发 | 文档作为 Agent 输入，其**一致性**成为工程问题 |

共性原则：大家都在解决「给 AI / 读者一份可信、可验证、结构化的文档上下文」。

## 2. 硬性排除规则执行结果

按流程要求，先拉取目标账号下**全部已存在仓库清单**做相似度校验：

- 拉取仓库总数：**1766**（分页 `GET /user/repos`，`per_page=100`）
- 语言分布：Python 1302、TypeScript 78、JavaScript 69、Go 24、Rust 11 等
- 高频主题：`cli` 976、`lightweight` 967、`zero-dependency` 744、`engine` 890

**一票否决命中**：`上下文压缩 / Token 优化`方向已有 **50+ 个**高度相似仓库
（`ContextSqueeze`、`TokenCrunch`、`SmartContext`、`TokenSlim`、`ContextForge` …），
相似度远超 60%，直接跳过。同理排除了 `readmelint`（单篇 README 评分）、
`I18nForge`（多语 README 生成）、`mdforge-pro`（单文档格式化）、
`PlanAnchor`（计划文件与代码漂移）、`SkillAudit`（SKILL.md 规范）等近似定位。

**空白维度确认**：`多语言文档一致性一致性校验 / 翻译漂移` 在账号内命中 0 个；
GitHub 全局同名仓库检索中 `DocConcord` 命中 0 个。

## 3. 锁定目标与差异化方向

| 项 | 结论 |
| --- | --- |
| 项目名 | **DocConcord** |
| 定位 | 零依赖、离线优先的多语言文档一致性契约校验引擎（Python 库 + CLI） |
| 对比对象 | **一组**译文文档，而非单篇文档（与既有 linter/生成器根本不同） |
| 技术栈 | Python 3.9+ 标准库（`dataclasses` / `argparse` / `unittest`），无第三方运行时依赖 |
| 可落地性 | 单仓库可完整实现，跨平台，无需外部服务或模型 |
| 原创性 | 100% 独立自研；仅参考上述项目的**产品逻辑与痛点**，不复制任何代码 |

差异化亮点：按标题序号或别名表对齐章节、比对代码块/表格/命令形状、
体检锚点与链接集合、拦截危险示例命令与硬编码凭据、默认离线且确定性、
输出 4 种 CI 可消费报告、提供可审阅的 diff 补丁。

## 4. 自测规划（第三步前置）

- 解析器：标题/围栏/表格/链接/锚点/路径穿越防护，共 8 组用例
- 规则：18 条规则的触发与对照，含别名表、豁免、危险命令、硬编码凭据
- 报告：JSON 可解析、JUnit 为合法 XML、文本/表格渲染、门禁退出码
- CLI：`version` / `rules` / `scan` / `check` / `fix` 全流程
- 工程：wheel + sdist 构建、三语 README 自审零 error、`selftest.sh` 一键闭环

## 5. 风险与规避

| 风险 | 规避措施 |
| --- | --- |
| 解析完整 CommonMark 复杂度失控 | 只实现审计所需构造，明确声明非完整实现 |
| 在线探测带来不确定性 | 默认关闭，仅 `--online` 显式启用 |
| 读取审计目录之外的文件 | `safe_resolve` 用 `realpath` 做根目录边界校验 |
| 文档示例泄露真实凭据 | X002 规则主动拦截并提示轮换 |
| 多语 README 自身漂移 | 共享模板生成 + CI 自审门禁 |
