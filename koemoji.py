#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoeMojiAuto - 自動文字起こしシステム (統合版)
音声・動画ファイルから自動で文字起こしを行うツール
"""

import os
import sys
import time
import json
import logging
import shutil
import argparse
import subprocess
import platform
from pathlib import Path

# Windowsかどうかを判定
IS_WINDOWS = platform.system() == 'Windows'

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

# グローバル変数
config = None
logger = None
processing_queue = []
files_in_process = set()
whisper_model = None
model_config = None

# フラグ設定
STOP_FLAG_FILE = "stop_koemoji.flag"

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

def log_and_print(message, level="info"):
    """ログとコンソールの両方に出力"""
    global logger
    
    if logger is None:
        logger = setup_logging()
    
    if level == "info":
        logger.info(message)
    elif level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
        return  # デバッグメッセージはコンソールには出さない
        
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
    return dest_path

def check_if_running():
    """停止フラグファイルが存在しないか確認"""
    return not os.path.exists(STOP_FLAG_FILE)

def is_already_running():
    """既に実行中かチェック"""
    try:
        import psutil
    except ImportError:
        log_and_print("psutilがインストールされていません", "warning")
        return False
        
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if proc.pid == current_pid:
                continue
                
            cmdline = proc.info.get('cmdline')
            if cmdline and len(cmdline) > 1:
                # PythonまたはPython3プロセスであることを確認
                if 'python' in cmdline[0].lower() or 'python3' in cmdline[0].lower():
                    # koemoji.pyを実行しているかチェック
                    for arg in cmdline[1:]:
                        if arg.endswith('koemoji.py') and '--cli' not in cmdline:
                            logger.debug(f"既存のプロセスを検出: PID={proc.pid}")
                            return True
        except:
            pass
    
    return False#=======================================================================
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
            os.remove(temp_path)

#=======================================================================
# 文字起こし処理
#=======================================================================

def transcribe_audio(file_path):
    """音声ファイルを文字起こし"""
    global whisper_model, model_config
    
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
            log_and_print(f"Whisperモデルをロード中: {model_size}")
            whisper_model = WhisperModel(model_size, compute_type=compute_type)
            model_config = (model_size, compute_type)
        
        log_and_print(f"文字起こし開始: {file_name}")
        
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
                log_and_print(f"文字起こし進行中: {file_name} - {segment_count}セグメント処理済み")
        
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
    global processing_queue
    
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
            log_and_print(f"キューに追加: {file_name}")
        
        log_and_print(f"現在のキュー: {len(processing_queue)}件")
        
    except Exception as e:
        log_and_print(f"キュースキャン中にエラーが発生しました: {e}", "error")

def is_file_queued_or_processing(file_path):
    """ファイルが既にキューにあるか処理中か確認"""
    if file_path in files_in_process:
        return True
    
    for item in processing_queue:
        if item["path"] == file_path:
            return True
    
    return False

def wait_for_resources(max_wait_seconds=30):
    """リソースが利用可能になるまで待機（タイムアウト付き）"""
    try:
        import psutil
    except ImportError:
        return True  # psutilがない場合は常にリソース利用可能とする
        
    max_cpu = config.get("max_cpu_percent", 95)
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        cpu_percent = psutil.cpu_percent(interval=1)  # 1秒間隔で測定
        
        if cpu_percent <= max_cpu:
            return True  # リソース利用可能
            
        wait_time = min(5, max_wait_seconds - (time.time() - start_time))
        if wait_time <= 0:
            break
            
        log_and_print(f"CPU使用率が高いため待機中: {cpu_percent}% > {max_cpu}% (あと{wait_time:.0f}秒)")
        time.sleep(min(2, wait_time))  # 最大2秒待機
    
    return False  # タイムアウト

def process_queued_files():
    """キューにあるファイルを処理"""
    global processing_queue, files_in_process
    
    try:
        if not processing_queue:
            logger.debug("処理すべきファイルはありません")
            return
        
        # リソース使用状況を確認
        if not wait_for_resources():
            log_and_print("リソース待機がタイムアウトしました。次回に処理を延期します。", "warning")
            return
        
        # 同時処理数を確認
        max_concurrent = config.get("max_concurrent_files", 3)
        current_running = len(files_in_process)
        available_slots = max(0, max_concurrent - current_running)
        
        if available_slots <= 0:
            logger.debug("同時処理数の上限に達しています")
            return
        
        # 処理するファイル数を決定
        files_to_process = processing_queue[:available_slots]
        
        # ファイルを処理
        for file_info in files_to_process:
            file_path = file_info["path"]
            # キューから削除
            processing_queue = [f for f in processing_queue if f["path"] != file_path]
            
            # 処理開始
            process_file(file_path)
    
    except Exception as e:
        log_and_print(f"キュー処理中にエラーが発生しました: {e}", "error")def process_file(file_path):
    """ファイルを処理する"""
    global files_in_process
    
    start_time = time.time()
    try:
        # ファイルが存在するか確認
        if not os.path.exists(file_path):
            log_and_print(f"ファイルが存在しません: {file_path}", "warning")
            return
        
        # 処理中リストに追加
        files_in_process.add(file_path)
        file_name = os.path.basename(file_path)
        log_and_print(f"ファイル処理開始: {file_name}")
        
        # 文字起こし処理を実行
        transcription = transcribe_audio(file_path)
        
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
            log_and_print(f"文字起こし完了: {file_name} -> {output_file} (処理時間: {processing_time:.2f}秒)")
            
            # アーカイブフォルダに移動
            archive_folder = config.get("archive_folder", "archive")
            ensure_directory(archive_folder)
            
            archive_path = os.path.join(archive_folder, file_name)
            archive_path = safe_move_file(file_path, archive_path)
            log_and_print(f"アーカイブ: {file_name} -> {archive_path}")
            
            return str(output_file)
        else:
            log_and_print(f"文字起こし失敗: {file_name}", "error")
            return None
    
    except Exception as e:
        log_and_print(f"ファイル処理中にエラーが発生しました: {file_path} - {e}", "error")
        return None
    finally:
        # 処理中リストから削除
        if file_path in files_in_process:
            files_in_process.remove(file_path)

#=======================================================================
# メイン処理ループ
#=======================================================================

def run_main_process():
    """メイン処理ループを実行"""
    try:
        # 停止フラグがあれば削除
        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)
            log_and_print("古い停止フラグを削除しました")
        
        # 既に実行中かチェック
        if is_already_running():
            log_and_print("既に別のKoemojiAutoプロセスが実行中です。", "error")
            return
        
        log_and_print("KoemojiAuto処理を開始しました")
        log_and_print("24時間連続モードで動作します")
        
        scan_interval = config.get("scan_interval_minutes", 30) * 60  # 秒に変換
        last_scan_time = 0
        
        # 初回スキャン
        scan_and_queue_files()
        process_queued_files()
        
        # メインループ（24時間動作）
        while True:
            # 停止フラグを確認
            if os.path.exists(STOP_FLAG_FILE):
                log_and_print("停止フラグが検出されました。処理を終了します")
                break
            
            current_time = time.time()
            
            # 定期的にファイルをスキャン
            if current_time - last_scan_time >= scan_interval:
                scan_and_queue_files()
                last_scan_time = current_time
            
            # キューのファイルを処理
            process_queued_files()
            
            # 短い待機（フラグファイルチェックの頻度も兼ねる）
            time.sleep(5)
        
    except KeyboardInterrupt:
        log_and_print("停止シグナルを受信しました")
    except Exception as e:
        log_and_print(f"処理中にエラーが発生しました: {e}", "error")
    finally:
        # 終了時にフラグファイルを削除
        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)
            log_and_print("停止フラグを削除しました")
        
        log_and_print("KoemojiAutoを終了しました")#=======================================================================
# CLI インターフェース
#=======================================================================

def clear_screen():
    """画面をクリア"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_recent_logs(lines=7):
    """最新のログを表示"""
    log_path = 'koemoji.log'
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
                for line in recent_lines:
                    print(line.strip())
        except Exception as e:
            print(f"ログ読み込みエラー: {e}")
    else:
        print("ログファイルがありません")

