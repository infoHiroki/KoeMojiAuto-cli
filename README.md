# KoeMojiAuto
[webサイト](https://infohiroki.github.io/KoeMojiAuto-cli/index.html)

音声・動画ファイルから自動で文字起こしを行うクロスプラットフォーム対応CLIツール。
Windows、macOS、Linuxで動作します。

## 🚀 クイックスタート

### Windows
1. [Python 3.9以上](https://www.python.org/downloads/)をインストール（**必ず「Add Python to PATH」にチェック**）
2. `install.bat`をダブルクリックする
3. `create_shortcut.bat`でショートカット作成して好きな場所に移動する
4. 音声ファイルを`input/`フォルダに入れる
5. ショートカットから起動して「1」を押してEnter

文字起こしが実行されます。
初回はWhisperAIのダウンロードなどがあります。しばらくお待ちください。
何か上手く動かなければ再起動してください。
ほとんどの問題は解決します。

### Mac
1. ターミナルで`python3 --version`を確認（3.9以上が必要）
2. プロジェクトフォルダで`python3 install.py`を実行
3. 短縮コマンドの設定（オプション）:
   - `./setup_aliases.sh`を実行
   - `source ~/.zshrc`を実行（設定を反映）
   - 以降は`km`だけで起動可能に！
4. 音声ファイルを`input/`フォルダに入れる
5. `km`で起動（または`python3 run.py`）して「1」を押す

## 📋 前提条件

| 項目 | Windows | Mac/Linux |
|------|---------|-----------|
| OS | Windows 10/11（64bit） | macOS 10.14+, Ubuntu 20.04+ |
| Python確認 | `python --version` | `python3 --version` |
| pip確認 | `pip --version` | `pip3 --version` |
| メモリ | 8GB以上推奨 | 8GB以上推奨 |
| ストレージ | 5GB以上の空き | 5GB以上の空き |

### 初回起動時の注意
- AIモデルの初回ダウンロード（約3GB）に10-30分かかります
- ダウンロード中は進捗が表示されないため、しばらくお待ちください

## 🔧 インストール

### Windows
```bash
# 方法1: 自動インストール（推奨）
install.batをダブルクリック

# 方法2: 手動インストール
pip install -r requirements.txt
```

### Mac/Linux
```bash
# 方法1: 自動インストール（推奨）
python3 install.py

# 方法2: 手動インストール
pip3 install -r requirements.txt
```

## 🎯 起動方法

### Windows
- **ショートカット**: 好きな場所で使えます。本体のフォルダを移動した場合はショートカットを作り直してください。
- **CLI**: `run.bat`または`python run.py`

### Mac/Linux
- **エイリアス使用**（推奨）: `km`
- **直接実行**: `python3 run.py`または`./run.sh`

## 📝 基本的な使い方

1. **音声ファイルを入れる**
   - Windows: `input\`フォルダ
   - Mac: `kmi`コマンドでFinderが開く

2. **KoeMojiを起動**
   - Windows: ショートカットまたは`run.bat`
   - Mac: `km`コマンド

3. **メニューで「1」を押して処理開始**

4. **結果を確認**
   - Windows: `output\`フォルダ
   - Mac: `kmo`コマンドでFinderが開く

### 対応ファイル形式
- 音声：MP3, WAV, M4A, FLAC, OGG, AAC
- 動画：MP4, MOV, AVI

## 🍎 Mac便利コマンド（エイリアス）

`./setup_aliases.sh`実行後に使用可能：

| コマンド | 動作 |
|----------|------|
| `km` | KoeMojiを起動 |
| `kmi` | 入力フォルダを開く |
| `kmo` | 出力フォルダを開く |
| `kml` | ログをリアルタイム表示 |
| `koemoji-config` | 設定ファイルを編集 |

## ⚙️ 設定のカスタマイズ

### AIモデル選択（config.json）

| モデル | 処理速度 | 精度 | 必要メモリ | 推奨用途 |
|--------|----------|------|------------|----------|
| small  | 高速(1x) | 普通 | 2GB | 議事録の下書き |
| medium | 中速(2x) | 良好 | 5GB | 一般的な文字起こし |
| large  | 低速(5x) | 最高 | 10GB | 正確性重視 |

```json
{
  "whisper_model": "large",     // モデルサイズ
  "language": "ja",             // 言語（日本語:ja, 英語:en）
  "scan_interval_minutes": 30,  // フォルダ監視間隔
  "max_cpu_percent": 95         // CPU使用率上限
}
```

## 🔧 トラブルシューティング

### Windows特有の問題

| エラー | 対処法 |
|--------|--------|
| `'python' は認識されていません` | Pythonを再インストールし「Add to PATH」にチェック |
| `Microsoft Visual C++ 14.0 required` | [Build Tools](https://visualstudio.microsoft.com/downloads/)をインストール |

### Mac特有の問題

| エラー | 対処法 |
|--------|--------|
| `command not found: python3` | Homebrewで`brew install python@3.11` |
| `Permission denied` | `chmod +x install.py run.py`を実行 |

### 共通の問題

| 症状 | 対処法 |
|------|--------|
| ファイルが処理されない | 対応形式か確認し、メニューで「1」を押す |
| 処理が異常に遅い | `whisper_model`を`small`に変更 |
| 文字化けする | UTF-8対応エディタで開く（VSCode等） |
| メモリ不足 | `max_cpu_percent`を50-70に下げる |

## ❓ よくある質問

**Q: Windows/Macで操作は違いますか？**  
A: 基本的な使い方は同じです。起動方法とファイルパスの表記（`\`と`/`）が異なるだけです。

**Q: 処理速度を上げたい**  
A: `whisper_model`を`small`または`medium`に変更してください。

**Q: 他の言語に対応していますか？**  
A: はい。`config.json`の`language`を変更してください（英語:`en`、中国語:`zh`など）。

**Q: ログファイルが大きくなりすぎた**  
A: `koemoji.log`は削除しても問題ありません。

## 📊 技術仕様

- **使用AI**: OpenAI Whisper（faster-whisper実装）
- **処理方式**: ローカル処理（インターネット接続不要※初回DL時を除く）
- **対応OS**: Windows 10/11、macOS 10.14+、Linux
- **必要Python**: 3.9以上

## 💡 使用例とヒント

### 適している用途
- ✅ 会議の議事録作成
- ✅ インタビューの文字起こし
- ✅ 講演会・セミナーの記録
- ✅ 動画の字幕作成準備
- ✅ 24時間365日の自動処理

### 便利な使い方
- **Windows**: タスクスケジューラーで自動化
- **Mac**: `launchd`やcronで自動化
- **共通**: 夜間に大量処理を実行

## 📞 サポート

- **GitHub Issues**: https://github.com/infoHiroki/KoeMojiAuto-cli/issues
- **作者**: [@infoHiroki](https://github.com/infoHiroki)

## 📄 ライセンス

- **個人・教育利用**: 無料・無制限
- **商用利用**: info.hirokitakamura@gmail.com へご連絡ください

詳細は[LICENSE](LICENSE)ファイルを参照
