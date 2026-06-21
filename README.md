# korean-subtitle-extractor

把韓文影片（YouTube 或本地檔案）自動轉換成「韓文 + 繁體中文」雙語字幕，並自動命名成可被播放器（IINA / VLC）直接讀取的格式。

## 動機

因為追星的關係，會想要看懂韓文的綜藝影片，但這類內容有時是內嵌字幕（hardcoded subtitle），沒有 CC 字幕可以直接抓取或翻譯，只能直接整段硬啃。

這個工具的目的是把「下載影片 → 語音轉文字 → 翻譯 → 對齊播放器」這個重複性流程自動化，從一支影片要硬啃或是等幾天後有人出中文翻譯，縮短成跑一個指令、等模型運算完即可。

## Demo

https://github.com/user-attachments/assets/a23be932-84cc-479c-9615-56a95ee5cfb5

## 功能

- 支援 **YouTube 連結** 與 **本地影片檔案** 兩種輸入
- 自動下載 YouTube 影片畫面，確保字幕可以對應到實際畫面
- 使用 [OpenAI Whisper](https://github.com/openai/whisper) 將韓文語音轉錄成文字字幕（本地運算，無需 API key）
- 自動翻譯成繁體中文，並產出「韓中雙語字幕」
- 每支影片自動建立獨立資料夾（依影片標題命名），重複使用不會互相覆蓋
- 自動將雙語字幕命名為與影片同名，IINA / VLC 開啟影片即可自動載入字幕，無需手動拖曳

## 安裝

```bash
# 建議使用虛擬環境
python3 -m venv venv
source venv/bin/activate

pip install yt-dlp openai-whisper deep-translator
brew install ffmpeg
```

## 使用方式

```bash
# YouTube 影片
python korean_to_srt.py "https://www.youtube.com/watch?v=xxxxx"

# YouTube Shorts
python korean_to_srt.py "https://www.youtube.com/shorts/xxxxx"

# 本地影片檔案
python korean_to_srt.py "/path/to/video.mp4"
```

執行後會在腳本所在資料夾下，依影片標題建立子資料夾：

```
korean-subtitle-extractor/
├── korean_to_srt.py
├── README.md
├── .gitignore
└── videos/                    # 已加入 .gitignore，不會上傳到 GitHub
    └── 影片標題/
        ├── video.mp4              # 影片本體
        ├── video.srt              # 雙語字幕（與影片同名，播放器自動載入）
        ├── video_bilingual.srt    # 雙語字幕（備份）
        └── video_zh.srt           # 純中文字幕
```

下載 [IINA](https://iina.io)（Mac 推薦）或使用 VLC，直接開啟 `video.mp4` 即可自動顯示雙語字幕。

## 疑難排解

字幕沒有自動載入，手動拖曳卻可以正常顯示？

如果專案資料夾放在 ~/Documents（或其他受 macOS 隱私權保護的目錄，如 Desktop、Downloads）底下，IINA 可能因為沒有被授予該資料夾的存取權限，導致「自動掃描同名字幕」這個動作被系統擋下——不會跳出任何錯誤訊息，影片依然能正常打開，只是字幕不會自動出現。

解法：到「系統設定 → 隱私權與安全性 → 檔案與資料夾」，找到 IINA，確認對應目錄（例如「文件」）的存取權限已開啟。開啟後重新打開影片即可恢復自動載入。

## 技術架構

| 步驟 | 工具 |
|------|------|
| 影片下載 | [yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| 語音轉文字 | [OpenAI Whisper](https://github.com/openai/whisper)（`turbo` 模型，本機運算） |
| 翻譯 | [deep-translator](https://github.com/nidhaloff/deep-translator)（Google 翻譯後端） |
| 字幕格式處理 | Python 標準函式庫 |

整個流程不依賴付費 API，Whisper 在本機運算，沒有額度或長度限制（影片長度只會影響運算時間）。

## 已知限制

- 目前語言設定為固定「韓文 → 繁體中文」，若要支援其他語言需修改 `--language` 參數與翻譯來源語言
- 翻譯後端為 Google 翻譯，對口語化、語氣詞較多的內容（如綜藝、直播）翻譯品質有時不夠自然，仍建議人工校對重要片段
- 影片長度越長，Whisper 運算時間越久；無 GPU 加速的機器（純 CPU）建議搭配 `small` 模型以加快速度

## License

MIT