def get_status_display():
    """ステータス表示文字列を取得"""
    running = check_if_running()
    status = "実行中" if running else "停止中"
    status_symbol = "●" if running else "○"
    return f"{status_symbol} {status}"

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
    print("  0. 終了      - プログラムを終了")
    print("-" * 40)

def display_cli():
    """CLIインターフェースを表示"""
    # 設定を読み込む
    load_config()
    
    while True:
        clear_screen()
        display_menu()
        
        # ログ表示領域
        print("\n最新ログ:")
        print("-" * 40)
        show_recent_logs(5)  # 最新の5行だけ表示
        print("-" * 40)
        
        # コマンド受付と処理
        choice = input("\n選択> ")
        
        if choice == "1":
            # Windowsの場合は独自の起動方法
            if IS_WINDOWS:
                # 非表示でプロセスを起動
                subprocess.Popen([sys.executable, sys.argv[0]], 
                                creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Unix系はバックグラウンドで起動
                subprocess.Popen([sys.executable, sys.argv[0], "&"], 
                                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print("KoemojiAutoを開始しました")
            input("\nEnterキーで戻る...")
        elif choice == "2":
            # 停止フラグを作成
            with open(STOP_FLAG_FILE, 'w') as f:
                f.write("1")
            print("停止フラグを作成しました。プログラムは次のサイクルで終了します。")
            input("\nEnterキーで戻る...")
        elif choice == "3":
            print("\n--- 設定内容 ---")
            for key, value in config.items():
                print(f"{key}: {value}")
            input("\nEnterキーで戻る...")
        elif choice == "0":
            break
        else:
            print("無効な選択です")
            input("\nEnterキーで戻る...")

#=======================================================================
# メイン実行部分
#=======================================================================

if __name__ == "__main__":
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="KoeMojiAuto文字起こしツール")
    parser.add_argument("--cli", action="store_true", help="CLIモードで起動")
    parser.add_argument("--stop", action="store_true", help="文字起こしを停止")
    args = parser.parse_args()
    
    # ロギング設定
    setup_logging()
    
    # 引数に基づいて処理を選択
    if args.cli:
        # CLIモードで起動
        display_cli()
    elif args.stop:
        # 停止フラグを作成
        with open(STOP_FLAG_FILE, 'w') as f:
            f.write("1")
        print("停止フラグを作成しました。プログラムは次のサイクルで終了します。")
    else:
        # 文字起こし処理を実行
        load_config()
        run_main_process()