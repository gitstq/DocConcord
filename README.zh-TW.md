# 🧭 DocConcord · 多語文件一致性契約校驗引擎

> 🌐 语言 / Languages: [简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

一份 README 寫成三種語言，最怕的從來不是翻得不夠漂亮，而是**某個版本悄悄改漏了**。DocConcord 把「各語言版本的結構是否還對得上」變成一條可以放進 CI 的確定性檢查。

**零依賴** · **離線優先** · **確定性輸出** · **CI 門檻就緒** · Python >= 3.9

## 1. 🎉 專案介紹

DocConcord 是一個以純標準庫實作的 Python 套件 + 命令列工具，專門稽核**同一份文件的多語版本**之間的結構漂移。它不翻譯、不改寫內文，只回答一個問題：簡體中文、繁體中文與 English 三份 README，是否仍是同一份文件？

**實際痛點 / 真實痛點:**

- 🧩 英文版加了一節「疑難排解」，中文版還停在舊結構，讀者照著做卻對不上步驟
- 🔗 安裝指令、參數表、外部連結在某個語言版本裡悄悄缺失，等使用者提 Issue 才發現
- 🧪 人工逐行對照三份文件成本太高，CI 裡又缺一個能直接給結束碼的檢查

市面上多數工具替**單篇** README 評分，翻譯工具負責**產生**譯文；DocConcord 補的是中間那一環 —— 產生之後的**一致性契約校驗**，並給出可逐行審閱的修補檔。比對對象是「一組文件」，不是「一篇文章」，這是它最根本的差異。

靈感來自本週 GitHub Trending 上 Agent Skills、文件上下文可靠性相關專案的集中爆發。在鎖定方向前，我們針對目標帳號下 **1766 個既有儲存庫**做了功能定位與技術堆疊的相似度校驗：「上下文壓縮 / Token 最佳化」已有 50+ 個高度重複專案，依一票否決規則直接略過；最終選擇「多語文件一致性」這個空白維度，程式碼 100% 獨立自研，僅參考其產品邏輯與痛點。

## 2. ✨ 核心特性

- 🔍 **跨語言結構對齊**：依標題序號或別名表比對章節數量、層級與順序
- 🧱 **內容形狀校驗**：程式碼區塊數量與語言標記、表格行列、可複製指令逐條比對
- 🔗 **連結與錨點健檢**：本機路徑、跨檔案錨點、外部連結集合差異一次查清
- 🛡️ **文件安全哨兵**：攔截危險範例指令與疑似硬編碼憑證，避免真實金鑰被寫進公開文件
- 📤 **四種報告格式**：text / json / markdown / junit，結束碼可直接作為 CI 門檻
- 🩹 **可審閱的自動修復**：預設只輸出 unified diff，`--apply` 才會真正寫回

| 規則族 | 編號 | 覆蓋內容 |
| --- | --- | --- |
| 結構 S | S001–S004 | 章節缺失、層級、順序 |
| 內容 B | B001–B007 | 程式碼區塊、表格、指令 |
| 連結 L | L001–L005 | 外鏈集合、錨點、路徑 |
| 安全 X | X001–X002 | 危險指令、硬編碼憑證 |

## 3. 🚀 快速開始

環境要求極簡：Python **3.9 以上**，**零第三方執行期依賴**，Windows / macOS / Linux 皆可直接使用。複製儲存庫後不必建立虛擬環境也能啟動。

安裝（也可以直接用 `python -m docconcord`，不需安裝）：

```bash
python -m pip install .
python -m docconcord --version
python -m docconcord rules
```

三道指令完成第一次健檢：`scan` 看發現了哪些語言版本，`check` 產出報告，`--format json` 方便機器讀取。

```bash
python -m docconcord scan .
python -m docconcord check . --format text
python -m docconcord check . --format json --fail-on warning
```

結構完全對齊時的輸出大致如下（`Gate: PASS` 代表門檻通過）：

```text
DocConcord v1.0.0 - Multilingual documentation parity audit
Documents: 3   Families: 1   Findings: 0
Parity score: 100 / 100   Gate: PASS
```

## 4. 📖 詳細使用指南

| 參數 | 作用 | 預設值 |
| --- | --- | --- |
| `--base` | 指定基準文件檔名或相對路徑 | 自動選擇 |
| `--format` | 報告格式 text / json / markdown / junit | text |
| `--fail-on` | 門檻閾值 error / warning / info / never | error |
| `--online` | 啟用外鏈線上探測（預設完全離線） | 關閉 |

把 `.docconcord.json` 放在儲存庫根目錄即可生效，命令列參數優先級更高。`aliases` 是選用的標題別名表，`disabled_rules` 用於明確豁免特定規則：

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

進階用法：別名表把不同語言的標題映射到同一個 canonical key，因此「缺少章節」能被精確點名，而不只是按第 N 個標題告警；`fix` 只做兩件保守的事 —— 補上語言切換導覽、替未標記的程式碼區塊補語言標記。

```bash
python -m docconcord check . --aliases docs/aliases.example.json --format markdown
python -m docconcord fix .
python -m docconcord fix . --apply
```

**典型使用情境:**

- 📌 開源專案維護多語 README，每次發版前跑一次門檻
- 📌 譯文由人工或 AI 產生後，用一致性報告作為驗收清單
- 📌 CI 中輸出 JUnit XML，讓 PR 頁面直接顯示失敗項目

> 🎬 示範動圖預留：`docs/assets/demo.gif` 將於後續版本補上；目前版本以上方 CLI 輸出範例為準。

## 5. 💡 設計思路與迭代規劃

整個引擎圍繞三條原則設計，任何新增規則都必須同時滿足：

- **確定性**：相同輸入永遠產出位元組一致的報告，發現項與檔案清單皆排序後才渲染
- **唯讀優先**：預設不連網、不執行文件內任何指令、不寫檔，唯一寫入動作是 `fix --apply`
- **零依賴**：解析器、規則、報告、CLI 全數基於標準庫，裝好即用，沒有供應鏈負擔

技術選型採用 `dataclasses` 建模、`argparse` 實作 CLI、`unittest` 撰寫測試。Markdown 解析器只涵蓋稽核真正需要的構造（標題、圍欄程式碼區塊、管道表格、連結、錨點），刻意不做完整 CommonMark —— 換來的是行為可預測、跨平台一致，以及極小的稽核面。

**迭代規劃:**

- 🗺️ 更完整的語言標籤辨識與 RTL 文件支援
- 🗺️ SARIF 輸出，串接 GitHub Code Scanning
- 🗺️ 官方 GitHub Action 封裝與更細緻的規則級設定

社群貢獻方向集中在三處：新增規則、補齊語言標籤、改進報告渲染器。詳見 [貢獻指南](CONTRIBUTING.md) 與 [架構設計](docs/ARCHITECTURE.md)。

## 6. 📦 打包與部署指南

本專案屬於**工具庫 / CLI 類**專案，依發布規範無須產生 Windows、macOS、Linux 三平台可執行檔；交付形態是原始碼儲存庫加上 wheel / sdist 建置產物，跨平台相容性由 Python 直譯器本身保證，不存在平台專屬的打包陷阱。

一鍵建置、安裝產物、產生 CI 報告：

```bash
bash scripts/build.sh
python -m pip install dist/docconcord-1.0.0-py3-none-any.whl
python -m docconcord check . --format junit --output docconcord.xml
```

在任一 CI 加一步即可（Windows 用 `scripts/build.ps1`，其餘平台用 `scripts/build.sh`）：

```yaml
- name: Audit multilingual docs
  run: python -m docconcord check . --format junit --output docconcord.xml
```

- ✅ 相容環境：Python 3.9 / 3.10 / 3.11 / 3.12 / 3.13
- ✅ 字元編碼：全程 UTF-8，正確處理簡體、繁體、日文與 emoji 標題
- ✅ 路徑安全：本機連結解析限制在稽核根目錄內，越界路徑直接忽略

## 7. 🤝 貢獻指南

歡迎提 PR 或 Issue。提交訊息遵循 Angular 規範（`feat:` / `fix:` / `docs:` / `test:` / `refactor:`），新增規則請同時補上單元測試，並在 [規則清單](docs/RULES.md) 登記編號。Issue 請附上最小可重現的文件片段與期望行為。

本機開發閉環：

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m docconcord check . --fail-on error
```

## 8. 📄 開源協定說明

本專案採用 **MIT 開源協定**：允許商業使用、修改、散布與再授權，唯一要求是在副本中保留版權聲明與授權聲明。完整條文見 [開源協定](LICENSE)。

協定全文也可在 [MIT 協定官網](https://opensource.org/license/mit) 查閱。版本變更記錄於 [更新日誌](CHANGELOG.md)，問題回報請走 [提交 Issue](https://github.com/gitstq/DocConcord/issues)。

工程文件：[架構設計](docs/ARCHITECTURE.md) · [規則清單](docs/RULES.md) · [環境與設定](docs/ENVIRONMENT.md) · [貢獻指南](CONTRIBUTING.md) · [更新日誌](CHANGELOG.md) · [開源協定](LICENSE)

致謝 [GitHub 儲存庫](https://github.com/gitstq/DocConcord) 主頁與 [Python 官網](https://www.python.org/downloads/) 提供的生態基礎；本工具不蒐集任何資料，也不上傳被稽核文件的內容。

[GitHub 儲存庫](https://github.com/gitstq/DocConcord) · [Python 官網](https://www.python.org/downloads/) · [MIT 協定](https://opensource.org/license/mit) · [提交 Issue](https://github.com/gitstq/DocConcord/issues) · [更新日誌](https://github.com/gitstq/DocConcord/blob/main/CHANGELOG.md)

