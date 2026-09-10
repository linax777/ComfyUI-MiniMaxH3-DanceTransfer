# ComfyUI MiniMax H3 舞蹈動作遷移與人物替換

繁體中文 · [English](README.md)

這是一組為 ComfyUI 原生 **MiniMax H3 Reference to Video** 工作流程設計的舞蹈與表演動作遷移節點。本 fork 的目標是保留原始 RGB 表演影片的舞步、節奏、肢體動作與運鏡，同時替換表演者，並維持多段生成時的人物、服裝、背景與光線一致性。

## 專案目標

本專案將兩種不應互相競爭的 conditioning 責任分開：

```text
原始舞蹈 RGB 片段 ──> 舞步、時間、姿勢與運鏡
前一段生成尾端 ──> 人物、服裝、背景、光線與接縫連續性
```

原始來源區間始終是主要動作參考。前一段的生成上下文只用來穩定下一段開頭，並可以逐漸淡出，不會取代或覆蓋原始舞蹈動作。

預設請求的續接上下文為 **24 fps 下的 24 個 RGB 影格**，執行時會對齊 MiniMax H3 合法的時間網格。第一版明確以 RGB 為主，不加入 Depth 或 DWPose conditioning。

## 本 fork 新增的能力

- 以動作還原為優先的舞蹈與表演遷移，原始 RGB 維持為權威動作參考。
- 獨立的 Dance Continuation 控制，可設定生成尾端上下文、淡出、強度與選用實驗噪聲。
- 直接 AV Latent 續接，避免每段之間的 RGB decode/re-encode 往返。
- 自適應 Drift-Control 遮罩，保護接縫側 latent，並逐步釋放可替換的前綴。
- Soft AV 音訊續接，降低跨段音訊轉場的突兀感。
- 長參考自動分段，適用於人物替換與長篇對嘴。
- H3 時間網格對齊、重疊移除與最終長度精確裁切。
- 集中編輯影片、影片原音、Guide、圖片與獨立音訊的緊湊時間軸。
- 採用獨立的 `MiniMaxH3Dance*` namespace，可與上游 Timeline Director 同時安裝。

## 建議工作流程

1. 在 **MiniMax H3 Dance 素材規劃台** 載入一段 RGB 舞蹈或表演影片。
2. 需要替換表演者時，將影片用途設為「可編輯參考」。「固定 Guide」會錨定原始像素，通常會阻礙人物替換。
3. 加入身分圖片；需要時再加入獨立的長音訊。
4. 完整來源表演建議使用 **MiniMax H3 Dance 長參考自動分段**；手動規劃長序列時可使用 **MiniMax H3 Dance 有限分段展開**。
5. 將規劃連接到 **MiniMax H3 Dance 有限分段採樣**；需要跨段人物穩定性時，開啟 Dance Continuation。
6. 先以預設 24 影格上下文與 baseline 比較；只有在生成上下文開始抑制新動作時，才調整淡出。

可先使用 [Dance Transfer A/B 基準測試工作流程](example_workflows/H3_DanceTransfer_AB_Test.json) 進行受控比較。

## 生成範例

以下兩個約一分鐘範例均由外掛在單次執行中生成，成品為 `52.625 秒 / 1263 影格 / 24 fps`。歷史媒體檔案繼續由上游 GitHub Release 提供，不會增加 clone 的體積。

| 直接 Latent 續接 | 參考素材＋請求 48 影格重疊 |
| --- | --- |
| [![播放直接 Latent 範例](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/case-finite-segments-60s.webp)](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/H3_finite_segments_60s.mp4) | [![播放參考重疊範例](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/case-reference-overlap-60s.webp)](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/H3_reference_overlap48_60s.mp4) |

