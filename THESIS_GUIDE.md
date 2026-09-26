# Thesis Guide

本指南供作者、指導教授與協作 AI 使用。先定義生醫問題、資料與可驗證主張，再決定模型。模板中的章節提示是寫作問題；沒有預先假定樣本數、IRB 核准、實驗結果或臨床效益。

## Writing workflow

所有學術文字採用使用者指定的 **John M. Swales and Christine B. Feak, _Academic Writing for Graduate Students: Essential Tasks and Skills_, 3rd ed.** 原則。先定 audience、purpose、strategy 與 scholarly positioning，再寫內容；期刊慣例可細化表達，但不取代這套修辭與證據要求。

| 審閱面向 | 執行方式 |
|---|---|
| Content → organization → flow → grammar | 先查證內容與論證順序，再用 old-to-new information flow 串接句子，最後修文法。 |
| Introduction／CARS | 建立研究領域 → 建立 gap／niche → 說明本研究的問題、目的與貢獻。 |
| Literature synthesis | 按問題、資料／方法、矛盾與缺口比較多篇來源，避免逐篇摘要串接。 |
| Results／data commentary | 圖表定位／summary → 核心比較或 highlighting statement → 解釋、例外及不確定性；不僅重報數字。 |
| Claim strength | 用詞強度依實際證據決定；本研究的關聯不可改寫為因果或臨床效益。 |
| Methods／disciplinary style | 主被動語態依程序焦點及學科慣例選擇，不使用一律改主動的規則。 |
| Source audit | 核對引文與原文，保留閱讀範圍與不確定性；不虛構 citation、書頁或逐字引文。 |

Paper 以期刊讀者為對象，thesis 以指導教授、口試委員與領域研究者為對象；可共用結果與來源，但背景深度、文字與組織分開處理。禁止 generic academic filler、只為顯得艱深而改寫，以及沒有新證據卻提高主張強度。下列原有工作流程仍適用：

1. **界定問題。** 寫清目標族群、使用者、臨床／生物學決策、預測時點、輸入、輸出、基準方法與主要終點。
2. **確認資料。** 記錄來源、版本、權限、納入排除、標籤定義、缺失值、重複個體、時間與院所界線。研究倫理／IRB、資料授權與同意範圍只寫已確認事項。
3. **固定評估方案。** 先定義資料切分、主要指標、比較方法、統計單位與選模流程；測試集不得用於調參。不同研究問題可採不同方案，須說明理由。
4. **完成可追溯的結果。** 每張表與圖連到實驗設定、程式版本及輸出來源。文獻結論、研究假設、已執行分析與未來工作分開表述。
5. **核對全文。** 正文、摘要、表圖、附錄與口試簡報的樣本數、指標、主要結論保持一致；再檢查版面與提交格式。

## 研究進度更新

目前研究主線與範圍見 [研究架構](docs/RESEARCH_ARCHITECTURE.md)。唯一狀態來源是根目錄 `research_progress.json`，圖與文字表由它產生：

| 檔案 | 角色 |
|---|---|
| `research_progress.json` | 手動維護的狀態、證據、目前焦點、短期計畫、決策點、里程碑與日期。 |
| `scripts/render_research_progress.py` | 驗證資料、產生 PNG 與文字表、檢查產生檔是否過期。 |
| `docs/research_progress.png` | README、研究架構與章節架構共同引用的固定圖片。 |
| `docs/RESEARCH_PROGRESS.md` | 同步產生的完整文字表與證據紀錄；適合搜尋、審查與輔助閱讀。 |
| `.github/workflows/research-progress.yml` | push／PR 時驗證資料與圖片同步；不自動提交、不更改研究狀態。 |

首次設定（Python 3.10 或更新版本）：

```sh
python3 -m venv .venv-progress
.venv-progress/bin/python -m pip install -r scripts/requirements-progress.txt
```

日常更新：

1. 先確認實際完成了什麼，新增證據來源。來源的 `type` 區分 `user_confirmed`、`reported_unverified`、`artifact_verified` 與 `planning_context`；規劃不能當作完成證據。
2. 修改階段的 `status`、`summary`、`evidence` 與適用的 `artifacts`。`evidence` 放來源 ID，`artifacts` 放可分享的產出路徑或識別碼；受限資料只記錄去識別的版本／受控位置，不複製資料。
3. 更新 `current_stage.id`、`focus` 與 `next_action`，並同步 `short_term_plan`、`decision_points`、`milestones`、`timeline` 與 `updated_at`。階段可平行或返回重做，不以階段數算完成百分比。`current_stage` 是目前工作焦點，可以指向尚待開始的計畫。
4. 重繪並查核：

```sh
.venv-progress/bin/python scripts/render_research_progress.py
.venv-progress/bin/python scripts/render_research_progress.py --check
```

5. 開啟圖片及三份引用文件，確認日期、文字及狀態正確，再一起提交 JSON、PNG 與文字表。只改 JSON 而未重繪時，`--check` 與 CI 會失敗並提示重新產生。

