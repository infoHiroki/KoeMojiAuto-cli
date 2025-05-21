# KoemojiAuto-win - Windows用自動文字起こしシステム

*最終更新: 2025年5月21日*

音声・動画ファイルから自動で文字起こしを行うWindows専用ツールです。
Whisperモデルを使用した高精度な文字起こしを、WebUIから簡単に操作できます。

## 使い方

1. **音声・動画ファイルを配置**
   ```
   inputフォルダに音声・動画ファイルを入れる
   ```

2. **実行方法**

   ### 推奨: WebUIで実行
   ```bash
   # WebUI起動
   start_webui.bat
   ```
   ブラウザで http://localhost:8080 にアクセス
   
   **WebUIの特徴:**
   - ✅ ブラウザから簡単操作（開始/停止/設定変更）
   - ✅ リアルタイムでステータスとログを確認
   - ✅ バックグラウンド実行（ブラウザを閉じても処理継続）
   - ✅ リモートアクセス可能（同一ネットワーク内）

   ### その他の実行方法
   
   **コマンドラインで実行（スクリプト連携向け）**
   ```bash
   # 実行
   start_koemoji.bat

   # 停止
   stop_koemoji.bat

   # ステータス確認
   status_koemoji.bat
   ```
   
   **Pythonで直接実行（開発・デバッグ用）**
   ```bash
   python main.py
   ```
   ※ フォアグラウンドで実行（ターミナルを閉じると停止）

3. **文字起こし結果を確認**
   ```
   outputフォルダに text ファイルが生成される
   ```

## 主な機能

- **高精度文字起こし**: Whisperモデル（tiny/small/medium/large）を選択可能
- **連続実行**: 24時間継続的にファイルを監視・処理
- **ファイルスキャン**: 30分毎にinputフォルダをスキャンして新しいファイルを自動処理
- **シンプルな管理**: WebUIで簡単設定・操作
- **安全な制御**: 実行・停止・ステータス確認コマンド
- **同時実行制御**: 複数プロセスの同時実行を防止
- **ログ記録**: 処理完了やエラーの詳細をログファイルに記録
- **処理済みファイル管理**: 一度処理したファイルは自動的にスキップ
- **エラーリカバリー**: 処理中にエラーが発生しても他のファイルの処理を継続
- **リソース管理**: CPU使用率制限とメモリ効率的な処理

## クイックスタート

### 1. 必要な環境

- Windows 10/11
- Python 3.9以上
- FFmpeg（音声・動画処理用）

### 2. セットアップ

```bash
# リポジトリをクローンまたはZIPをダウンロード
git clone https://github.com/infoHiroki/KoeMojiAuto-win.git
cd KoeMojiAuto-win

# 依存関係をインストール
pip install -r requirements.txt

# FFmpegをインストール
# 公式サイトからダウンロードしてインストールするか、以下を実行
install.bat
```

### 3. WebUIを起動

```bash
start_webui.bat
```

ブラウザで http://localhost:8080 を開いて使用開始！

## パス指定について

設定ファイルでパスを指定する場合は以下の形式が利用できます：

1. **相対パス**: `output` （カレントディレクトリからの相対パス）
2. **絶対パス**: `C:\Users\Username\Documents\出力フォルダ`
3. **UNCパス**: `\\ServerName\SharedFolder\出力フォルダ`

**注意**: 日本語パスを使用する場合は、プログラムが適切にエンコーディングを処理しますが、
トラブルを避けるためにASCII文字のみのパスを使用することを推奨します。

## 設定ファイル

`config.json` で各種設定を管理：

```json
{
  "input_folder": "input",          // 入力フォルダ
  "output_folder": "output",        // 出力フォルダ
  "scan_interval_minutes": 30,      // フォルダスキャン間隔（分）
  "max_concurrent_files": 3,        // 同時処理ファイル数
  "whisper_model": "large",         // Whisperモデル（tiny/small/medium/large）
  "language": "ja",                 // 言語設定
  "compute_type": "int8",           // 計算精度
  "max_cpu_percent": 80             // CPU使用率上限（%）
}
```

## セキュリティ情報

- WebUIはデフォルトで認証機能がありません。信頼されたネットワーク内でのみ使用してください。
- Windowsファイアウォールでポート8080の接続を制限することを推奨します。
- 処理する音声・動画ファイルは権限のあるフォルダのみを使用してください。

## トラブルシューティング

### WebUIにアクセスできない場合
- ポート8080が使用されていないか確認
- ファイアウォール設定を確認
- 別のポートで起動: `app.run(port=8081)` に変更

### 文字起こしが開始されない場合
- 入力フォルダに音声/動画ファイルがあるか確認
- 対応形式: mp3, mp4, wav, m4a, mov, avi, flac, ogg, aac
- ログファイル（koemoji.log）でエラーを確認

### メモリ不足エラー
- Whisperモデルをsmallやtinyに変更
- max_concurrent_filesを減らす
- max_cpu_percentを下げる

## 動作モード

### 24時間連続モード
一度起動すると、停止するまで継続的にファイルを監視・処理します。

## 設定項目の詳細

### Whisperモデルサイズ
処理速度と精度のバランスを選択：

| モデル | サイズ | 精度 | 速度 | 推奨用途 |
|--------|--------|------|------|----------|
| tiny   | 39MB   | ★★☆☆☆ | ★★★★★ | 高速処理・字幕確認 |
| small  | 244MB  | ★★★☆☆ | ★★★★☆ | バランス型 |
| medium | 769MB  | ★★★★☆ | ★★★☆☆ | 高品質バランス |
| large  | 1550MB | ★★★★★ | ★★☆☆☆ | 最高精度（推奨） |

