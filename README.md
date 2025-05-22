# KoeMojiAuto

音声・動画ファイルから自動で文字起こしを行うCLIツールです。

## 🚀 使い方

### 初回セットアップ
1. 依存関係をインストール：`pip install -r requirements.txt`
2. 実行すると自動的に以下のフォルダが作成されます：
   - `input/` - 音声・動画ファイルを置くフォルダ
   - `output/` - 文字起こし結果（テキストファイル）
   - `archive/` - 処理済みファイルの保管場所

### 基本的な使い方
1. `python koemoji.py` で起動
2. メニューから「1. 開始」を選択
3. `input/` フォルダに音声・動画ファイルを配置
4. 自動的に文字起こしが実行され、結果が `output/` に保存されます

### 対応ファイル形式
- 音声：MP3, WAV, M4A, FLAC, OGG, AAC
- 動画：MP4, MOV, AVI

### 設定変更
`config.json` ファイルを編集することで設定を変更できます：
- `whisper_model`: 認識精度（"small", "medium", "large"）
- `language`: 言語設定（"ja"は日本語）
- `scan_interval_minutes`: フォルダ監視間隔（分）

## 🛠️ 開発者向け

### セットアップ
```bash
# 依存関係インストール
pip install -r requirements.txt
```

### 要件
- Python 3.8+
- faster-whisper
- psutil