## 安裝

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/linax777/ComfyUI-MiniMaxH3-DanceTransfer.git
```

重新啟動 ComfyUI，並搜尋 `MiniMax H3 Dance`。

### 環境需求

- 較新版本的 ComfyUI，並包含原生 MiniMax H3 節點。
- 使用固定 Guide conditioning 時需要 `MiniMaxH3AddGuide`。
- MiniMax H3 Ref2VA 模型、CLIP、影片 VAE 與音訊 VAE。
- Python 3.10 或更新版本。
- 使用低解析度預覽代理時，需要 ComfyUI 環境中的 `imageio-ffmpeg`。

外掛不另外宣告 pip 依賴，會使用相容 ComfyUI 安裝通常已提供的 PyAV、Pillow、NumPy、PyTorch、torchaudio、aiohttp 與 imageio-ffmpeg。

## 內含節點

| 節點 | 用途 |
| --- | --- |
| **MiniMax H3 Dance 素材規劃台** | 編輯參考素材，並產生 H3 規劃與已排序的 Omni 素材包。 |
| **MiniMax H3 Dance Omni 素材包提示詞橋** | 將已排序素材送往已安裝的 Prompt Rewriter Omni 後端。 |
| **MiniMax H3 Dance 規劃編碼器** | 將規劃、提示詞、CLIP 與 VAE 轉換為 H3 conditioning 與 latent 輸出。 |
| **MiniMax H3 Dance 長參考自動分段** | 將完整表演與同步音訊切成對齊來源時間的生成視窗。 |
| **MiniMax H3 Dance 有限分段展開** | 建立不含採樣的輕量化有限長影片規劃。 |
| **MiniMax H3 Dance 有限分段採樣** | 展開直接 Latent 續接、遮罩、採樣、重疊移除與合併執行圖。 |
| **MiniMax H3 Dance 時間軸導演台** | 提供一體化的時間軸規劃與編碼介面。 |

拆分式規劃可以避免 ComfyUI 依賴循環：

```text
素材規劃台 ──Omni 素材包──> Omni 素材包提示詞橋 ──rewritten_prompt──> 規劃編碼器
     └────────────────────── H3 規劃 ──────────────────────> 規劃編碼器
```

## 內含工作流程

- [Dance Transfer A/B 基準測試](example_workflows/H3_DanceTransfer_AB_Test.json)：比較受保護的 RGB baseline 與 Dance Continuation。
- [長影片動作遷移、人物替換與數位人](example_workflows/MinimaxH3长视频动作迁移人物替换+长视频数字人工作流.json)：自動切分一段原始表演與選用長音訊。
- [有限直接 Latent 續接](example_workflows/MiniMax时间线插件内置有限分段工作流.json)：不依賴通用 Loop 節點，建立有限無環分段執行圖。
- [基礎時間軸工作流程](example_workflows/MiniMax_H3基础时间线规划工作流.json)：使用一體化 Dance 時間軸導演台。
- [拆分式素材規劃與編碼](example_workflows/MiniMax_H3时间线规划拆分节点工作流.json)：將素材規劃與 H3 編碼分開。
- [素材規劃與提示詞擴寫](example_workflows/MiniMax_H3时间规划+Prompt提示词生成.json)：整合 [MiniMax-H3-Prompt-Rewriter-ComfyUI](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI)。

## Dance Continuation 調整建議

- 將原始 RGB 片段與前一段生成尾端視為兩種不同輸入，並讓它們各自負責動作與連續性。
- 開啟 Dance Continuation 時，不要將所有來源影片全部改為固定 Guide。
- 請求 24 影格上下文時，實際重疊可能因 MiniMax H3 合法時間網格而對齊為較小數值；續接、裁切與合併會共用同一個對齊結果。
- 生成上下文能維持人物，但抑制分段邊界的新動作時，可開啟淡出。
- 每個分段都使用採樣節點畫面上顯示的同一種子。
- `timeline_data` 繼續相容；namespace 更名前儲存的工作流程只需遷移節點類型。

完整對照請參考[節點 namespace 遷移指南](docs/NODE_NAMESPACE_MIGRATION.md)。

## 適用範圍與限制

- 主要目標是單人舞蹈或表演動作遷移，並替換人物與背景。
- 動作還原度的優先順序高於單段最大長度。
- 取景清楚、肢體可見、影格率穩定與來源光線一致會有較好的結果。
- 多人遮擋、突然剪接、極端運鏡與來源壓縮品質不佳仍是困難情境。
- 第一版以 RGB 動作遷移為 baseline，Depth 與 DWPose 明確不在本版範圍。
- 生成尾端續接可改善一致性，但無法保證每個鏡頭都完美保留身分或無縫轉場。
- 發佈版本 tag 前，應在完整 ComfyUI 環境中進行真實模型驗收。

## 技術參考與歸屬

- 本 fork 以上游 [ComfyUI-MiniMaxH3-TimelineDirector](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector) 的 `e4d6d5e` baseline 為基礎。
- Drift-Control AV 改作自 GPL-3.0 專案 [ComfyUI-MiniMaxH3-Contex-Loop](https://github.com/ethanfel/ComfyUI-MiniMaxH3-Contex-Loop)。
- Omni 提示詞橋與相關工作流程參考 [MiniMax-H3-Prompt-Rewriter-ComfyUI](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI)。
- 官方模型與提示詞指南：[MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3)。

## 授權

[GPL-3.0](LICENSE)
