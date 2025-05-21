# KoemojiAuto テストディレクトリ

## ディレクトリ構造

```
tests/
├── README.md               # このファイル
├── __init__.py            # Pythonパッケージ化
│
├── # 自動テスト（pytest用）
├── test_config.py         # 設定ファイル関連のテスト
├── test_utils.py          # ユーティリティ関数のテスト
├── test_file_scanning.py  # ファイルスキャン機能のテスト
├── test_queue_management.py # キュー管理のテスト
├── test_file_processing.py  # ファイル処理のテスト
├── test_reporting.py      # レポート機能のテスト
├── test_integration.py    # 統合テスト
│
└── manual/                # 手動テスト用スクリプト
    ├── test_notification.py           # 通知機能の基本テスト
    ├── test_notification_debug.py     # 通知機能の詳細デバッグ
    └── test_alternative_notification.py # 代替通知方法のテスト
```

## 自動テストの実行

```bash
# すべてのテストを実行
python3 -m pytest tests/ -v

# カバレッジレポート付きで実行
python3 -m pytest tests/ --cov=. --cov-report=html

# 特定のテストファイルのみ実行
python3 -m pytest tests/test_config.py -v
```

## 手動テストの実行

```bash
# 通知機能のテスト
python3 tests/manual/test_notification.py

# 通知機能の詳細デバッグ
python3 tests/manual/test_notification_debug.py

# 代替通知方法のテスト
python3 tests/manual/test_alternative_notification.py
```

## テストの追加方法

新しいテストを追加する場合：

1. 自動テストの場合
   - `tests/`ディレクトリに`test_*.py`形式でファイルを作成
   - pytestの規約に従ってテストを記述

2. 手動テストの場合
   - `tests/manual/`ディレクトリにスクリプトを作成
   - 実行可能な独立したスクリプトとして記述

## 注意事項

- 自動テストはCI/CDパイプラインで実行されることを想定
- 手動テストは開発者が手動で実行することを想定
- テスト実行前に`requirements.txt`の依存関係をインストールすること