### 計算精度（compute_type）とスペック目安
メモリ使用量とパフォーマンスのバランス：

| 設定 | メモリ使用 | 速度 | 推奨環境 |
|------|------------|------|----------|
| int8 | 低 | 高速 | CPU専用・一般的なPC（8GB RAM以上） |
| float16 | 中 | 中速 | GPU推奨（NVIDIA GPU + 16GB RAM以上） |
| float32 | 高 | 低速 | 高性能GPU推奨（RTX 3060以上 + 32GB RAM） |

**注意事項:**
- **int8**: CPU向けに最適化。GPUがなくても高速動作
- **float16**: GPU（特にNVIDIA）で最も効率的。GPUメモリが必要
- **float32**: 最高精度だが処理速度は遅い。研究用途向け

### GPU対応について

**Windows上でのGPU対応:**
- NVIDIA GPUをお持ちの場合は自動的に使用されます（CUDA要インストール）
- CUDA環境のセットアップ:
  1. NVIDIA CUDAツールキットをインストール（公式サイトから）
  2. cuDNNをインストール
  3. `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

### 推奨設定例

**CPU環境（GPUなしのWindows）**:
```json
{
    "whisper_model": "medium",
    "compute_type": "int8",     // CPUに最適
    "max_concurrent_files": 2,
    "max_cpu_percent": 80
}
```

**GPU搭載PC**（NVIDIA GPU + 16GB RAM）:
```json
{
    "whisper_model": "large",
    "compute_type": "float16",  // GPUに最適
    "max_concurrent_files": 3,
    "max_cpu_percent": 60      // GPUが処理するためCPU負荷は低め
}
```

**ハイエンドGPU搭載PC**（RTX 3080以上 + 32GB RAM）:
```json
{
    "whisper_model": "large",
    "compute_type": "float16",  // float32は精度重視の場合のみ
    "max_concurrent_files": 5,
    "max_cpu_percent": 50
}
```

## 対応ファイル形式

- 音声: MP3, WAV, M4A, FLAC, OGG, AAC
- 動画: MP4, MOV, AVI

## フォルダ構成

```
KoeMojiAuto-win/
├── input/              # 音声・動画ファイルを配置
├── output/             # 文字起こし結果（.txt）
├── archive/            # 処理済みファイル保存場所
├── config.json         # 設定ファイル
├── koemoji.log         # 実行ログ
├── *.bat               # 起動・停止用バッチファイル
└── static/             # WebUI用素材
```

## よくある質問（FAQ）

### Q: ファイルが処理されない
A: 以下を確認してください：
- ファイル形式が対応しているか（MP3, WAV, M4A等）
- `processed_files.json`に記録されていないか
- CPU使用率が制限値を超えていないか

### Q: 処理速度を上げたい
A: `config.json`で以下を調整：
- `whisper_model`: "large" → "medium" や "small"
- `max_concurrent_files`: 数値を増やす（CPU負荷注意）
- `compute_type`: GPUがある場合は "float16"

### Q: 特定のファイルだけ再処理したい
A: inputフォルダに戻して次回の処理を待つか、UI上で停止→開始

### Q: 起動しているか確認したい
A: UI上で開始していてターミナルウィンドウが閉じられていなければ起動している

### Q: 処理がすぐに始まらない
A: 以下を確認：
- CPU使用率が80%を超えていないか
- 同時処理数の上限に達していないか（デフォルト3ファイル）
- ファイル形式が対応しているか

### Q: 文字起こしの精度を上げたい
A: `whisper_model`を`large`に設定（デフォルト）。ただし処理時間は長くなります。音声自体のクオリティも影響します。

### Q: メモリ不足エラーが出る
A: 以下を試してください：
- `whisper_model`を`medium`や`small`に変更
- `max_concurrent_files`を減らす（例：1〜2）
- `compute_type`を`int8`に設定（デフォルト）

### Q: 日本語以外の音声を処理したい
A: `config.json`の`language`を変更：
- 英語: `"en"`
- 中国語: `"zh"`
- 自動検出: `"auto"`（処理時間増加）

### Q: ログファイルが大きくなりすぎた
A: 手動削除可能

### Q: 処理完了の通知について
A: KoemojiAutoの通知はログファイルに記録される仕様です。
- 全ての通知は`koemoji.log`に「通知:」として記録されます
- 画面への通知（通知センター、ポップアップ等）は表示されません
- 処理状況の確認方法：
  ```bash
  # PowerShellで確認
  Get-Content koemoji.log -Wait | Select-String "通知:"
  
  # コマンドプロンプトで確認
  type koemoji.log | findstr "文字起こし完了"
  ```

## トラブルシューティング

### プロセスが停止しない場合
# 通常の停止方法
WebUIから停止ボタンを使用

# 上記で停止しない場合
```bash
stop_koemoji.bat

# それでも停止しない場合（最終手段）
taskkill /F /IM python.exe  # すべてのPythonプロセスが停止するので注意
```

### ログの確認
koemoji.logを確認する。

### リセット方法
processed_files.jsonを削除する。

```bash
# 処理済みファイルリストをクリア
del processed_files.json
```

## 開発者向け

### テストの実行
```bash
pytest tests/
```

### 開発モード
```bash
python main.py
```

## ライセンス

本ソフトウェアは以下の条件で利用できます：

- **個人利用**: 無料・無制限
- **教育・研究利用**: 無料・無制限  
- **商用利用**: 事前に info.hirokitakamura@gmail.com へご連絡ください

詳細は[LICENSE](LICENSE)ファイルをご確認ください。

## 作者

infoHiroki

## 参考リンク

- [OpenAI Whisper](https://github.com/openai/whisper)
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper)