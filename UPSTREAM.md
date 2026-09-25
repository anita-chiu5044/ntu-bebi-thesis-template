# Upstream and attribution

本專案改作自 [NTU-NCS-lab/NTU-Thesis-Writing-Template](https://github.com/NTU-NCS-lab/NTU-Thesis-Writing-Template)。本次改作基準為 commit [849a64b3dc23936d2ef4924267ff8a838af8478f](https://github.com/NTU-NCS-lab/NTU-Thesis-Writing-Template/commit/849a64b3dc23936d2ef4924267ff8a838af8478f)。

上游 README 指明其原始來源為 [Hsins/NTU-Thesis-LaTeX-Template](https://github.com/Hsins/NTU-Thesis-LaTeX-Template)。原始 [LICENSE](LICENSE) 的 MIT 授權文字及 Copyright (c) 2017 Hsin-Hsiang Peng 保持不變。

## BEBI adaptation

- 將預設系所改為生醫電子與資訊學研究所，保留電機資訊學院中英文名稱。
- 新增 bebi-thesis.cls 與草稿／定稿入口；目前主文件不使用 NCS 品牌與樣式預設。
- 整理前置頁、羅馬頁碼、目次、審定書選項、英文正文行距、定稿黑色文字，以及浮水印／DOI 需求。
- 用 Biomedical ML 的八章寫作骨架取代示範正文，移除示範作者與示範書目作為預設內容。
- 新增寫作指南、Thesis Lab 協作規則及可追溯的官方格式檢查文件。
- 移除 NCS 專屬 class、submodule 與未使用的範例；完整上游歷史仍保存在 Git。舊版 ntuthesis.cls 原樣保留作為來源參照，目前不載入。

本版並未獲 NTU 或 NCS Lab 官方認可。

MIT 授權適用範圍依原始授權而定。臺大標誌／浮水印、字型及第三方素材的權利依各自來源處理；不得把模板的 MIT 授權當作所有附帶素材的再授權。未新增或推定第三方素材授權。

格式依據見 [NTU_COMPLIANCE.md](docs/NTU_COMPLIANCE.md)。後續同步上游時應逐項審查差異，避免把舊示範資料、NCS 樣式或不合適的預設設定重新引入本版。
