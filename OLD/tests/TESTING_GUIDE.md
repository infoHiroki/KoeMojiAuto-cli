# KoemojiAuto テスト実行ガイド

## テスト準備

### 1. テスト環境のセットアップ

```bash
# テスト用ライブラリのインストール
pip install pytest pytest-cov pytest-asyncio mock

# テストディレクトリの作成
mkdir -p tests/test_data
```

### 2. テスト用データの準備

```bash
# テスト用の音声ファイルを作成（無音でも可）
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 10 -q:a 9 -acodec libmp3lame tests/test_data/sample_audio.mp3

# テスト用の動画ファイルを作成
ffmpeg -f lavfi -i testsrc=duration=10:size=320x240:rate=30 -pix_fmt yuv420p tests/test_data/sample_video.mp4
```

## テスト実行順序

### 1. 設定ファイルのテスト
`tests/test_config.py`

最初に設定ファイルの読み込み、作成、デフォルト値のテストを行います。

```bash
pytest tests/test_config.py -v
```

### 2. ユーティリティ関数のテスト
`tests/test_utils.py`

優先度計算やファイルフィルタリングなどの基本的な関数をテストします。

```bash
pytest tests/test_utils.py -v
```

### 3. ファイルスキャン機能のテスト
`tests/test_file_scanning.py`

入力フォルダのスキャンとファイル検出機能をテストします。

```bash
pytest tests/test_file_scanning.py -v
```

### 4. キュー管理のテスト
`tests/test_queue_management.py`

ファイルキューの管理、優先度順序付けをテストします。

```bash
pytest tests/test_queue_management.py -v
```

### 5. ファイル処理のテスト
`tests/test_file_processing.py`

個別ファイルの処理と文字起こし機能をテストします。

```bash
pytest tests/test_file_processing.py -v
```

### 6. 日次レポート機能のテスト
`tests/test_reporting.py`

日次サマリーの生成機能をテストします。

```bash
pytest tests/test_reporting.py -v
```

### 7. 統合テスト
`tests/test_integration.py`

全体的な処理フローをテストします。

```bash
pytest tests/test_integration.py -v
```

## すべてのテストを実行

```bash
# すべてのテストを実行
pytest tests/ -v

# カバレッジレポート付きで実行
pytest tests/ --cov=. --cov-report=html

# 並列実行（高速化）
pytest tests/ -n auto
```

## テスト作成のヒント

### モックの使用

Whisperモデルの実際のロードを避けるため、モックを使用します：

```python
from unittest.mock import patch, MagicMock

@patch('faster_whisper.WhisperModel')
def test_transcribe_audio(mock_model):
    # モックの設定
    mock_instance = MagicMock()
    mock_model.return_value = mock_instance
    mock_instance.transcribe.return_value = (
        [MagicMock(text="テスト文字起こし")], 
        MagicMock()
    )
    
    # テストの実行
    processor = KoemojiProcessor()
    result = processor.transcribe_audio("test.mp3")
    assert result == "テスト文字起こし"
```

### 一時ファイルの使用

```python
import tempfile
import os

def test_with_temp_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        # テスト用ファイルの作成
        test_file = os.path.join(temp_dir, "test.mp3")
        # ファイル操作のテスト
```

### 時間に関するテスト

```python
from unittest.mock import patch
from datetime import datetime

@patch('main.datetime')
def test_time_based_feature(mock_datetime):
    # 特定の時刻を設定
    mock_datetime.now.return_value = datetime(2024, 1, 1, 19, 0)
    # テストの実行
```

## CI/CD設定例

GitHub Actionsの設定例 (`.github/workflows/test.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install FFmpeg
      run: sudo apt-get update && sudo apt-get install -y ffmpeg
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## トラブルシューティング

### FFmpegが見つからない
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

### importエラー
```bash
# プロジェクトルートから実行
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/
```

### メモリ不足
```python
# テスト設定でより小さいモデルを使用
config = {
    "whisper_model": "tiny",  # テスト用に小さいモデル
    "max_concurrent_files": 1  # 並列処理を制限
}
```