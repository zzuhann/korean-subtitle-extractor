#!/usr/bin/env python3
"""
韓文影片（本地或 YouTube）→ 雙語字幕（韓文 + 繁體中文）
自動將字幕檔命名為與影片同名，方便 IINA / VLC 自動載入。

用法：
  本地影片：python korean_to_srt_final.py "/path/to/video.mp4"
  YouTube：  python korean_to_srt_final.py "https://www.youtube.com/watch?v=xxxxx"
"""

import sys
import os
import re
import subprocess
import shutil

# ── 設定 ──────────────────────────────────────────────
INPUT = sys.argv[1] if len(sys.argv) > 1 else input("請貼上影片路徑或 YouTube 網址：").strip()
WHISPER_MODEL = "turbo"   # 可改成 small / medium / large
BASE_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
# ──────────────────────────────────────────────────────

def sanitize_filename(name, max_length=80):
    """把標題轉成安全的資料夾名稱"""
    name = re.sub(r'[\\/:*?"<>|]', '', name)   # 移除不合法字元
    name = name.strip().strip('.')
    name = re.sub(r'\s+', ' ', name)
    return name[:max_length] if name else "untitled"

def get_youtube_title(url):
    """取得 YouTube 影片標題，用來命名資料夾"""
    result = subprocess.run(
        f'yt-dlp --get-title "{url}"',
        shell=True, capture_output=True, text=True
    )
    title = result.stdout.strip().split("\n")[0] if result.returncode == 0 else ""
    return sanitize_filename(title) if title else "youtube_video"

def run(cmd, desc=""):
    print(f"\n▶ {desc}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ 失敗：{desc}")
        sys.exit(1)

def is_youtube_url(s):
    return s.startswith("http://") or s.startswith("https://")

def check_deps(is_url):
    missing = []
    tools = ["whisper", "ffmpeg"]
    if is_url:
        tools.append("yt-dlp")
    for tool in tools:
        if subprocess.run(f"which {tool}", shell=True, capture_output=True).returncode != 0:
            missing.append(tool)
    if missing:
        print(f"❌ 缺少工具：{', '.join(missing)}")
        print("請先安裝：pip install yt-dlp openai-whisper && brew install ffmpeg")
        sys.exit(1)

def check_yt_dlp_version():
    """檢查 yt-dlp 是否為最新版本（比對 PyPI 上的最新版本號）。
    若有新版本，停止腳本並提示手動更新——因為更新方式因安裝方式
    （pip / pipx / Homebrew / 獨立執行檔）而異，腳本無法可靠地自動判斷，
    交由使用者確認後手動執行較安全。"""
    result = subprocess.run("yt-dlp --version", shell=True, capture_output=True, text=True)
    current_version = result.stdout.strip()
    print(f"▶ 當前 yt-dlp 版本：{current_version}")

    print("▶ 檢查最新版本中...")
    latest_result = subprocess.run(
        f"{sys.executable} -m pip index versions yt-dlp",
        shell=True, capture_output=True, text=True
    )

    match = re.search(r"yt-dlp \(([\d.]+)\)", latest_result.stdout)
    if not match:
        print("⚠️  無法取得最新版本資訊，跳過版本檢查")
        return True

    latest_version = match.group(1)
    print(f"▶ 最新版本：{latest_version}")

    if current_version == latest_version:
        print("✅ yt-dlp 已是最新版本")
        return True

    print("🔄 發現新版本！請先手動更新後再重新執行此腳本：")
    print()
    print("    pipx upgrade yt-dlp")
    print()
    print("   （若你的 yt-dlp 不是用 pipx 安裝，請改用對應的更新方式）")
    return False

