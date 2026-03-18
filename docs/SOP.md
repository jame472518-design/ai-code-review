# AI Code Review — 安裝與使用 SOP

## 一、安裝

### 前置需求

| 項目 | 需求 | 確認指令 |
|------|------|----------|
| Python | 3.10 以上 | `python3 --version` |
| Git | 任意版本 | `git --version` |
| pip | 任意版本 | `pip --version` |
| Ollama（選用） | 本地 LLM 推理 | `ollama --version` |

### Step 1：安裝 ai-review

如果尚未安裝 Python 3.10+：

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip python3-venv

# macOS (Homebrew)
brew install python@3.12
```

從原始碼安裝：

```bash
# GitHub
git clone https://github.com/jame472518-design/ai-code-review.git

# 或內網 GitLab（替換為實際 URL）
# git clone https://gitlab.internal.company.com/bsp-tools/ai-code-review.git

cd ai-code-review
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

或直接安裝（不需 clone）：

```bash
pip install git+https://github.com/jame472518-design/ai-code-review.git
```

驗證：`ai-review --help`

### Step 2：設定 LLM Provider

選擇一種：

```bash
# 方案 A：本地 Ollama（推薦內網）
ai-review config set provider default ollama
ai-review config set ollama base_url http://localhost:11434
ai-review config set ollama model llama3.2
ai-review config set ollama timeout 300

# 方案 B：企業內部 LLM
ai-review config set provider default enterprise
ai-review config set enterprise base_url https://llm.internal.company.com
ai-review config set enterprise api_path /v1/chat/completions
ai-review config set enterprise model internal-codellama-70b
ai-review config set enterprise auth_type bearer
ai-review config set enterprise auth_token_env ENTERPRISE_LLM_KEY

# 方案 C：OpenAI（精確度最高，建議用 gpt-4o）
ai-review config set provider default openai
ai-review config set openai api_key_env OPENAI_API_KEY
ai-review config set openai model gpt-4o
```

驗證：`ai-review health-check`

### Step 3：初始化 Commit 模板與 Generate Prompt

```bash
# 初始化 commit message 模板（可自訂格式）
ai-review config init-template

# 初始化 AI 生成 prompt（可自訂 AI 行為）
ai-review config init-generate-prompt
```

模板與 prompt 會複製到 `~/.config/ai-code-review/`，可直接編輯：

| 檔案 | 用途 | 編輯後更新 |
|------|------|------------|
| `commit-template.txt` | Commit message 格式模板 | `ai-review config init-template --force` |
| `generate-prompt.txt` | AI 生成 commit message 的 prompt | `ai-review config init-generate-prompt --force` |

### Step 4：安裝 Hooks

```bash
ai-review hook install --template
```

這會設定 `init.templateDir`，之後新 clone 的 repo 自動帶有 hooks（放在 `.git/hooks/`）。

既有 repo 補上 hooks：

```bash
# Android repo 專案
repo forall -c 'git init'

# 或個別 repo
cd /path/to/project && git init
```

### Step 5：啟用 AI Review

Hooks 預設不啟用，需在每個 repo 設定 opt-in（存在 `.git/config`，不產生任何 repo 檔案）：

```bash
# 單一 repo
ai-review hook enable

# 指定 repo
ai-review hook enable --path /path/to/repo

# 批次啟用
ai-review hook enable --all /workspace
# 或
repo forall -c 'ai-review hook enable'
```

### Step 6（選用）：設定專案 ID

設定後 AI 自動產生的 commit message 會前綴 `[PROJECT-ID]`：

```bash
ai-review config set commit project_id "BSP-456"
```

### Step 7（選用）：調整審查副檔名

預設審查所有檔案。如需限制特定副檔名：

```bash
ai-review config set review include_extensions "c,cpp,h,hpp,java,py"
```

清除限制（回到全部審查）：

```bash
ai-review config set review include_extensions ""
```

### Step 8（選用）：新增自訂審查規則

在預設審查規則之外，追加專案特定的檢查項目：

```bash
ai-review config set review custom_rules "Also check for integer overflow, use-after-free, and double-free"
```

自訂規則會附加在預設 prompt 後面，未設定時行為與預設完全相同。

### 安裝檢查清單

- [ ] `ai-review --help` 正常顯示
- [ ] `ai-review health-check` 驗證 LLM provider 連線正常
- [ ] `ai-review config show` 確認設定正確
- [ ] `ai-review hook status` 顯示 template hooks installed
- [ ] 需要 AI review 的 repo 已執行 `ai-review hook enable`

---

## 二、日常使用

### 自動觸發（推薦）

啟用後，`git commit` 自動執行：

```
git commit
  |
  +-- 檢查 ai-review.enabled -- 未啟用則跳過
  |
  +-- [Hook 1] pre-commit: AI Code Review
  |   PASS  無嚴重問題 -- 繼續
  |   BLOCK 發現 critical/error -- 擋下 commit
  |
  +-- [Hook 2] prepare-commit-msg: Commit Message 助手（互動選單）
  |   1 Load template       - 載入模板格式
  |   2 Manual draft        - 輸入草稿 → AI 優化
  |   3 LLM interview       - AI 問你問題 → 生成
  |   4 LLM auto-generate   - AI 從 diff 自動生成（兩階段）
  |   s Skip                - 跳過，直接進編輯器
  |
  +-- 編輯器開啟 -- 確認/修改 commit message
  |
  +-- [Hook 3] commit-msg: 格式驗證
  |   PASS  格式正確 -- 顯示最終 commit message
  |   BLOCK 格式錯誤 -- 擋下 commit
  |
  +-- Commit 成功
```

`git push` 自動執行：

```
git push origin main
  |
  +-- [Hook] pre-push: AI Review 所有待推送 commits
  |   PASS  無嚴重問題 -- 繼續 push
  |   BLOCK 發現 critical/error -- 擋下 push
  |
  +-- Push 成功
```

所有 hooks 使用 `--graceful` 模式：LLM 連線失敗時只印警告，不阻擋操作。

### Commit Message 助手（選項說明）

#### 選項 1：Load template

載入 commit-template.txt 模板格式到編輯器，手動填寫。

#### 選項 2：Manual draft → AI 優化

手動輸入草稿文字（按 Enter 兩次結束），AI 根據 diff 和模板優化成正式格式。

#### 選項 3：LLM interview

AI 根據 diff 產生 3-5 個中英雙語問題，你回答後 AI 根據答案生成 commit message。適合不知道怎麼描述變更時使用。

#### 選項 4：LLM auto-generate（兩階段）

全自動，不需任何輸入：

```
Stage 1: AI 分析 diff（file stats + recent commits + diff）
         ↓ 產生結構化變更摘要
Stage 2: AI 根據摘要 + 模板生成 commit message
         ↓ 寫入編輯器供確認
```

### Commit Message 模板格式

預設模板（可自訂）：

```
["Status ex:NEW,UPDATE"]["team ex:BSP,CP,AP"]["category ex:Sensor,Wifi,APK"]["Bug number ex:JIRA-0001"]["Sku ex:NAL, or none"] short description

[IMPACT PROJECTS]

[DESCRIPTION]
1.
2.
...
[test]
1.
2.
...
```

規則：
- `["..."]` 帶引號的 bracket → 占位符，AI 會替換成實際值（如 `[NEW]`）
- `[DESCRIPTION]`、`[test]` 等不帶引號 → section 標題，原樣保留
- `[none]` 會自動移除不顯示

### Pre-push 審查

`git push` 時自動對所有待推送的 commits 執行 AI code review：

- 發現 critical/error 等級問題時擋下 push
- warning/info 等級只提示，不阻擋
- 使用 `--graceful` 模式，LLM 連線失敗時不阻擋 push

手動執行 pre-push 審查：

```bash
ai-review pre-push
```

### 手動 Code Review

```bash
git add src/main.py
ai-review                    # terminal 輸出
ai-review -v                 # debug logging（排查問題用）
ai-review --format markdown  # Markdown（貼 Issue）
ai-review --format json      # JSON（CI/CD 整合）
```

### 檢查設定與連線

```bash
ai-review config show             # 檢視所有設定
ai-review config show openai      # 檢視單一 section
ai-review health-check            # 驗證 LLM provider 連線
ai-review hook status             # 檢視 hook 安裝狀態
```

### 跳過 Hooks

```bash
git commit --no-verify -m "[HOTFIX-001] emergency fix"
```

### 啟用 / 停用 Repo

```bash
ai-review hook enable           # 啟用
ai-review hook disable          # 停用
ai-review hook enable --all /workspace   # 批次啟用
ai-review hook disable --all /workspace  # 批次停用
```

---

## 三、設定參考

設定檔：`~/.config/ai-code-review/config.toml`

```toml
[provider]
default = "ollama"

[ollama]
base_url = "http://localhost:11434"
model = "llama3.2"
timeout = 300              # HTTP timeout（秒），預設 120

[review]
include_extensions = ""    # 空 = 全部檔案（預設），或 "c,cpp,h,hpp,java"
max_diff_lines = 2000      # diff 行數上限，超過會截斷，預設 2000
custom_rules = ""          # 追加審查規則（選用）

[commit]
project_id = "BSP-456"                    # 自動前綴 [PROJECT-ID]
template_file = "~/.config/ai-code-review/commit-template.txt"
generate_prompt_file = "~/.config/ai-code-review/generate-prompt.txt"

[openai]
api_key_env = "OPENAI_API_KEY"
model = "gpt-4o"
timeout = 120

[enterprise]
base_url = "https://llm.internal.company.com"
api_path = "/v1/chat/completions"
model = "internal-codellama-70b"
auth_type = "bearer"
auth_token_env = "ENTERPRISE_LLM_KEY"
timeout = 120
```

### 審查等級

| 等級 | 說明 | 擋下 Commit |
|------|------|:-----------:|
| critical | 安全漏洞、資料洩漏 | **是** |
| error | 明顯 bug、邏輯錯誤 | **是** |
| warning | 潛在問題 | 否 |
| info | 一般建議 | 否 |

### 審查重點（自動偵測語言）

AI 根據 diff 中的檔案類型自動選擇檢查重點，**不報告**程式碼風格或命名建議：

| 語言 | 檢查項目 |
|------|----------|
| C/C++ | 記憶體洩漏、Null pointer、Race condition、Buffer overflow |
| Python | 未處理例外、注入攻擊、資源洩漏、邏輯錯誤 |
| Java | Null pointer、資源洩漏、並發問題 |
| 全語言 | Hardcoded 密碼/金鑰、明顯邏輯錯誤 |

---

## 四、常見問題

**Q: 安裝後所有 repo 都會被影響嗎？**
不會。只有執行 `ai-review hook enable` 的 repo 才會觸發 AI review。

**Q: 如何自訂 commit message 模板？**
編輯 `~/.config/ai-code-review/commit-template.txt`，或編輯原始碼後 `ai-review config init-template --force` 更新。

**Q: 如何自訂 AI 生成 commit message 的行為？**
編輯 `~/.config/ai-code-review/generate-prompt.txt`，可調整語氣、格式規則、語言等。

**Q: 誤報太多怎麼辦？**
小型模型（llama3.2:3b）可能產生誤報。建議用更大模型（70b+）或 OpenAI GPT-4o。單次跳過：`git commit --no-verify`。

**Q: 多人共用 Ollama？**
在伺服器啟動 Ollama，其他人設定：`ai-review config set ollama base_url http://192.168.1.100:11434`

**Q: 網路不穩定，LLM 呼叫常失敗？**
ai-review 內建 HTTP 重試機制（自動重試 3 次）。如果仍然失敗，可調整 timeout：`ai-review config set ollama timeout 300`。使用 `ai-review -v` 查看詳細 debug log。

**Q: diff 太大，LLM 回應很慢或超時？**
預設限制 diff 最多 2000 行。如需調整：`ai-review config set review max_diff_lines 500`。超過上限時會自動截斷並警告。

**Q: LLM 連線失敗會擋下 commit/push 嗎？**
不會。所有 hooks 使用 `--graceful` 模式，LLM 連線失敗時只印警告，不阻擋操作。格式驗證（如 commit message 格式）不受影響，仍會正常擋下。

**Q: Windows 上 hook 執行失敗？**
確認使用 Git Bash。ai-review 會自動將路徑轉為 POSIX 格式（`/c/Users/...`），確保 Git Bash 能正確執行。

**Q: 如何完全移除？**

```bash
ai-review hook uninstall --template
pip uninstall ai-code-review
rm -rf ~/.config/ai-code-review
```

---

## 五、快速安裝腳本

存為 `setup-ai-review.sh` 發給團隊：

```bash
#!/usr/bin/env bash
set -e
REPO_URL="${AI_REVIEW_REPO:-https://github.com/jame472518-design/ai-code-review.git}"
INSTALL_DIR="${HOME}/ai-code-review"

echo "=== AI Code Review Setup ==="
git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
ai-review config set provider default ollama
ai-review config set ollama base_url "${OLLAMA_URL:-http://localhost:11434}"
ai-review config set ollama model "${OLLAMA_MODEL:-llama3.2}"
ai-review config set ollama timeout 300
ai-review config init-template
ai-review config init-generate-prompt
ai-review hook install --template
echo ""
echo "=== Setup Complete ==="
echo "Enable repos: repo forall -c 'git init && ai-review hook enable'"
echo "Skip once:    git commit --no-verify"
```

```bash
# 使用（GitHub）
bash setup-ai-review.sh

# 使用（內網 GitLab）
AI_REVIEW_REPO=https://gitlab.internal.company.com/bsp-tools/ai-code-review.git bash setup-ai-review.sh

repo forall -c 'git init && ai-review hook enable'
```
