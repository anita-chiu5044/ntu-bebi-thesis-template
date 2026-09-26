# Biomedical ML 研究架構

![研究流程與進度：人類基因變異 × 鼻咽菌相，從前處理、功能變異篩選、sCCA 到疾病模組及寫作交付](research_progress.png)

本圖與 [README](../README.md) 共用唯一圖片 `docs/research_progress.png`。狀態、目前焦點、短期計畫、決策點、里程碑及時程一律從 [research_progress.json](../research_progress.json) 產生；完整可讀狀態與證據見 [文字版進度](RESEARCH_PROGRESS.md)。這份文件說明研究結構，避免另外維護一份容易失同步的完成清單。

## 研究問題與分析主線

以同一批鼻咽拭子 mNGS 的人類 reads 與微生物 reads，探索**人類基因變異集合與鼻咽菌群的共同變動**，並將宿主端基因放到 interactome，分析與疾病模組的關聯。這是 Biomedical ML 的關聯研究；模型分數、canonical correlation 與網路 proximity 均須依其評估條件解釋。

| 模組 | 輸入與處理 | 產出與查核重點 |
|---|---|---|
| 宿主端 | 低覆蓋人類 reads、joint calling、QC、GLIMPSE2 imputation、KING | 基因型／dosage 矩陣、QC 與親緣紀錄；duplicate 和家系處理各自記錄。 |
| 微生物端 | Kraken2、Bracken、去污染、盛行率過濾、零值處理與 CLR 等轉換 | 微生物矩陣；保留版本、污染清單、轉換與樣本對應。 |
| 功能變異篩選 | GPN-MSA baseline；Evo2 ΔLL、EVEE 與 AlphaGenome 作候選比較 | 固定 **GPN-MSA 篩選前**的共同候選池；記錄 genome build、ref/alt、MAF 分層、score 方向、覆蓋與授權。不能把 pathogenicity 自動等同本研究功能效應。 |
| sCCA | 配對的宿主／微生物特徵、預定共變數與相依性處理 | canonical pairs、兩側 loading、實際評估輸出與可重跑設定。 |
| 驗證與選模 | permutation／留出、模擬、重抽樣穩定度、無親緣樣本與臨床分組敏感度 | 依預定方案固定主分析；樣本內相關不等於泛化或顯著性。 |
| Interactome／疾病模組 | SNP→gene 映射、PPI 網路、疾病種子集 | proximity／separation、matched null 與菌種↔疾病模組二分網路；交代網路不完整及映射不確定性。 |

v1 可先接上 interactome 開發原型；最終網路與生物學解釋須使用通過核對的主分析。進度圖的箭頭表示分析／證據依賴，排程中可平行開發。各種篩選器仍為候選，不預設必須採用全部模型。

run／深度、ancestry PCs、年齡、性別與臨床分組的角色須依研究問題確認。不得把先前提出的殘差化方法或 random effect 自動視為已採用；所有特徵篩選、調參、殘差化、切分與置換均須避免洩漏並尊重個體／家系相依性。非編碼 SNP 對基因映射要有依據，不能僅因最近基因方便就當作功能連結。

## 成果路徑與章節對應

| 成果 | 目的 | 與既有四章骨架的關係 |
|---|---|---|
| Paper | 以研究問題、可信評估及圖表建立核心論證。 | 共用證據與結果，依目標讀者另寫 manuscript。 |
| Q1 投稿準備 | 核對 scope、當年度 JCR 類別與分區、作者指引，完成共同作者審閱與投稿材料。 | 不把投稿、接受或期刊分區預先標為已完成；JCR 與 SJR 分開記錄。 |
| NTU BEBI Thesis | 完整呈現問題、資料、方法、結果、解釋與限制。 | Chapter 1：問題、文獻與 gap；Chapter 2：兩端資料、篩選、sCCA 與網路方法；Chapter 3：結果及討論；Chapter 4：有證據支持的結論。 |

十二月中是研究交付的規劃錨點，不能據此推論已確認的期刊投稿、碩論送審或口試期限。HUMAnN3 功能×宿主、罕見變異 burden 與擴大 benchmark 列為延伸範圍，是否納入以進度來源的 `deferred` 與決策紀錄為準。

## 學術寫作與維護

Paper 與 Thesis 均遵循 **Swales & Feak, _Academic Writing for Graduate Students: Essential Tasks and Skills_, 3rd ed.** 的既定原則：audience／purpose／positioning、old-to-new flow、CARS、跨來源 synthesis、證據相稱的 claim strength，以及 data commentary。詳細規則與更新步驟見 [THESIS_GUIDE.md](../THESIS_GUIDE.md)。這裡承接使用者已指定的原則，沒有新增書中逐字引文或未經核實的頁碼。

既有 [四章架構](THESIS_STRUCTURE.md)、[NTU 格式檢查](NTU_COMPLIANCE.md)、授權與排版層繼續適用。新增研究狀態時先改 JSON，再執行產圖與 `--check`；勿手改圖片或自動產生的文字版。
