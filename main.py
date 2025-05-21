#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoemojiAuto - 自動文字起こしシステム
音声・動画ファイルの文字起こしを自動処理
"""

import os
import time
import signal
import sys
import platform
import utils
from config_manager import ConfigManager
from file_handler import FileHandler
from transcription_engine import TranscriptionEngine

class KoemojiApp:
    def __init__(self, config_path="config.json"):
        """初期化"""
        self.config_manager = ConfigManager(config_path)
        self.file_handler = FileHandler(self.config_manager)
        self.transcription_engine = TranscriptionEngine(self.config_manager)
    
    def is_already_running(self):
        """既に実行中かチェック"""
        import psutil
        
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                if proc.pid == current_pid:
                    continue
                    
                cmdline = proc.info.get('cmdline')
                if cmdline and len(cmdline) > 1:
                    # PythonまたはPython3プロセスであることを確認
                    if 'python' in cmdline[0].lower() or 'python3' in cmdline[0].lower():
                        # main.pyを実行しているかチェック
                        for arg in cmdline[1:]:
                            if arg.endswith('main.py'):
                                utils.logger.debug(f"既存のプロセスを検出: PID={proc.pid}")
                                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return False
    
    def clear_old_flags(self):
        """古い停止フラグがあれば削除"""
        flag_path = utils.get_stop_flag_path()
        if os.path.exists(flag_path):
            os.remove(flag_path)
            utils.log_and_print("古い停止フラグを削除しました")
    
    def run(self):
        """メイン処理ループ"""
        try:
            stop_flag_path = utils.get_stop_flag_path()
            
            # 既に実行中かチェック
            if self.is_already_running():
                utils.log_and_print("既に別のKoemojiAutoプロセスが実行中です。", "error")
                return            
            # 起動時に古い停止フラグを削除
            self.clear_old_flags()
            
            utils.log_and_print("KoemojiAuto処理を開始しました")
            
            # 24時間連続モードで動作
            utils.log_and_print("24時間連続モードで動作します")
            
            scan_interval = self.config_manager.get("scan_interval_minutes", 30) * 60  # 秒に変換
            last_scan_time = 0
            
            # 初回スキャン
            self.file_handler.scan_and_queue_files()
            self.file_handler.process_queued_files(self.transcription_engine)
            
            # メインループ（24時間動作）
            while True:
                # 停止フラグを確認
                if os.path.exists(stop_flag_path):
                    utils.log_and_print("停止フラグが検出されました。処理を終了します")
                    break
                
                current_time = time.time()
                
                # 定期的にファイルをスキャン
                if current_time - last_scan_time >= scan_interval:
                    self.file_handler.scan_and_queue_files()
                    last_scan_time = current_time
                
                # キューのファイルを処理
                self.file_handler.process_queued_files(self.transcription_engine)
                
                # 短い待機（フラグファイルチェックの頻度も兼ねる）
                time.sleep(5)
            
        except KeyboardInterrupt:
            utils.log_and_print("停止シグナルを受信しました")
        except Exception as e:
            utils.log_and_print(f"処理中にエラーが発生しました: {e}", "error")
        finally:
            # 終了時にフラグファイルを削除
            if 'stop_flag_path' in locals() and os.path.exists(stop_flag_path):
                os.remove(stop_flag_path)
                utils.log_and_print("停止フラグを削除しました")
            
            utils.log_and_print("KoemojiAutoを終了しました")


# 実行例
if __name__ == "__main__":
    # シグナルハンドラーの設定
    def signal_handler(sig, frame):
        utils.log_and_print("停止シグナルを受信しました")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    app = KoemojiApp()
    app.run()