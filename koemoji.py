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
import threading
import platform
import psutil
from pathlib import Path
from collections import deque

# Windowsかどうかを判定
IS_WINDOWS = platform.system() == 'Windows'

# グローバル変数
config = {}
logger = None
processing_queue = []
whisper_model = None
model_config = None  # (model_size, compute_type)のタプルまたはNone

# 実行状態を管理するグローバル変数
is_running = False
stop_requested = False
processing_thread = None

# 実行ディレクトリをベースディレクトリとして使用
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# デフォルト設定
DEFAULT_CONFIG = {
    "input_folder": os.path.join(BASE_DIR, "input"),
    "output_folder": os.path.join(BASE_DIR, "output"), 
    "archive_folder": os.path.join(BASE_DIR, "archive"),
    "scan_interval_minutes": 30,
    "whisper_model": "large",
    "language": "ja",
    "max_cpu_percent": 95,
    "compute_type": "int8",  # CPUでの高速処理（GPUある場合は"auto"推奨）
    "auto_start": False
}

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
        # モデルサイズを設定
        model_size = config.get("whisper_model", "large")
        compute_type = config.get("compute_type", "int8")  # config.jsonから読み込み
        
        # モデルが未ロードか設定が変わった場合のみ再ロード
        if (whisper_model is None or 
            model_config != (model_size, compute_type)):
            # モデルロード前に再度停止要求をチェック
            if stop_requested:
                log_and_print("モデルロードをキャンセル（停止要求）", category="モデル", print_console=False)
                return None
                
            log_and_print(f"モデルロード: Whisper {model_size} (compute_type: {compute_type})", category="モデル", print_console=False)
            
            # モデルをロード（config.jsonの設定を使用）
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
    """ファイルが既にキューにあるか確認"""
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
    global processing_queue, stop_requested
    
    if stop_requested or not is_running:
        return False
    
    try:
        if not processing_queue:
            return False  # 処理すべきファイルなし
        
        # リソース使用状況を確認
        if not wait_for_resources():
            return False  # リソース不足またはタイムアウト
        
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
    global stop_requested
    
    if stop_requested:
        return None
    
    start_time = time.time()
    try:
        # ファイルが存在するか確認
        if not os.path.exists(file_path):
            log_and_print(f"ファイルが存在しません: {file_path}", "warning", category="ファイル")
            return None
        
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

#=======================================================================
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
            # ファイル処理
            while process_next_file():
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


#=======================================================================
# CLI インターフェース
#=======================================================================

def clear_screen():
    """画面をクリアしてタイトルを設定"""
    if IS_WINDOWS:
        os.system('cls')
        os.system('title KoeMoji')
    else:
        os.system('clear')
        # macOS/Linuxでのターミナルタイトル設定
        sys.stdout.write('\033]0;KoeMoji\007')
        sys.stdout.flush()

def show_recent_logs(lines=10):
    """最新のログを表示"""
    log_path = 'koemoji.log'
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                # 最後のN行だけを保持（メモリ効率的）
                recent_lines = deque(f, maxlen=lines)
                
                for line in recent_lines:
                    print(line.strip())
                    
        except Exception as e:
            print(f"ログ読み込みエラー: {e}")
    else:
        print("ログファイルがありません")

def get_status_display():
    """ステータス表示文字列を取得"""
    status = "実行中" if is_running else "停止中"
    status_symbol = "●" if is_running else "○"
    return f"{status_symbol} {status}"

def display_menu():
    """メニューを表示"""
    print("=" * 40)
    print("        K O E M O J I - A U T O")
    print("=" * 40)
    print(f"状態: {get_status_display()}")
    print("-" * 40)
    print("  1. 開始      - 文字起こしを開始")
    print("  2. 設定表示  - 現在の設定を確認")
    print("-" * 40)

def display_auto_mode():
    """自動実行モード時の表示"""
    while True:
        clear_screen()
        print("=" * 40)
        print("    K O E M O J I - A U T O (自動実行中)")
        print("=" * 40)
        print(f"状態: {get_status_display()}")
        print("-" * 40)
        print("\n最新ログ:")
        print("-" * 40)
        show_recent_logs(10)
        print("-" * 40)
        print("\nCtrl+C で終了")
        
        time.sleep(2)  # 2秒ごとに更新

def display_cli():
    """CLIインターフェースを表示"""
    global is_running
    
    # auto_start チェック
    if config.get("auto_start", False):
        log_and_print("自動実行モードで起動しました", category="システム")
        if start_processing():
            try:
                display_auto_mode()
            except KeyboardInterrupt:
                print("\n終了しました")
        else:
            log_and_print("自動実行の開始に失敗しました", level="error", category="システム")
        return
    
    try:
        while True:
            clear_screen()
            display_menu()
            
            # ログ表示領域
            print("\n最新ログ:")
            print("-" * 40)
            show_recent_logs(15)
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
                print("\n--- 設定内容 ---")
                for key, value in config.items():
                    print(f"{key}: {value}")
                input("\nEnterキーで戻る...")
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
        # ロギング設定
        setup_logging()
        
        # 設定を読み込む
        load_config()
        
        # CLIを起動
        display_cli()
        
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        input("\nEnterキーで終了...")