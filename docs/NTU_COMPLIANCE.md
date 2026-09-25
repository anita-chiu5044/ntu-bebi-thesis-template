# NTU Compliance

官方來源查核日：**2026-09-26**。本文件區分官方規定、模板實作與作者仍須完成的事項。模板不是臺大官方核准版本；送審前須重新查核連結與所辦公告。

## Official sources

| 來源 | 適用內容 |
|---|---|
| [2026-02-03 公文及補充附件](https://www.lib.ntu.edu.tw/doc/cl/1150009478.pdf) | 現行 112.10.20 規範、2026 退件提醒及補正後目次範例。 |
| [臺大學位論文格式規範](https://www.lib.ntu.edu.tw/doc/cl/THESISSAMPLE.pdf) | 封面、正文版面與字體；目次以 2026 補充附件為準。 |
| [電子論文提交操作手冊](https://www.lib.ntu.edu.tw/doc/cl/NTUTDR_Guide.pdf) | 電子版、浮水印、DOI、PDF 保全與上傳前檢查。 |
| [審定書與目次 FAQ](https://faq.lib.ntu.edu.tw/node/627) | 電子版選擇性附審定書及頁碼一致性。 |
| [BEBI 官方網站](https://www.bebi.ntu.edu.tw/?lang=en&page_id=854)、[EECS 系所名單](https://eecs.ntu.edu.tw/en/deps) | 正式所名與學院歸屬。 |
| [BEBI 115-1 學位考試公告](https://www.bebi.ntu.edu.tw/?p=7647)、[離校流程](https://www.bebi.ntu.edu.tw/?page_id=5314) | 審定書下載、原創性比對與所級離校程序。 |
| [圖書館繳交與離校](https://www.lib.ntu.edu.tw/node/103) | 送審當期公告及操作入口。 |

## Format mapping

| 官方規範 | 本模板對應 | 作者需確認 |
|---|---|---|
| 中英文校院系所、題目、姓名、指導教授、年月；碩士為 Master's Thesis | BEBI／EECS 名稱預設；其餘在 ntusetup.tex 填寫 | 正式名稱、學位／職稱、日期；長題目是否溢出封面 |
| 紙本順序：外封面、書名頁、審定書、選擇性謝辭、中英文摘要、目次、圖次、表次、正文、文獻、附錄、封底 | 電子與紙本以 print 選項切換；正文八章 | 印刷廠外封面、書脊、封底與裝訂 |
| 前置頁羅馬數字，正文從 1 起；目次列自己、圖次、表次 | 自動排序、編碼與列目次 | 最終 PDF 實際頁碼與連結相符 |
| 中英文摘要各最多 3 頁，各 5–7 關鍵詞 | 提供雙語環境；final 檢查關鍵詞數量 | 摘要頁數、內容及 TDR 登錄一致 |
| 正文 A4，上 3／下 2／左右 3 cm；頁碼底部置中 | 排版層設定 | 大圖、長表及橫向頁未侵入邊界 |
| 英文原則 12 pt Times New Roman、雙行間距；中文 12 pt、1.5 行距 | 英文正文骨架使用雙行間距；保留上游字型來源 | 若改為中文正文，明確維護其行距設定 |
| 黑色字體 | final 使用黑色文字、標題與連結 | 外部圖像的文字、表格及自行添加的色彩 |

順序及雙語欄位依 [2026 公文第 1–2、7 頁](https://www.lib.ntu.edu.tw/doc/cl/1150009478.pdf)；版面與字體依[格式規範第 2 頁](https://www.lib.ntu.edu.tw/doc/cl/THESISSAMPLE.pdf)。**黑色字體不等於所有圖片都須灰階**；規範允許彩色圖片。本模板不會自動重新著色匯入的影像。

## Verification letter

電子 PDF 可省略審定書；省略時不得用空白審定書占位，目次也不列入。若附上已簽署審定書，須有對應目次與該頁的羅馬頁碼。紙本必須裝訂已簽署審定書，影本可。依據：[圖書館 FAQ](https://faq.lib.ntu.edu.tw/node/627)及[操作手冊印刷頁碼 4](https://www.lib.ntu.edu.tw/doc/cl/NTUTDR_Guide.pdf)。

模板的 verification 選項一次處理插頁與目次；verificationfile 指向本地已簽署 PDF。BEBI 表單請從[當期公告](https://www.bebi.ntu.edu.tw/?p=7647)取得。模板無法驗證簽名、日期或口試程序；不要將個人簽名頁推送到公開 repository。

## Electronic and print copies

電子 PDF 只要一頁封面、無書脊；封面不能出現頁碼或 Draft／Proposal 等標記。紙本外封面應另加書脊，後接同內容書名頁。外封面不加浮水印／DOI，內頁版本加上；可參考[圖書館送審說明第 6 頁](https://www.lib.ntu.edu.tw/doc/cl/ThesisSubmission_202407.pdf)。

print 選項提供紙本排版分支，但不會生成依實體厚度決定的書脊。與印刷廠核對外封面、書名頁、審定書及內文的裝訂次序；不能把有書脊的外封面放入上傳的電子 PDF。

## Watermark and DOI

依[操作手冊印刷頁碼 5–12、18](https://www.lib.ntu.edu.tw/doc/cl/NTUTDR_Guide.pdf)：

- 每一頁電子 PDF（含封面）均需浮水印與 DOI；審定書頁可例外。
- [官方浮水印](https://www.lib.ntu.edu.tw/doc/CL/watermark.pdf)：絕對比例 50%、不透明度 50%、頁面下層；距頂與右各 2.5 cm。
- DOI：複製自己在 [TDR](https://submit.tdr.lib.ntu.edu.tw/) 分配到的實際碼，包含 doi: 前綴；12 pt、不透明度 100%、頁面下層；距底與右各 1 cm。

在 ntusetup.tex 的 DOI 欄位只填識別碼本體，不含 doi: 或網址；模板在 PDF 自動加上 doi:。final 自動啟用相關檢查與疊印；draft 不啟用。不要放入示範 DOI。逐頁檢查封面、滿版圖像及插入的 PDF；設定存在不保證最終外觀正確。

## PDF security and final review

PDF 保全需在編譯後另外完成：限制編輯、允許高解析列印及輔助工具複製，不設文件開啟密碼。儲存、關閉、重新開啟後確認權限。依[操作手冊印刷頁碼 13–18](https://www.lib.ntu.edu.tw/doc/cl/NTUTDR_Guide.pdf)。不要把權限密碼寫入論文原始檔或 Git。

提交前逐項核對：

- 題目、作者、指導教授與年月已確定；中英文摘要、關鍵詞及 TDR 欄位一致。
- 所有 placeholder／TODO 已由完成的內容取代；每一項數字、文獻、圖表來源均可追溯。
- 從封面開始逐頁看 PDF：字型、邊界、順序、羅馬及阿拉伯頁碼、目次、圖次、表次與文獻。
- 浮水印、真正的 DOI、檔案標題／作者 metadata 與 PDF 保全已確認。
- 已完成指導教授定稿同意、BEBI 原創性比對與當期所級流程。
- 圖書館已審核通過後，依實際要求處理紙本及離校。

上述部分是作者的實務檢查，不是 LaTeX 自動認證。BEBI [2026-09-07 公告](https://www.bebi.ntu.edu.tw/?p=7647)目前要求定稿進行 Turnitin 比對，總相似度 ≤10%；不能由編譯結果推定通過。正式提交時重新核對當期要求與截止日期。
