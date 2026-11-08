# 🧭 DocConcord · 多语言文档一致性契约校验引擎

> 🌐 语言 / Languages: [简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

一份 README 写成三种语言，最怕的从来不是翻译得不够漂亮，而是**某一版悄悄改漏了**。DocConcord 把「各语言版本的结构是否还对得上」变成一条可以放进 CI 的确定性检查。

**零依赖** · **离线优先** · **确定性输出** · **CI 门禁就绪** · Python >= 3.9

## 1. 🎉 项目介绍

DocConcord 是一个纯标准库实现的 Python 库 + 命令行工具，专门审计**同一份文档的多语言版本**之间的结构漂移。它不翻译、不改写正文，只回答一个问题：简体中文、繁体中文和 English 三份 README，是否还是同一份文档？

**它解决的是这些真实痛点 / The pain it removes:**

- 🧩 英文版加了一节「故障排查」，中文版还停在旧结构，读者照着做却对不上步骤
- 🔗 安装命令、参数表、外链在某个语言版本里悄悄缺失，等用户提 Issue 才发现
- 🧪 人工逐行对照三份文档成本太高，CI 里又缺一个能直接给退出码的检查

市面上多数工具给**单篇** README 打分，翻译工具负责**生成**译文；DocConcord 补的是中间那一环 —— 生成之后的**一致性契约校验**，并给出可逐行审阅的修复补丁。对比对象是「一组文档」，不是「一篇文章」，这是它最根本的差别。

灵感来自本周 GitHub Trending 上 Agent Skills、文档上下文可靠性相关项目的集中爆发。在锁定方向前，我们对目标账号下 **1766 个已有仓库**做了功能定位与技术栈的相似度校验：「上下文压缩 / Token 优化」已有 50+ 个高度重复项目，按一票否决规则直接跳过；最终选择「多语言文档一致性」这一空白维度，代码 100% 独立自研，仅参考其产品逻辑与痛点。

## 2. ✨ 核心特性

- 🔍 **跨语言结构对齐**：按标题序号或别名表比对章节数量、层级与顺序
- 🧱 **内容形状校验**：代码块数量与语言标注、表格行列、可复制命令逐条比对
- 🔗 **链接与锚点体检**：本地路径、跨文件锚点、外链集合差异一次查清
- 🛡️ **文档安全哨兵**：拦截危险示例命令与疑似硬编码凭据，避免真实密钥被写进公开文档
- 📤 **四种报告格式**：text / json / markdown / junit，退出码可直接作为 CI 门禁
- 🩹 **可审阅的自动修复**：默认只输出 unified diff，`--apply` 才会真正写回

| 规则族 | 编号 | 覆盖内容 |
| --- | --- | --- |
| 结构 S | S001–S004 | 章节缺失、层级、顺序 |
| 内容 B | B001–B007 | 代码块、表格、命令 |
| 链接 L | L001–L005 | 外链集合、锚点、路径 |
| 安全 X | X001–X002 | 危险命令、硬编码凭据 |

## 3. 🚀 快速开始

环境要求极简：Python **3.9 及以上**，**零第三方运行时依赖**，Windows / macOS / Linux 均可直接运行。克隆仓库后无需创建虚拟环境也能启动。

安装（也可直接用 `python -m docconcord`，无需安装）：

```bash
python -m pip install .
python -m docconcord --version
python -m docconcord rules
```

三条命令完成第一次体检：`scan` 看发现了哪些语言版本，`check` 出报告，`--format json` 方便机器消费。

```bash
python -m docconcord scan .
python -m docconcord check . --format text
python -m docconcord check . --format json --fail-on warning
```

结构完全对齐时的输出大致如下（`Gate: PASS` 表示门禁通过）：

```text
DocConcord v1.0.0 - Multilingual documentation parity audit
Documents: 3   Families: 1   Findings: 0
Parity score: 100 / 100   Gate: PASS
```

## 4. 📖 详细使用指南

| 参数 | 作用 | 默认值 |
| --- | --- | --- |
| `--base` | 指定基准文档文件名或相对路径 | 自动选择 |
| `--format` | 报告格式 text / json / markdown / junit | text |
| `--fail-on` | 门禁阈值 error / warning / info / never | error |
| `--online` | 启用外链在线探测（默认完全离线） | 关闭 |

把 `.docconcord.json` 放在仓库根目录即可生效，命令行参数优先级更高。`aliases` 是可选的标题别名表，`disabled_rules` 用于显式豁免个别规则：

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

进阶用法：别名表把不同语言的标题映射到同一个 canonical key，于是「缺少章节」能被精确点名，而不只是按第 N 个标题报警；`fix` 只做两件保守的事 —— 补语言切换导航、给未标注的代码块补语言标记。

```bash
python -m docconcord check . --aliases docs/aliases.example.json --format markdown
python -m docconcord fix .
python -m docconcord fix . --apply
```

**典型使用场景:**

- 📌 开源项目维护多语言 README，每次发版前跑一次门禁
- 📌 译文由人工或 AI 生成后，用一致性报告做验收清单
- 📌 CI 中输出 JUnit XML，让 PR 页面直接显示失败项

> 🎬 演示动图占位：`docs/assets/demo.gif` 将在后续版本补充；当前版本以上方 CLI 输出示例为准。

## 5. 💡 设计思路与迭代规划

整个引擎围绕三条原则设计，任何新增规则都必须同时满足：

- **确定性**：相同输入永远产出字节一致的报告， discoveries 与 findings 全部排序后再渲染
- **只读优先**：默认不联网、不执行文档里的任何命令、不写文件，唯一写操作是 `fix --apply`
- **零依赖**：解析器、规则、报告、CLI 全部基于标准库，安装即用，没有供应链负担

技术选型上采用 `dataclasses` 建模、`argparse` 做 CLI、`unittest` 做测试。Markdown 解析器只覆盖审计真正需要的构造（标题、围栏代码块、管道表格、链接、锚点），刻意不做完整 CommonMark —— 换来的是行为可预测、跨平台一致、以及极小的审计面。

**迭代规划:**

- 🗺️ 更完整的语言标签识别与 RTL 文档支持
- 🗺️ SARIF 输出，对接 GitHub Code Scanning
- 🗺️ 官方 GitHub Action 封装与更细的规则级配置

社区贡献方向集中在三处：新增规则、补充语言标签、改进报告渲染器。详见 [贡献指南](CONTRIBUTING.md) 与 [架构设计](docs/ARCHITECTURE.md)。

## 6. 📦 打包与部署指南

本项目属于**工具库 / CLI 类**项目，按发布规范无需生成 Windows、macOS、Linux 三平台可执行二进制；交付形态是源码仓库加上 wheel / sdist 构建产物，跨平台兼容性由 Python 解释器本身保证，不存在平台专属的打包陷阱。

一键构建、安装产物、生成 CI 报告：

```bash
bash scripts/build.sh
python -m pip install dist/docconcord-1.0.0-py3-none-any.whl
python -m docconcord check . --format junit --output docconcord.xml
```

在任意 CI 里加一步即可（Windows 用 `scripts/build.ps1`，其余平台用 `scripts/build.sh`）：

```yaml
- name: Audit multilingual docs
  run: python -m docconcord check . --format junit --output docconcord.xml
```

- ✅ 兼容环境：Python 3.9 / 3.10 / 3.11 / 3.12 / 3.13
- ✅ 字符编码：全程 UTF-8，正确处理简体、繁体、日文与 emoji 标题
- ✅ 路径安全：本地链接解析限制在审计根目录内，越界路径直接忽略

## 7. 🤝 贡献指南

欢迎提 PR 或 Issue。提交信息遵循 Angular 规范（`feat:` / `fix:` / `docs:` / `test:` / `refactor:`），新增规则请同时补上单元测试，并在 [规则清单](docs/RULES.md) 中登记编号。Issue 请附上最小可复现的文档片段与期望行为。

本地开发闭环：

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m docconcord check . --fail-on error
```

## 8. 📄 开源协议说明

本项目采用 **MIT 开源协议**：允许商业使用、修改、分发与再授权，唯一要求是在副本中保留版权声明与许可声明。完整条文见 [开源协议](LICENSE)。

协议全文也可在 [MIT 协议官网](https://opensource.org/license/mit) 查阅。版本变更记录在 [更新日志](CHANGELOG.md)，问题反馈请走 [提交 Issue](https://github.com/gitstq/DocConcord/issues)。

工程文档：[架构设计](docs/ARCHITECTURE.md) · [规则清单](docs/RULES.md) · [环境与配置](docs/ENVIRONMENT.md) · [贡献指南](CONTRIBUTING.md) · [更新日志](CHANGELOG.md) · [开源协议](LICENSE)

致谢 [GitHub 仓库](https://github.com/gitstq/DocConcord) 主页与 [Python 官网](https://www.python.org/downloads/) 提供的生态基础；本工具不采集任何数据，也不上传被审计文档的内容。

[GitHub 仓库](https://github.com/gitstq/DocConcord) · [Python 官网](https://www.python.org/downloads/) · [MIT 协议](https://opensource.org/license/mit) · [提交 Issue](https://github.com/gitstq/DocConcord/issues) · [更新日志](https://github.com/gitstq/DocConcord/blob/main/CHANGELOG.md)

