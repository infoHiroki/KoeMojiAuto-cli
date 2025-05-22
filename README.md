# KoeMojiAuto

音声・動画ファイルから自動で文字起こしを行うCLIツールです。
デフォルトは開始時に一度実行されます。それ以降は30分ごとに実行されます。

## 🚀 使い方

### 初回セットアップ
1. `install.bat`を実行する。
2. `Setup Complete!`　と表示されればOK。

＊上手くいかなかった場合は手動でインストール
1. 依存関係をインストール：`pip install -r requirements.txt`
2. 初回実行時に自動的に以下のフォルダが作成されます：
   - `input/` - 音声・動画ファイルを置くフォルダ
   - `output/` - 文字起こし結果（テキストファイル）
   - `archive/` - 処理済みファイルの保管場所
3. 文字起こしを開始する場合は一度、開き直してください。


### ショートカット作成
- `create_shortcut.bat`を実行するとショートカットが作られます。好きな場所に移動して使ってください。


### 基本的な使い方
1. `ショートカットから起動`　or `run.batから起動` or `python koemoji.py` で起動
2. `input/` フォルダに音声・動画ファイルを配置
3. `input/` メニューから「1. 開始」を選択
4. 自動的に文字起こしが実行され、結果が `output/` に保存されます
5. 音声ファイルはarchiveフォルダに移動します。

### 対応ファイル形式
- 音声：MP3, WAV, M4A, FLAC, OGG, AAC
- 動画：MP4, MOV, AVI

### 設定変更
`config.json` ファイルを編集することで設定を変更できます：
- `whisper_model`: 認識精度（"small", "medium", "large"）
- `language`: 言語設定（"ja"は日本語）
- `scan_interval_minutes`: フォルダ監視間隔（分）

### ログ情報
- `koemoji.log`にあります。長くなりすぎたら削除してください。

### 要件
- Python 3.9以上（FasterWhisperの要件に準ずる）
- faster-whisper
- psutil
