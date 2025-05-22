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

## ❓ FAQ（よくある質問）

### インストール・セットアップ関連

**Q: install.batが失敗する**
A: 以下を確認してください：
- Python 3.9以上がインストールされているか
- インターネット接続が安定しているか
- 管理者権限で実行しているか
- 手動でインストールする場合：`pip install -r requirements.txt`

**Q: 「Python が見つかりません」エラーが出る**
A: 
- Pythonがインストールされていない可能性があります
- [Python公式サイト](https://www.python.org/)からダウンロード・インストール
- インストール時に「Add Python to PATH」にチェックを入れる

**Q: 初回実行後、ショートカットが動作しない**
A: 
- `create_shortcut.bat`を実行してショートカットを再作成
- または`run.bat`を直接実行

### 使用方法関連

**Q: ファイルを置いても処理されない**
A: 以下を確認してください：
- メニューから「1. 開始」を選択しているか
- 対応ファイル形式か（MP3, WAV, M4A, FLAC, OGG, AAC, MP4, MOV, AVI）
- ファイルが破損していないか
- 最新ログで`koemoji.log`を確認

**Q: 処理が遅い、止まる**
A: 
- CPU使用率が高い場合は自動で待機します
- `config.json`で`max_cpu_percent`を調整（デフォルト95%）
- `whisper_model`を"small"や"medium"に変更して軽量化
- 大容量ファイルは処理に時間がかかります

**Q: 複数ファイルを同時に処理したい**
A: 
- `input/`フォルダに複数ファイルを配置すると自動で順次処理
- `config.json`の`max_concurrent_files`で同時処理数を調整（デフォルト3）

### エラー・トラブルシューティング

**Q: 「faster_whisperがインストールされていません」エラー**
A: 
```bash
pip install faster-whisper
```
を実行してください

**Q: 文字起こし結果が文字化けする**
A: 
- 出力ファイルはUTF-8形式です
- メモ帳の代わりに、VS Code やnotepad++などのエディタを使用
- Windowsのメモ帳で開く場合は、エンコーディングをUTF-8に設定

**Q: 音声認識の精度が悪い**
A: 
- `config.json`で`whisper_model`を"large"に変更（処理は重くなります）
- 音声品質を確認（ノイズが多い、音量が小さい等）
- 言語設定が正しいか確認（`language: "ja"`）

**Q: ログファイルが大きくなりすぎる**
A: 
- `koemoji.log`を定期的に削除してください
- または名前を変更してバックアップ

### 設定関連

**Q: 処理間隔を変更したい**
A: 
`config.json`の`scan_interval_minutes`を変更（分単位）
```json
{
  "scan_interval_minutes": 10
}
```

**Q: 英語音声を処理したい**
A: 
`config.json`の`language`を変更
```json
{
  "language": "en"
}
```

**Q: 処理完了後にファイルを削除したい**
A: 
現在は`archive/`フォルダに移動する仕様です。必要に応じて`archive/`フォルダから手動で削除してください。

### パフォーマンス関連

**Q: メモリ使用量を減らしたい**
A: 
- `whisper_model`を"small"に変更
- `max_concurrent_files`を1に設定
- `compute_type`を"int8"に設定（デフォルト）

**Q: GPU処理に対応していますか？**
A: 
faster-whisperはGPU対応していますが、本ツールではCPU処理のみ対応。GPU使用したい場合は、`compute_type`設定の変更が必要です。

## 🐛 問題が解決しない場合

1. `koemoji.log`でエラー内容を確認
2. [GitHub Issues](https://github.com/infoHiroki/KoeMojiAuto-cli/issues)で同様の問題を検索
3. 新しい問題の場合はIssueを作成してください

## 📞 サポート

- GitHub Issues: [https://github.com/infoHiroki/KoeMojiAuto-cli/issues](https://github.com/infoHiroki/KoeMojiAuto-cli/issues)
- アーキテクチャ詳細: [https://infohiroki.github.io/KoeMojiAuto-cli/](https://infohiroki.github.io/KoeMojiAuto-cli/)
