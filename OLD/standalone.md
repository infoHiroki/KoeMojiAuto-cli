承知いたしました。KISS原則 (Keep It Simple, Stupid) に基づき、PyInstallerでの `.exe` 化を前提としたシンプルな設計案を以下に提案します。複雑なバッチファイルの連鎖や動的生成を極力排除し、`.exe` 単体とその設定ファイルで完結することを目指します。

**KoeMojiAuto シンプル設計案 (for .exe)**

**1. 基本方針:**

*   **単一実行ファイル:** `KoeMojiAuto.exe` をユーザーが直接実行する。
*   **設定ファイル:** `KoeMojiAuto.exe` と同じディレクトリに `config.json` を配置・使用する。初回起動時に `config.json.sample` (同梱) から自動生成する。
*   **ログファイル:** `KoeMojiAuto.exe` と同じディレクトリに `koemoji.log` を出力する。
*   **作業フォルダ:** `input`, `output`, `archive` フォルダは、`config.json` で指定された相対パスまたは絶対パスに基づき、実行時にプログラムが確認・作成する。デフォルトは `.exe` と同じ階層。
*   **外部依存 (FFMPEG):** ユーザーに別途インストールしてもらい、システムのPATHを通してもらうか、`config.json` で FFMPEG の実行ファイルパスを指定できるようにする。アプリケーション側では FFMPEG の存在チェックと、見つからない場合のエラー表示を行う。
*   **コマンドライン引数:** 主要な操作（停止、リセット）はコマンドライン引数でサポートする。
*   **再起動:** プログラム自身が内部ロジックで再起動処理を行う。

**2. ファイル構成 (配布物イメージ):**

```
KoeMojiAuto/
├── KoeMojiAuto.exe          (PyInstallerでビルドされた実行ファイル)
├── config.json.sample     (設定ファイルのテンプレート、同梱)
├── LICENSE
├── README.md                (使い方、FFMPEGのインストール方法などを記載)
└── (オプション) ffmpeg/      (もしFFMPEGを同梱する場合のフォルダ)
    ├── bin/
    │   ├── ffmpeg.exe
    │   └── ffprobe.exe
    └── ... (その他ffmpeg関連ファイル)
```
*   `input`, `output`, `archive` フォルダは、初回起動時や必要に応じて `.exe` と同じ階層に自動生成されるか、ユーザーが作成する。

**3. `koemoji.py` (メインスクリプト) の主な変更点・機能:**

*   **起動処理 (`if __name__ == "__main__":`)**
    *   コマンドライン引数の解析 (`argparse` を使用):
        *   `--cli` (デフォルト): 通常のCLIモードで起動。
        *   `--stop`: 実行中の `KoeMojiAuto.exe` プロセスに停止を指示 (後述のプロセス間通信またはフラグファイルを利用)。
        *   `--reset`: `reset_state()` を実行 (既存のロジックを流用、ただしプロセス終了は自分自身に対しては行わない)。
        *   (オプション) `--autostart`: 起動後、自動的に処理を開始する。
    *   `config.json` の読み込み:
        *   まず `.exe` と同じディレクトリで `config.json` を探す。
        *   見つからなければ `config.json.sample` (同梱データとしてアクセス) を `config.json` としてコピー・生成する。
    *   ロギング設定 (`setup_logging`)。
    *   必要な作業フォルダ (`input`, `output`, `archive`) を確認・作成 (`ensure_directory`)。
    *   `--stop` 引数が指定された場合は、停止処理を実行して終了。
    *   `--reset` 引数が指定された場合は、リセット処理を実行して終了。
    *   それ以外の場合（通常起動）は `display_cli()` を呼び出す。

*   **`reset_state()` 関数の変更:**
    *   古い `stop_koemoji.flag` の削除は維持。
    *   **他の `koemoji.py` (または `KoeMojiAuto.exe`) プロセスを終了するロジックは、`--reset` 引数で起動された場合に限り、慎重に検討する。** 基本的には、複数起動を許容しないのであれば、起動時に二重起動チェックを行う方がシンプル。ここでは、他のプロセス終了ロジックは一旦「削除」または「無効化」する方向でシンプル化を検討。

*   **`display_cli()` (CLIインターフェース):**
    *   「1. 開始」: `start_processing()` を呼び出す。
    *   「2. 停止」: `stop_processing_and_restart()` (新設または改名) を呼び出す。
    *   「3. 設定表示」: `config` の内容を表示。
    *   「4. リセット」: `reset_state()` を呼び出し、ユーザーに再起動を促すか、自動で再起動する。

*   **`start_processing()`:**
    *   処理スレッドを開始する (既存ロジック)。

*   **`stop_processing_and_restart()` (旧 `stop_processing` から改名または新設):**
    *   `stop_requested = True` を設定。
    *   `is_running = False` を設定。
    *   `log_and_print` で停止と再起動を通知。
    *   `restart_application()` を呼び出す。