| `status` | 使用條件 |
|---|---|
| `planned` | 尚未執行；計畫已排期並不代表進行中。 |
| `in_progress` | 已開始，但完成條件尚未全部滿足；具體進展寫在摘要／證據。 |
| `reported_complete` | 使用者已確認或歷史摘要已回報完成，尚未查核實際產出。 |
| `verified_complete` | 對應產出已實際核對，記錄 `artifact_verified` 來源、檔案／執行版本及查核範圍。 |
| `blocked` | 有明確阻礙；在摘要與下一步說明依賴條件。 |

每個階段有 `acceptance` 完成條件；完成一個子任務不等於整階段完成。更新里程碑或每週工作時，也要逐項判斷其交付內容，不能只因關聯階段完成就直接標記完成。

變更資料結構／繪圖器時，另外執行：

```sh
.venv-progress/bin/python -m unittest discover -s tests -p 'test_research_progress.py'
```

繪圖器從自己的檔案位置解析專案根目錄，可在其他工作目錄執行。測試或替代預覽可用 `--source /path/to/progress.json --output-dir /path/to/preview`。使用 repository 既有字型，無需病人資料、API、GPU 或網路即可重繪；修改字型或繪圖器後也要重新產圖並查核。

`deadline.date` 的 12/15 是沿用先前規劃的十二月中研究交付錨點；確切交付形式寫在 `deadline.note`。如使用者或指導教授修訂，先修改來源及受影響的里程碑／時程再重繪。Q1 投稿、口試、碩論送審和畢業各自需要事件證據及日期，不能從研究交付日推定。查期刊分區時記錄當年度 **JCR** 類別／分區及來源，不將 **SJR** 當成同一項。

圖不是研究完成證明。初始狀態依歷史回報和使用者對 v1 的確認建立；實驗結果尚未在本次核實，模板已完成也只代表寫作骨架存在。

## Editing boundaries

日常寫作可改 `contents/chapter01.tex` 至 `chapter04.tex`、`front/abstract.tex`、`front/acknowledgement.tex`、`front/denotation.tex`、`back/appendix01.tex` 與 `back/references.bib`。`ntusetup.tex` 只能填寫使用者提供或明確核實的論文資料與選項；不知道的保留空白。

正文採四章：Introduction、Materials and Methods、Results and Discussion、Conclusion。文獻與問題背景放第一章，資料、方法及評估方案放第二章，結果與對應解釋放第三章，第四章整理有證據支持的結論。詳細對應見 [章節架構](docs/THESIS_STRUCTURE.md)；不因合併章節而省略資料切分、統計方法、研究限制或與既有研究的比較。參考版中的研究主題、工具、樣本數與成果不自動成為本論文的內容。

**AI 不得因為改寫正文而自行改動排版層**：`bebi-thesis.cls`、入口文件、頁面邊界、字型、行距、封面、頁碼、前置頁順序、浮水印／DOI 或定稿檢查。若任務明確授權模板維護，可以在該範圍內修改，並說明依據與驗證結果。本次建立 BEBI 模板及修正格式已獲授權。

保留 `LICENSE` 與上游來源。舊版 `ntuthesis.cls` 留作來源參照，目前文件不載入；目前排版行為以 `bebi-thesis.cls` 為準。

## Content rules

- `\thesisplaceholder{...}`：尚未撰寫的段落；`\todomark{...}`：須追蹤的修改事項。兩者在草稿可見，在定稿會報錯。完成內容後才移除，不能靠隱藏待辦產生看似完成的文件。
- 每一項研究結果須有實際分析輸出；沒有執行過的實驗用未來式或待驗證標記，不能寫成已證實。
- 引文須核對作者、題名、年份、來源與 DOI／URL，以及原文是否支持該主張。只讀摘要時應註明閱讀範圍；不能假裝讀過全文。
- 不以不存在的 citation key、示範論文或隨機 DOI 填滿文獻。`back/references.bib` 起始為空，註解範例不會生成文獻。
- 外部效度、因果關係、臨床效益、模型安全性與法規資格不能由單一離線指標直接推論。
- 對不適用的章節，在討論後明確說明理由並調整骨架；不要發明資料補齊標題。

## Data and reproducibility

本 repository 是可分享的模板。**病人可識別資料、醫療紀錄、原始受限資料、金鑰、帳號及簽名頁不得提交至公開 repository。** 正式研究素材存於機構批准的儲存空間；文稿只使用取得授權且完成必要去識別的內容。把審定書放在本地的 `front/verification.pdf`，先確認忽略規則生效再提交其他檔案。

可重現性記錄至少包含資料版本／處理流程、資料切分單位、隨機種子、套件環境、訓練設定、模型選擇、評估腳本、計算資源及輸出位置。原始資料不能公開時，記錄可提供的程式、合成範例、申請流程與限制；不要承諾未經授權的開放資料。

## Before final

依 [NTU Compliance](docs/NTU_COMPLIANCE.md) 檢查題目與姓名、雙語摘要與關鍵詞、審定書、目次和頁碼、浮水印與 DOI、PDF 保全、圖表可讀性，以及 BEBI 當期流程。`final.tex` 的成功編譯只是部分技術檢查，不能替代來源稽核、指導教授同意或圖書館格式審查。
