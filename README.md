# KoeMojiAuto

音声・動画ファイルから自動で文字起こしを行うクロスプラットフォーム対応CLIツール。
Windows、macOS、Linuxで動作します。

## 🚀 クイックスタート（5分で始める）

1. [Python 3.9以上](https://www.python.org/downloads/)をインストール（**必ず「Add Python to PATH」にチェック**）
2. `install.bat`をダブルクリック
3. `create_shortcut.bat`でデスクトップにショートカット作成
4. 音声ファイルを`input/`フォルダに入れる
5. ショートカットから起動して「1」を押す

## 📋 導入前の確認

### 前提条件チェックリスト
- [ ] OS: Windows 10/11、macOS 10.14以上、Linux（Ubuntu 20.04以上推奨）
- [ ] Python 3.9以上
  - Windows: コマンドプロンプトで`python --version`
  - Mac/Linux: ターミナルで`python3 --version`
- [ ] pip（パッケージマネージャー）
  - Windows: `pip --version`
  - Mac/Linux: `pip3 --version`
- [ ] メモリ 8GB以上推奨
- [ ] ストレージ 5GB以上の空き容量

### 初回起動時の注意
- AIモデルの初回ダウンロード（約3GB）に10-30分かかります
- ウイルス対策ソフトが警告を出す場合があります（AIモデルのダウンロードのため。安全です）
- ダウンロード中は進捗が表示されないため、しばらくお待ちください

## 🔧 インストール

### 自動インストール（推奨）

#### Windows
1. `install.bat`を**右クリック→管理者として実行**
2. 「Setup Complete!」と表示されれば完了

#### Mac/Linux
1. ターミナルを開く
2. プロジェクトフォルダに移動
3. 以下のコマンドを実行:
```bash
python3 install.py
```

### 手動インストール（自動インストールが失敗した場合）

#### Windows
```bash
# コマンドプロンプトを管理者権限で開く
cd C:\path\to\KoeMojiAuto-cli
pip install -r requirements.txt
```

#### Mac/Linux
```bash
# ターミナルで実行
cd /path/to/KoeMojiAuto-cli
pip3 install -r requirements.txt
```

### Pythonが見つからない場合
1. [Python公式サイト](https://www.python.org/downloads/)から最新版をダウンロード
2. インストーラーを実行し、**最初の画面で「Add Python to PATH」に必ずチェック**
3. インストール完了後、PCを再起動
4. コマンドプロンプトで`python --version`を実行して確認
## 🎬 初回セットアップと起動

### ショートカットの作成
1. `create_shortcut.bat`を実行
2. デスクトップに「KOEMOJIAUTO」ショートカットが作成される
3. ショートカットを使いやすい場所（タスクバーなど）にピン留め

### 初回起動

#### Windows
1. 作成したショートカットをダブルクリック（または`run.bat`を直接実行）

#### Mac/Linux
1. ターミナルで以下を実行:
```bash
python3 run.py
# または
./run.sh  # install.pyで作成されている場合
```
2. 以下のフォルダが自動作成される：
   - `input/` - 音声ファイルを入れる場所
   - `output/` - 文字起こし結果の保存場所
   - `archive/` - 処理済みファイルの保管場所
3. メニューが表示されたら初期設定完了
4. 初回実行時はAIモデルのダウンロードが始まる（10-30分待つ）

## 📝 基本的な使い方

### 文字起こしの手順
1. `input/`フォルダに音声・動画ファイルを入れる
2. ショートカットから起動する
3. メニューから「1」を入力して開始
4. 処理が完了すると`output/`フォルダにテキストファイルが作成される
5. 元ファイルは`archive/`フォルダに自動で移動する

### 対応ファイル形式
- 音声：MP3, WAV, M4A, FLAC, OGG, AAC
- 動画：MP4, MOV, AVI

### 処理時間の目安
**一般的なPC（Core i5、8GB RAM）**
- 10分の音声：約10-15分
- 1時間の音声：約60-90分

**高性能PC（Core i7/i9、16GB RAM以上）**
- 10分の音声：約5-8分
- 1時間の音声：約30-50分
## ⚙️ 設定のカスタマイズ

### AIモデル選択ガイド
`config.json`の`whisper_model`を変更することで、速度と精度のバランスを調整できます。

| モデル | 処理速度 | 精度 | 必要メモリ | 推奨用途 |
|--------|----------|------|------------|----------|
| small  | 高速(1x) | 普通 | 2GB | 議事録の下書き、ざっくりとした内容把握 |
| medium | 中速(2x) | 良好 | 5GB | 一般的な文字起こし（デフォルト推奨） |
| large  | 低速(5x) | 最高 | 10GB | 正確性重視、専門用語が多い音声 |

```json
{
  "whisper_model": "medium"  // ← ここを変更
}
```

### 言語の変更
```json
{
  "language": "en"  // 英語の場合（日本語は"ja"）
}
```

### その他の詳細設定
```json
{
  "scan_interval_minutes": 30,  // フォルダ監視間隔（分）
  "max_cpu_percent": 95        // CPU使用率の上限（他の作業をする場合は50-70に下げる）
}
```
## 🔧 トラブルシューティング

### よくあるエラーメッセージと対処法

#### インストール時のエラー
| エラーメッセージ | 原因 | 対処法 |
|-----------------|------|--------|
| `'python' は認識されていません` | PythonがPATHに追加されていない | Pythonを再インストールし、「Add to PATH」にチェック |
| `No module named pip` | pipがインストールされていない | `python -m ensurepip --upgrade`を実行 |
| `error: Microsoft Visual C++ 14.0 or greater is required` | C++ビルドツールが不足 | [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)をインストール |

#### 実行時のエラー
| エラーメッセージ | 原因 | 対処法 |
|-----------------|------|--------|
| `ModuleNotFoundError: No module named 'faster_whisper'` | 依存関係が不完全 | `pip install -r requirements.txt`を再実行 |
| `RuntimeError: CUDA out of memory` | GPUメモリ不足 | より小さいモデル（small/medium）を使用 |
| `PermissionError: [Errno 13]` | ファイルが使用中 | 対象ファイルを閉じてから再実行 |
| `UnicodeDecodeError` | 文字コードの問題 | ログファイル（koemoji.log）を削除して再実行 |

### 一般的な問題
| 症状 | 対処法 |
|------|--------|
| ファイルが処理されない | 対応形式か確認し、メニューで「1」を押す |
| 処理が異常に遅い | `config.json`の`whisper_model`を`small`に変更 |
| 文字化けする | メモ帳ではなく、VSCodeやサクラエディタなどUTF-8対応エディタで開く |
| メモリ不足エラー | 他のアプリを終了し、`max_cpu_percent`を下げる |
| 初回起動が終わらない | AIモデルのダウンロード中（最大30分程度待つ） |
## ❓ よくある質問（FAQ）

**Q: 処理中にPCが重くなって他の作業ができない**  
A: `config.json`の`max_cpu_percent`を50-70に下げてください。処理は遅くなりますが、他の作業と並行できます。

**Q: 文字起こしの精度を上げたい**  
A: `whisper_model`はデフォルトで`large`になっていて、最も精度が高いモデルに設定されています。

**Q: 英語の音声も文字起こしできますか？**  
A: はい。`config.json`の`language`を`"en"`に変更してください。

**Q: 複数の言語が混在する音声は処理できますか？**  
A: 現在は単一言語のみ対応しています。最も多く含まれる言語を設定してください。

**Q: OneDriveやGoogleドライブのフォルダで使えますか？**  
A: 使えますが、同期中のファイルはエラーになる場合があります。処理完了まで同期を一時停止することを推奨します。

**Q: 処理済みファイルを元に戻したい**  
A: `archive/`フォルダから手動で移動してください。

**Q: ログファイルが大きくなりすぎた**  
A: `koemoji.log`は削除しても問題ありません。自動的に再作成されます。

## 💡 使用例とヒント

### 適している用途
- ✅ 会議の議事録作成
- ✅ インタビューの文字起こし
- ✅ 講演会・セミナーの記録
- ✅ 動画の字幕作成準備
- ✅ ポッドキャストの書き起こし
- ✅ 24時間365日の自動処理

### 適さない用途
- ❌ リアルタイム文字起こし（録音と同時表示）
- ❌ ストリーミング配信の処理
- ❌ 1日100ファイル以上の大量処理
- ❌ 複数言語が頻繁に切り替わる音声
- ❌ 音楽の歌詞起こし（精度が低い）

### 便利な使い方
- **夜間の大量処理**: PCをスリープさせずに放置。朝には完了
- **定期的な処理**: Windowsタスクスケジューラーと組み合わせて自動化
- **フォルダ監視**: 30分ごとに自動でファイルをチェック（常時起動で実現）
## 📊 技術仕様

- **使用AI**: OpenAI Whisper（faster-whisper実装）
- **処理方式**: ローカル処理（インターネット接続不要※初回モデルDL時を除く）
- **CPU使用率制限**: デフォルト95%（他の作業に影響しないよう制御可能）
- **対応OS**: Windows 10/11（64bit）、macOS 10.14+、Linux（Ubuntu 20.04+推奨）
- **必要Python**: 3.9以上

## 📌 バージョン情報

- **現在のバージョン**: 1.0.0
- **最終更新**: 2024-01-XX
- **動作確認済み環境**:
  - Windows 11 (22H2, 23H2)
  - Windows 10 (21H2, 22H2)
  - Python 3.9.13, 3.10.11, 3.11.5, 3.12.0

## 🐛 問題が解決しない場合

1. `koemoji.log`でエラー内容を確認
2. [GitHub Issues](https://github.com/infoHiroki/KoeMojiAuto-cli/issues)で同様の問題を検索
3. 新しい問題の場合はIssueを作成（ログファイルの該当部分を添付）

## 📞 サポート

- **GitHub Issues**: https://github.com/infoHiroki/KoeMojiAuto-cli/issues
- **技術詳細**: https://infohiroki.github.io/KoeMojiAuto-cli/
- **作者**: [@infoHiroki](https://github.com/infoHiroki)

## 📄 ライセンス

本ソフトウェアは以下の条件で利用できます：

- **個人利用**: 無料・無制限
- **教育・研究利用**: 無料・無制限
- **商用利用**: 事前に info.hirokitakamura@gmail.com へご連絡ください

詳細は[LICENSE](LICENSE)ファイルを参照