#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoeMojiAuto - 自動文字起こしシステム (統合版 - シンプルモデル)
音声・動画ファイルから自動で文字起こし - CLIを閉じると処理も停止
"""

import os
import sys
import time
import json
import logging
import shutil
import argparse
import threading
import platform
import atexit
import signal
import psutil
from pathlib import Path

# Windowsかどうかを判定
IS_WINDOWS = platform.system() == 'Windows'

# グローバル変数
config = {}
logger = None
processing_queue = []
files_in_process = set()
whisper_model = None
model_config = None

# 実行状態を管理するグローバル変数
is_running = False
stop_requested = False
processing_thread = None

# 停止フラグファイル（互換性のために残す、起動時に削除）
STOP_FLAG_FILE = "stop_koemoji.flag"

# デフォルト設定
DEFAULT_CONFIG = {
    "input_folder": "input",
    "output_folder": "output", 
    "archive_folder": "archive",
    "scan_interval_minutes": 30,
    "max_concurrent_files": 3,
    "whisper_model": "large",
    "language": "ja",
    "compute_type": "int8",
    "max_cpu_percent": 95
}

#=======================================================================
# 初期化とクリーンアップ
#=======================================================================

def cleanup_on_exit():
    """終了時のクリーンアップ処理"""
    global stop_requested, is_running
    
    # 停止要求フラグを立てる
    stop_requested = True
    is_running = False
    
    # 停止フラグファイルを作成（もし外部から呼ばれた場合のために）
    try:
        if not os.path.exists(STOP_FLAG_FILE):
            with open(STOP_FLAG_FILE, 'w') as f:
                f.write(str(time.time()))
    except:
        pass
        
    # 少し待機してから停止フラグファイルを削除（他のプロセスが読み取る時間を確保）
    time.sleep(0.5)
    
    # 停止フラグファイルが存在すれば削除
    if os.path.exists(STOP_FLAG_FILE):
        try:
            os.remove(STOP_FLAG_FILE)
            if logger:
                logger.info("停止フラグファイルを削除しました")
        except:
            pass
    
    # 処理スレッドが動いていれば最大10秒待つ
    if processing_thread and processing_thread.is_alive():
        processing_thread.join(timeout=10)
    
    if logger:
        logger.info("KoeMojiAutoを終了しました")

def reset_state():
    """状態をリセット - 古いプロセスやフラグを削除"""
    # 停止フラグを削除
    if os.path.exists(STOP_FLAG_FILE):
        try:
            os.remove(STOP_FLAG_FILE)
            print("古い停止フラグファイルを削除しました")
        except:
            print("停止フラグの削除に失敗しました")
    
    # 関連するPythonプロセスを検索して終了
    current_pid = os.getpid()
    killed = False
    
    try:
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                if proc.pid == current_pid:
                    continue
                    
                cmdline = proc.info.get('cmdline')
                if cmdline and len(cmdline) > 1:
                    # koemoji.pyを実行している他のプロセスを探す
                    if any('koemoji.py' in arg for arg in cmdline):
                        proc.terminate()
                        killed = True
                        print(f"関連するプロセス(PID: {proc.pid})を終了しました")
            except:
                pass
    except:
        print("プロセスのクリーンアップに失敗しました")
    
    if killed:
        print("システムをリセットしました。起動を続行します。")
    
    return killed

# 終了時の処理を登録
atexit.register(cleanup_on_exit)

# シグナルハンドラ設定
def signal_handler(sig, frame):
    """シグナル受信時の処理"""
    cleanup_on_exit()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

#=======================================================================
# ロギング・ユーティリティ関数
#=======================================================================

def setup_logging(log_file='koemoji.log', level=logging.INFO):
    """ロギングの設定"""
    global logger
    
    # ハンドラを直接作成してエンコーディングを指定
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s', '%Y-%m-%d %H:%M'))
    
    # ロガーの設定
    logger = logging.getLogger("KoemojiAuto")
    logger.setLevel(level)
    
    # 既存のハンドラがあれば削除（重複ログ防止）
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 新しいハンドラを追加
    logger.addHandler(file_handler)
    
    return logger

def log_and_print(message, level="info", category=None, print_console=True):
    """ログとコンソールの両方に出力（print_console=Falseでログのみ）
    
    カテゴリを指定すると「[カテゴリ] メッセージ」の形式で出力されます。
    カテゴリの例: システム, ファイル, 処理, モデル
    """
    global logger
    
    if logger is None:
        logger = setup_logging()
    
    # カテゴリが指定されている場合はフォーマットを適用
    formatted_message = message
    if category:
        formatted_message = f"[{category}] {message}"
    
    if level == "info":
        logger.info(formatted_message)
    elif level == "error":
        logger.error(formatted_message)
    elif level == "warning":
        logger.warning(formatted_message)
    elif level == "debug":
        logger.debug(message)
        return  # デバッグメッセージはコンソールには出さない
        
    if print_console:
        print(message)  # コンソールにも出力

def ensure_directory(path_str):
    """ディレクトリの存在を確認し、必要に応じて作成"""
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_move_file(source, destination):
    """ファイルを安全に移動（同名ファイル対応）"""
    dest_path = Path(destination)
    
    # 同名ファイルがある場合は名前を変更
    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            dest_path = dest_path.with_name(new_name)
            counter += 1
    
    # 移動実行
    shutil.move(source, str(dest_path))
    return dest_path#=======================================================================
# 設定管理
#=======================================================================

def load_config(config_path="config.json"):
    """設定ファイルを読み込む"""
    global config
    
    try:
        if not os.path.exists(config_path):
            # 初回使用時：デフォルト値を設定
            log_and_print("設定ファイルが見つからないため、デフォルト設定を使用します。")
            config = DEFAULT_CONFIG.copy()
            save_config(config_path)
        else:
            # 設定読み込み
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                log_and_print(f"設定を読み込みました: {config_path}")
            except UnicodeDecodeError:
                # Shift-JISで再試行
                try:
                    with open(config_path, 'r', encoding='shift-jis') as f:
                        config = json.load(f)
                    log_and_print(f"設定を読み込みました（shift-jis）: {config_path}")
                    # 成功したらUTF-8で保存し直す
                    save_config(config_path)
                except:
                    log_and_print("設定ファイルを読み込めませんでした。デフォルト設定を使用します。", "error")
                    config = DEFAULT_CONFIG.copy()
                    save_config(config_path)
            
            # 設定値の検証
            validate_config()
            
        # 入力・出力・アーカイブフォルダの確認と作成
        for folder_key in ["input_folder", "output_folder", "archive_folder"]:
            folder_path = config.get(folder_key)
            ensure_directory(folder_path)
            log_and_print(f"{folder_key}を確認しました: {folder_path}")
                
    except Exception as e:
        log_and_print(f"設定の読み込み中にエラーが発生しました: {e}", "error")
        config = DEFAULT_CONFIG.copy()

def validate_config():
    """設定値の妥当性をチェック"""
    global config
    
    # 必須項目がない場合はデフォルト値を設定
    for key, default in DEFAULT_CONFIG.items():
        if key not in config:
            log_and_print(f"必須設定 '{key}' が見つかりません。デフォルト値 '{default}' を使用します。", "warning")
            config[key] = default

def save_config(config_path="config.json"):
    """設定ファイルを保存"""
    try:
        # 一時ファイルに書き込み
        temp_path = f"{config_path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 成功したら元のファイルを置き換え
        if os.path.exists(temp_path):
            if os.path.exists(config_path):
                os.remove(config_path)
            os.rename(temp_path, config_path)
            logger.info(f"設定ファイルを保存しました: {config_path}")
        
    except Exception as e:
        log_and_print(f"設定の保存中にエラーが発生しました: {e}", "error")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)#=======================================================================
# 文字起こし処理
#=======================================================================

def transcribe_audio(file_path):
    """音声ファイルを文字起こし"""
    global whisper_model, model_config, stop_requested
    
    # 停止要求をチェック（この関数の先頭で確認）
    if stop_requested:
        log_and_print("停止要求を検出したため、文字起こしをキャンセルします", "info", print_console=False)
        return None
    
    start_time = time.time()
    file_name = os.path.basename(file_path)
    
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        log_and_print("faster_whisperがインストールされていません。pip install faster-whisperを実行してください。", "error")
        return None
    
    try:
        # モデルサイズとコンピュートタイプを設定
        model_size = config.get("whisper_model", "large")
        compute_type = config.get("compute_type", "int8")
        
        # モデルが未ロードか設定が変わった場合のみ再ロード
        if (whisper_model is None or 
            model_config != (model_size, compute_type)):
            # モデルロード前に再度停止要求をチェック
            if stop_requested:
                log_and_print("モデルロードをキャンセル（停止要求）", category="モデル", print_console=False)
                return None
                
            log_and_print(f"モデルロード: Whisper {model_size}", category="モデル", print_console=False)
            whisper_model = WhisperModel(model_size, compute_type=compute_type)
            model_config = (model_size, compute_type)
            
            # モデルロード後にも停止要求をチェック
            if stop_requested:
                log_and_print("処理をキャンセル（停止要求）", category="モデル", print_console=False)
                return None
        
        # 文字起こし開始前に再度停止要求をチェック
        if stop_requested:
            log_and_print("処理をキャンセル（停止要求）", category="処理", print_console=False)
            return None
            
        log_and_print(f"音声認識開始: {file_name}", category="処理", print_console=False)
        
        # 文字起こし実行
        segments, info = whisper_model.transcribe(
            file_path,
            language=config.get("language", "ja"),
            beam_size=5,
            best_of=5,
            vad_filter=True
        )
        
        # セグメントをテキストに結合
        transcription = []
        segment_count = 0
        
        for segment in segments:
            segment_count += 1
            transcription.append(segment.text.strip())
            
            # 10セグメントごとに進捗をログに記録
            if segment_count % 10 == 0:
                log_and_print(f"進捗: {segment_count}セグメント処理済み", category="処理", print_console=False)
        
        # 処理時間を計算
        processing_time = time.time() - start_time
        log_and_print(f"文字起こし完了: {file_name} - 合計{segment_count}セグメント (処理時間: {processing_time:.2f}秒)")
        
        return "\n".join(transcription)
    
    except Exception as e:
        log_and_print(f"文字起こし処理中にエラーが発生しました: {e}", "error")
        return None#=======================================================================
# ファイル処理
#=======================================================================

def scan_and_queue_files():
    """入力フォルダをスキャンしてファイルをキューに追加"""
    global processing_queue, stop_requested
    
    if stop_requested:
        return
    
    try:
        logger.debug("入力フォルダのスキャンを開始します")
        
        input_folder = config.get("input_folder")
        if not os.path.exists(input_folder):
            log_and_print(f"入力フォルダが存在しません: {input_folder}", "warning")
            ensure_directory(input_folder)
            return
        
        # メディアファイルの拡張子
        media_extensions = ('.mp3', '.mp4', '.wav', '.m4a', '.mov', '.avi', '.flac', '.ogg', '.aac')
        
        # 新しいファイルを検出
        new_files = []
        for file in os.listdir(input_folder):
            file_path = os.path.join(input_folder, file)
            
            # ディレクトリはスキップ
            if os.path.isdir(file_path):
                continue
            
            # 対象拡張子のファイルのみ処理
            if not file.lower().endswith(media_extensions):
                continue
            
            # 既に処理中またはキュー済みのファイルはスキップ
            if is_file_queued_or_processing(file_path):
                continue
            
            new_files.append(file_path)
        
        if not new_files:
            logger.debug("新しいファイルはありません")
            return
        
        # キューに追加
        for file_path in new_files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # ファイル情報のメタデータを作成
            file_info = {
                "path": file_path,
                "name": file_name,
                "size": file_size,
                "queued_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            processing_queue.append(file_info)
            log_and_print(f"キュー追加: {file_name}", category="キュー", print_console=False)
        
        log_and_print(f"キュー状態: {len(processing_queue)}件待機中", category="キュー", print_console=False)
        
    except Exception as e:
        log_and_print(f"キュースキャン中エラー: {e}", "error", category="キュー")

def is_file_queued_or_processing(file_path):
    """ファイルが既にキューにあるか処理中か確認"""
    if file_path in files_in_process:
        return True
    
    for item in processing_queue:
        if item["path"] == file_path:
            return True
    
    return False

def wait_for_resources(max_wait_seconds=5):
    
    """リソースが利用可能になるまで待機（タイムアウト付き）"""
    global stop_requested
    
    if stop_requested:
        return False
        
    try:
        import psutil
    except ImportError:
        return True  # psutilがない場合は常にリソース利用可能とする
        
    max_cpu = config.get("max_cpu_percent", 95)
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        if stop_requested:
            return False
            
        cpu_percent = psutil.cpu_percent(interval=1)  # 1秒間隔で測定
        
        if cpu_percent <= max_cpu:
            return True  # リソース利用可能
            
        wait_time = min(2, max_wait_seconds - (time.time() - start_time))
        if wait_time <= 0:
            break
            
        log_and_print(f"CPU使用率が高いため待機中: {cpu_percent}% > {max_cpu}% (あと{wait_time:.0f}秒)")
        time.sleep(min(1, wait_time))  # 最大1秒待機
    
    return False  # タイムアウト

def process_next_file():
    """キューの次のファイルを処理"""
    global processing_queue, files_in_process, stop_requested
    
    if stop_requested or not is_running:
        return False
    
    try:
        if not processing_queue:
            return False  # 処理すべきファイルなし
        
        # リソース使用状況を確認
        if not wait_for_resources():
            return False  # リソース不足またはタイムアウト
        
        # 同時処理数を確認
        max_concurrent = config.get("max_concurrent_files", 3)
        if len(files_in_process) >= max_concurrent:
            return False  # 同時処理数の上限
        
        # 次のファイルを取得
        file_info = processing_queue.pop(0)
        file_path = file_info["path"]
        
        # 処理開始
        result = process_file(file_path)
        return result is not None
    
    except Exception as e:
        log_and_print(f"ファイル処理中にエラーが発生しました: {e}", "error")
        return False

def process_file(file_path):
    """ファイルを処理する"""
    global files_in_process, stop_requested
    
    if stop_requested:
        return None
    
    start_time = time.time()
    try:
        # ファイルが存在するか確認
        if not os.path.exists(file_path):
            log_and_print(f"ファイルが存在しません: {file_path}", "warning", category="ファイル")
            return None
        
        # 処理中リストに追加
        files_in_process.add(file_path)
        file_name = os.path.basename(file_path)
        log_and_print(f"処理開始: {file_name}", category="ファイル", print_console=False)
        
        # 文字起こし処理を実行
        transcription = transcribe_audio(file_path)
        
        if stop_requested:
            log_and_print(f"処理中断: {file_name}", "warning", category="ファイル")
            return None
        
        if transcription:
            # 出力ファイルパスを生成
            output_folder = config.get("output_folder")
            output_path = Path(output_folder)
            output_path.mkdir(exist_ok=True)
            
            output_file = output_path / f"{Path(file_name).stem}.txt"
            
            # 結果を保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcription)
            
            # 処理時間を計算
            processing_time = time.time() - start_time
            log_and_print(f"処理完了: {file_name} → {output_file} (処理時間: {processing_time:.2f}秒)", category="ファイル")
            
            # アーカイブフォルダに移動
            archive_folder = config.get("archive_folder", "archive")
            ensure_directory(archive_folder)
            
            archive_path = os.path.join(archive_folder, file_name)
            archive_path = safe_move_file(file_path, archive_path)
            log_and_print(f"アーカイブ: {file_name}", category="ファイル", print_console=False)
            
            return str(output_file)
        else:
            log_and_print(f"処理失敗: {file_name}", "error", category="ファイル")
            return None
    
    except Exception as e:
        log_and_print(f"エラー発生: {file_path} - {e}", "error", category="ファイル")
        return None
    finally:
        # 処理中リストから削除
        if file_path in files_in_process:
            files_in_process.remove(file_path)#=======================================================================
# メイン処理ループとスレッド管理
#=======================================================================

def processing_loop():
    """文字起こし処理のメインループ（スレッドで実行）"""
    global is_running, stop_requested
    
    try:
        log_and_print("文字起こし処理を開始しました", category="システム")
        
        scan_interval = config.get("scan_interval_minutes", 30) * 60  # 秒に変換
        last_scan_time = 0
        
        # 初回スキャン
        scan_and_queue_files()
        
        # メインループ
        while is_running and not stop_requested:
            # 停止フラグファイルのチェック（外部からの停止命令に対応）
            if os.path.exists(STOP_FLAG_FILE):
                log_and_print("停止フラグファイルを検出しました。処理を終了します。", "info")
                try:
                    os.remove(STOP_FLAG_FILE)
                except:
                    pass
                stop_requested = True
                is_running = False
                break  # ループを確実に抜ける
            
            # ファイル処理
            while process_next_file():
                # 処理内でも停止フラグファイルをチェック
                if os.path.exists(STOP_FLAG_FILE):
                    log_and_print("停止フラグファイルを検出しました。処理を終了します。", "info")
                    try:
                        os.remove(STOP_FLAG_FILE)
                    except:
                        pass
                    stop_requested = True
                    is_running = False
                    break
                
                if stop_requested:
                    break
                time.sleep(0.1)  # 短い待機
            
            # 定期的にフォルダをスキャン
            current_time = time.time()
            if current_time - last_scan_time >= scan_interval:
                scan_and_queue_files()
                last_scan_time = current_time
            
            # 短い待機（停止チェックの頻度も兼ねる）
            time.sleep(1)
        
    except Exception as e:
        log_and_print(f"処理ループでエラーが発生しました: {e}", "error", category="システム")
    finally:
        is_running = False
        log_and_print("文字起こし処理を終了しました", category="システム")

def start_processing():
    """文字起こし処理を開始"""
    global is_running, stop_requested, processing_thread
    
    if is_running:
        return False  # 既に実行中
    
    # フラグを設定
    is_running = True
    stop_requested = False
    
    # 処理スレッドを開始
    processing_thread = threading.Thread(target=processing_loop)
    processing_thread.daemon = True  # メインスレッド終了時に自動終了
    processing_thread.start()
    
    return True

def stop_processing():
    """文字起こし処理を停止"""
    global is_running, stop_requested
    
    if not is_running:
        return False  # 既に停止中
    
    # 停止要求フラグを設定
    stop_requested = True
    is_running = False
    
    # 処理中のファイルがあるか確認
    if files_in_process:
        log_and_print("注意: 処理中のファイルは中断できません。完全に停止するには画面を閉じてください。", "warning")
    else:
        log_and_print("処理を停止しました", category="システム")
    
    # 停止フラグファイルを作成して外部プロセスにも通知
    try:
        with open(STOP_FLAG_FILE, 'w') as f:
            f.write(str(time.time()))  # タイムスタンプ付きで作成
    except Exception as e:
        log_and_print(f"停止フラグファイルの作成に失敗しました: {e}", "error")
    
    # ログに停止を記録
    log_and_print("処理停止を要求しました", category="システム", print_console=False)
    
    # CLI側で待機を行うため、ここでは待機しない
    # (終了コマンドの場合はデーモンスレッドとして自動終了する)
    
    return True#=======================================================================
# CLI インターフェース
#=======================================================================

def clear_screen():
    """画面をクリアしてタイトルを設定"""
    # 実行状態を文字列で取得
    status = "実行中" if is_running else "停止中"
    
    if IS_WINDOWS:
        os.system('cls')
        # Windowsでタイトルを設定（状態を含める）
        os.system(f'title KoeMoji-{status}')
    else:
        os.system('clear')
        # Linux/Macではエスケープシーケンスでタイトル設定
        print(f"\033]0;KoeMoji-{status}\007", end="")

def show_recent_logs(lines=10):
    """最新のログを表示"""
    log_path = 'koemoji.log'
    if os.path.exists(log_path):
        try:
            # バイナリモードで読み込み
            with open(log_path, 'rb') as f:
                # ファイルの最後から最大10KB読み込む（十分な行数を確保）
                f.seek(0, 2)  # ファイル末尾に移動
                file_size = f.tell()  # ファイルサイズを取得
                
                # 読み込むサイズを決定（最大10KB、ファイル全体が10KB未満ならファイル全体）
                read_size = min(10240, file_size)
                f.seek(max(0, file_size - read_size), 0)  # 末尾から適切な位置に移動
                
                # データを読み込み
                data = f.read()
            
            # 様々なエンコーディングでデコードを試みる
            encodings = ['utf-8', 'shift-jis', 'cp932', 'euc-jp', 'iso-2022-jp']
            decoded_lines = None
            
            for encoding in encodings:
                try:
                    text = data.decode(encoding)
                    decoded_lines = text.splitlines()
                    break
                except UnicodeDecodeError:
                    continue
                    
            if decoded_lines:
                # 最新の指定行数を表示
                recent_lines = decoded_lines[-lines:] if len(decoded_lines) >= lines else decoded_lines
                for line in recent_lines:
                    print(line.strip())
            else:
                # どのエンコーディングでもデコードできない場合は、省略して表示
                print("ログファイルを読み込めませんでした。ログファイルをリセットすることをお勧めします。")
                # 実用的な対応: 最新の数行だけでも何かを表示する
                print("最新のログ内容の一部（生データ）:")
                for i in range(min(5, lines)):
                    if i < len(data) // 40:  # 40バイトごとに1行として扱う
                        start = max(0, len(data) - (i+1)*40)
                        end = max(0, len(data) - i*40)
                        print(f"[バイナリデータ {start}:{end}]")
        except Exception as e:
            print(f"ログ読み込みエラー: {e}")
    else:
        print("ログファイルがありません")

def get_status_display():
    """ステータス表示文字列を取得"""
    if stop_requested and files_in_process:
        return "⏸ 停止処理中 (処理中ファイルを完了中)"
    elif is_running:
        return "● 実行中"
    else:
        return "○ 停止中"

def display_menu():
    """メニューを表示"""
    print("=" * 40)
    print("     KoeMojiAuto コマンドライン")
    print("=" * 40)
    print(f"状態: {get_status_display()}")
    print("-" * 40)
    print("  1. 開始      - 文字起こしを開始")
    print("  2. 停止      - 文字起こしを停止")
    print("  3. 設定表示  - 現在の設定を確認")
    print("  4. リセット  - 状態を初期化")
    print("  0. 終了      - プログラムを終了")
    print("-" * 40)

def display_cli():
    """CLIインターフェースを表示"""
    global is_running
    
    try:
        while True:
            # 停止フラグファイルをチェック（外部からの停止命令をCLIにも反映）
            if os.path.exists(STOP_FLAG_FILE):
                is_running = False
                try:
                    os.remove(STOP_FLAG_FILE)
                except:
                    pass
                print("外部からの停止シグナルを検出しました。状態を停止に更新します。")
                
            clear_screen()
            display_menu()
            
            # ログ表示領域
            print("\n最新ログ:")
            print("-" * 40)
            show_recent_logs(10)
            print("-" * 40)
            
            # コマンド受付と処理
            choice = input("\n選択> ")
            
            if choice == "1":
                if is_running:
                    print("すでに実行中です")
                else:
                    if start_processing():
                        print("処理を開始しました")
                    else:
                        print("処理の開始に失敗しました")
                input("\nEnterキーで戻る...")
            elif choice == "2":
                if not is_running:
                    print("すでに停止しています")
                else:
                    print("停止中です")
                    
                    # 停止処理を実行
                    stop_result = stop_processing()
                    
                    # 処理中のファイルがあるか確認
                    if files_in_process:
                        print("\n注意: 現在処理中のファイルは中断できません")
                        print("完全に停止するには次の選択肢があります:")
                        print("1. プログラムを終了する (0を選択)")
                        print("2. 画面を閉じる (×ボタン)")
                        print("\n処理中のファイル:")
                        for file_path in files_in_process:
                            print(f" - {os.path.basename(file_path)}")
                    else:
                        # 停止処理中の待機（スレッド終了を待機）
                        if processing_thread and processing_thread.is_alive():
                            for i in range(5):  # 5秒間待機
                                time.sleep(1)
                                print(f"停止中です{'.' * (i+1)}")
                                
                                # スレッドが終了したら待機ループを抜ける
                                if not processing_thread.is_alive():
                                    break
                        
                        if stop_result:
                            print("文字起こし処理を停止しました")
                        else:
                            print("処理の停止に失敗しました")
                input("\nEnterキーで戻る...")
            elif choice == "3":
                print("\n--- 設定内容 ---")
                for key, value in config.items():
                    print(f"{key}: {value}")
                input("\nEnterキーで戻る...")
            elif choice == "4":
                print("\n状態をリセットします...")
                reset_state()
                input("\nEnterキーで戻る...")
            elif choice == "0":
                # 処理中ファイルがある場合は確認
                if files_in_process:
                    print("\n注意: 処理中のファイルがあります")
                    print("プログラムを終了すると、処理は中断されます")
                    confirm = input("終了しますか？ (y/n): ")
                    if confirm.lower() != 'y':
                        continue  # キャンセルしてメニューに戻る
                
                # 実行中なら停止処理
                if is_running:
                    print("停止中です...")
                    stop_processing()
                    
                    # 停止処理中の待機表示
                    if processing_thread and processing_thread.is_alive():
                        for i in range(3):  # 終了前なので短めに
                            time.sleep(1)
                            print(f"停止中です{'.' * (i+1)}")
                
                print("\nプログラムを終了します...")
                sys.exit(0)  # プロセスを確実に終了
            else:
                print("ログを更新しました（無効な選択がログ更新として機能します）")
                input("\nEnterキーで戻る...")
    except Exception as e:
        print(f"CLIの実行中にエラーが発生しました: {e}")
        input("\nEnterキーで終了...")  # エラー時にユーザーに確認を求める#=======================================================================
# メイン実行部分
#=======================================================================

if __name__ == "__main__":
    try:
        # コマンドライン引数の解析
        parser = argparse.ArgumentParser(description="KoeMojiAuto文字起こしツール")
        parser.add_argument("--cli", action="store_true", help="CLIモードで起動")
        parser.add_argument("--reset", action="store_true", help="状態をリセット")
        parser.add_argument("--stop", action="store_true", help="実行中のプロセスを停止")
        args = parser.parse_args()
        
        # --stopオプションの処理（最優先）
        if hasattr(args, 'stop') and args.stop:
            # 停止フラグファイルを作成
            try:
                with open(STOP_FLAG_FILE, 'w') as f:
                    f.write(str(time.time()))  # タイムスタンプ付きで作成
                print("停止シグナルを送信しました。プロセスは直ちに停止します。")
                sys.exit(0)
            except Exception as e:
                print(f"停止シグナルの送信中にエラーが発生しました: {e}")
                sys.exit(1)
        
        # 起動時にシステム状態をリセット（古いプロセスとフラグを削除）
        reset_state()
        
        # ロギング設定
        setup_logging()
        
        # 設定を読み込む
        load_config()
        
        # CLI表示
        display_cli()
        
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        input("\nEnterキーで終了...")