def translate_srt(ko_srt_path, zh_srt_path, bilingual_srt_path):
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print("\n⚠️  需要安裝翻譯套件：pip install deep-translator")
        print("安裝後重新執行，或手動翻譯字幕檔。")
        return False

    translator = GoogleTranslator(source='ko', target='zh-TW')

    with open(ko_srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    zh_blocks = []
    bilingual_blocks = []

    print(f"▶ 翻譯字幕中（共 {len(blocks)} 段）...")

    for i, block in enumerate(blocks):
        lines = block.strip().split("\n")
        if len(lines) < 3:
            zh_blocks.append(block)
            bilingual_blocks.append(block)
            continue

        index_line = lines[0]
        time_line = lines[1]
        ko_text = "\n".join(lines[2:])

        try:
            zh_text = translator.translate(ko_text)
        except Exception as e:
            print(f"  翻譯第 {i+1} 段失敗：{e}")
            zh_text = ko_text

        zh_blocks.append(f"{index_line}\n{time_line}\n{zh_text}")
        bilingual_blocks.append(f"{index_line}\n{time_line}\n{ko_text}\n{zh_text}")

        if (i + 1) % 50 == 0:
            print(f"  進度：{i+1}/{len(blocks)}")

    with open(zh_srt_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(zh_blocks))

    with open(bilingual_srt_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(bilingual_blocks))

    return True


def main():
    is_url = is_youtube_url(INPUT)
    check_deps(is_url)
    if is_url:
        if not check_yt_dlp_version():
            print("⏸️  請先完成更新後再重新執行此腳本")
            sys.exit(1)
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

    if is_url:
        print("\n▶ Step 1／3　取得影片標題以建立專屬資料夾...")
        title = get_youtube_title(INPUT)
        OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, title)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"  資料夾：{OUTPUT_DIR}")

        # 下載「影片」而非只下載音訊，這樣才有畫面可以搭配字幕播放
        video_path = os.path.join(OUTPUT_DIR, "video.mp4")
        run(
            f'yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" '
            f'-o "{video_path}" "{INPUT}"',
            "下載 YouTube 影片中..."
        )
        whisper_input = video_path
        base_name = "video"
    else:
        if not os.path.exists(INPUT):
            print(f"❌ 找不到檔案：{INPUT}")
            sys.exit(1)

        title = sanitize_filename(os.path.splitext(os.path.basename(INPUT))[0])
        OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, title)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 把本地影片複製一份到輸出資料夾，方便跟字幕放在一起、檔名統一管理
        ext = os.path.splitext(INPUT)[1]
        video_path = os.path.join(OUTPUT_DIR, f"video{ext}")
        shutil.copy(INPUT, video_path)
        whisper_input = video_path
        base_name = "video"
        print(f"\n▶ Step 1／3　使用本地影片：{INPUT}")
        print(f"  資料夾：{OUTPUT_DIR}（已複製影片到此）")

    # Step 2：Whisper 轉錄韓文
    run(
        f'whisper "{whisper_input}" --language Korean --model {WHISPER_MODEL} '
        f'--output_format srt --output_dir "{OUTPUT_DIR}"',
        "Step 2／3　Whisper 轉錄韓文中（這步最久，請耐心等待）..."
    )

    ko_srt = os.path.join(OUTPUT_DIR, f"{base_name}.srt")
    zh_srt = os.path.join(OUTPUT_DIR, f"{base_name}_zh.srt")
    bilingual_srt_raw = os.path.join(OUTPUT_DIR, f"{base_name}_bilingual.srt")

    if not os.path.exists(ko_srt):
        print(f"❌ 找不到字幕檔：{ko_srt}")
        sys.exit(1)

    # Step 3：翻譯 + 合併雙語字幕
    print("\n▶ Step 3／3　翻譯成繁體中文並合併雙語字幕...")
    success = translate_srt(ko_srt, zh_srt, bilingual_srt_raw)

    # ── 關鍵：把雙語字幕複製成跟影片完全同名，IINA/VLC 才會自動載入 ──
    # video.mp4 → video.srt（取代副檔名，不是疊加）
    video_basename_no_ext = os.path.splitext(os.path.basename(video_path))[0]
    auto_load_srt = os.path.join(OUTPUT_DIR, f"{video_basename_no_ext}.srt")

    if success:
        shutil.copy(bilingual_srt_raw, auto_load_srt)
    else:
        shutil.copy(ko_srt, auto_load_srt)

    print("\n" + "="*50)
    print("✅ 完成！輸出檔案：")
    print(f"  影片：        {video_path}")
    print(f"  韓文字幕：    {ko_srt}")
    if success:
        print(f"  中文字幕：    {zh_srt}")
        print(f"  雙語字幕：    {bilingual_srt_raw}")
    print(f"  🎯 自動載入字幕（與影片同名）：{auto_load_srt}")
    print("="*50)
    print(f"\n直接用 IINA 開啟「{video_path}」即可自動顯示雙語字幕，不用手動拖曳！")


if __name__ == "__main__":
    main()