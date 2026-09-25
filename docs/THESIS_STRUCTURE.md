# Thesis structure

架構版本：2026-09-26，依使用者指定的 BEBI 參考論文目次改為四章主體。這是寫作安排，不代表已採用參考論文的研究問題、資料、演算法或結果；原始 PDF 與私人 Drive 連結不納入本 repository。

## Main chapters

| 章節 | 本章要完成的工作 | 原八章內容的去向 |
|---|---|---|
| 1. Introduction | 說明問題與動機、必要背景、相關研究及缺口、研究目標與全文安排。 | Introduction + Related Work |
| 2. Materials and Methods | 交代資料與研究設計、前處理、分析流程、模型與強基準、資料切分、評估與統計方法、實驗設定。 | Cohort and Data + Methods + Experimental Design |
| 3. Results and Discussion | 按研究問題呈現結果並給出對應解釋，包含穩健性、錯誤分析、與既有研究的比較及限制。 | Results + Discussion |
| 4. Conclusion | 回答研究問題，總結可由結果支持的貢獻，區分尚未完成的未來工作。 | Conclusion |

保留參考版的四個章名；小節用可替換的 Biomedical ML 骨架。參考版中的特定疾病、定序工具、資料增強方法與模型不是預設研究承諾。只有作者實際採用並有來源或執行紀錄的方法，才寫成已使用的方法。

## Front matter and appendices

- 封面、紙本書名頁及審定書選項沿用既有 BEBI 模板。
- 謝辭、中英文摘要、目次、圖次、表次之後接「符號與縮寫」，再進入正文。符號頁不增加章號，列入目次並沿用羅馬頁碼。
- 參考論文的 Denotation 用作符號頁的位置參考；縮寫與定義需按實際正文重新整理。
- References 放在第四章之後，附錄接在文獻之後。預設保留可重現性與補充材料附錄；其他附錄依實際研究需要增補，不先放入參考版的分析或圖表。
- 不複製參考論文的作者、指導教授、題目、DOI、摘要、正文、圖表或成果。作者欄位與研究內容仍待填寫。

## Review gates

章節合併後，第二章仍須能讓讀者重建研究與評估流程；第三章每項解釋須連到實際結果，並區分文獻證據、確認性分析、探索性分析與推測。第四章不得加入第三章未呈現的新結果。

排版依 [NTU_COMPLIANCE.md](NTU_COMPLIANCE.md)；AI 協作依 [THESIS_GUIDE.md](../THESIS_GUIDE.md) 與 [AGENTS.md](../AGENTS.md)。四章架構不改變既有字型、頁面邊界、行距、頁碼、浮水印、DOI 或 final 阻擋條件。