*   **`restart_application()`:**
    *   `subprocess.Popen([sys.executable] + sys.argv)` で自分自身を再起動。
    *   `os._exit(0)` で現在のプロセスを終了。

*   **`processing_loop()`:**
    *   `STOP_FLAG_FILE` (外部からの停止用) のチェックは削除、またはコマンドライン引数 `--stop` による停止メカニズムに統一する。シンプルにするなら、外部ファイルによる停止は削除。CLIからの停止とCtrl+Cでの終了に絞る。
    *   ループ内の再起動ロジックは `stop_requested` フラグと `is_running` フラグで制御し、ループ終了後に `restart_application()` が呼ばれる流れにする（CLIの「停止」メニュー経由）。

*   **`transcribe_audio()`:**
    *   FFMPEGの呼び出し部分:
        *   まず `config.json` で指定された FFMPEG パス (もしあれば) を試す。
        *   次に、同梱された FFMPEG パス (もし同梱する場合) を試す。
        *   最後に、システムのPATHから `ffmpeg` を探す。
        *   見つからなければエラーメッセージを表示し、処理を中断する。

*   **ファイルパスの解決 (`resource_path` 関数):**
    *   `config.json.sample` や、将来的に `static` フォルダ内のリソース (アイコン等) にアクセスするために、`sys._MEIPASS` を考慮したパス解決関数を用意する (前述の `resource_path` 関数のようなもの)。

**4. PyInstaller ビルド設定 (`.spec` ファイルまたはコマンドライン):**

*   **基本:** `--name KoeMojiAuto`
*   **モード:** `--onedir` (最初はこれがデバッグしやすい) または `--onefile` (配布時はこちらが便利)。
*   **データ同梱 (`--add-data`):**
    *   `config.json.sample`
    *   (もしあれば) `static` フォルダ
    *   `LICENSE`, `README.md` (これらはインストーラで含めるのでも良いが、`.exe` と一緒に配布するなら同梱も可)
*   **アイコン (`--icon`):** アプリケーションアイコンを指定。
*   **コンソール:** CLIアプリなので、コンソールは表示する (デフォルト、または `--noconsole` は指定しない)。

**5. 外部からのプロセス停止 (`--stop` 引数):**

*   **課題:** 実行中の `KoeMojiAuto.exe` を、別のターミナルから `KoeMojiAuto.exe --stop` で安全に停止させる方法。
*   **シンプルな方法:**
    1.  起動時に `.exe` と同じディレクトリに `koemoji.pid` (プロセスIDファイル) を作成する。
    2.  `KoeMojiAuto.exe --stop` が実行されたら、`koemoji.pid` を読み込み、そのプロセスIDに対してシグナルを送る (Windowsでは難しい) か、あるいは `koemoji.stoprequest` のようなフラグファイルを作成する。
    3.  実行中のメインプロセスは、定期的に `koemoji.stoprequest` ファイルの存在をチェックし、あれば停止処理を開始して自身も再起動する。
    *   **よりシンプルな代替案:** `STOP_FLAG_FILE` (`stop_koemoji.flag`) をシンプルに復活させる。`--stop` 引数はこのファイルを作成するだけ。メインループはこれを定期的にチェックする。CLIからの停止もこれを利用。これにより、外部からの停止とCLIからの停止が同じメカニズムになる。

**KISS原則に沿ったポイント:**

*   **バッチファイル依存の排除:** `.exe` 実行とコマンドライン引数に機能を集中。
*   **単一の設定源:** `config.json` で動作を制御。
*   **明確なファイル配置:** `.exe` と同階層に必要なファイルを置く。
*   **エラー処理:** FFMPEGが見つからないなど、主要な問題はユーザーに分かりやすく通知する。
*   **再起動の単純化:** プログラム自身のロジックで完結させる。
*   **外部からの停止の単純化:** 共通のフラグファイル (`stop_koemoji.flag`) を利用する。

**この設計に基づいた実装ステップの提案:**

1.  まず、`koemoji.py` 内の再起動ロジック (`restart_application`) を実装・テスト。
2.  次に、`config.json` の初回生成ロジックを実装・テスト。
3.  コマンドライン引数 (`--stop`, `--reset`) の処理を実装・テスト。`--stop` は `stop_koemoji.flag` を作成するようにする。
4.  `processing_loop` 内の `STOP_FLAG_FILE` チェックを復活させ、CLIの「停止」もこのフラグを利用するようにする。
5.  FFMPEGのパス解決ロジックを検討・実装 (まずはPATH依存からでOK)。
6.  上記がPythonスクリプトとして動作することを確認したら、PyInstallerでビルドし、`.exe` としてテスト。
7.  パス解決関数 (`resource_path`) を導入し、`--add-data` で同梱するファイルへのアクセスを修正。
8.  `README.md` に使い方、FFMPEGの準備方法を記載。