#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoemojiAuto - ファイル処理モジュール
入力フォルダの監視、ファイルキューの管理、処理済みファイルのアーカイブ
"""

import os
import time
from pathlib import Path
import psutil
import utils

class FileHandler:
    def __init__(self, config_manager):
        """初期化"""
        self.config = config_manager
        self.processing_queue = []
        self.files_in_process = set()
    
    def scan_and_queue_files(self):
        """入力フォルダをスキャンしてファイルをキューに追加"""
        try:
            utils.logger.debug("入力フォルダのスキャンを開始します")
            
            input_folder = self.config.get("input_folder")
            if not os.path.exists(input_folder):
                utils.log_and_print(f"入力フォルダが存在しません: {input_folder}", "warning")
                utils.ensure_directory(input_folder)
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
                if self.is_file_queued_or_processing(file_path):
                    continue
                
                new_files.append(file_path)
            
            if not new_files:
                utils.logger.debug("新しいファイルはありません")
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
                
                self.processing_queue.append(file_info)
                utils.log_and_print(f"キューに追加: {file_name}")
            
            utils.log_and_print(f"現在のキュー: {len(self.processing_queue)}件")
            
        except Exception as e:
            utils.log_and_print(f"キュースキャン中にエラーが発生しました: {e}", "error")    
    def is_file_queued_or_processing(self, file_path):
        """ファイルが既にキューにあるか処理中か確認"""
        if file_path in self.files_in_process:
            return True
        
        for item in self.processing_queue:
            if item["path"] == file_path:
                return True
        
        return False
    
    def wait_for_resources(self, max_wait_seconds=30):
        """リソースが利用可能になるまで待機（タイムアウト付き）"""
        max_cpu = self.config.get("max_cpu_percent", 95)
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            cpu_percent = psutil.cpu_percent(interval=1)  # 1秒間隔で測定
            
            if cpu_percent <= max_cpu:
                return True  # リソース利用可能
                
            wait_time = min(5, max_wait_seconds - (time.time() - start_time))
            if wait_time <= 0:
                break
                
            utils.log_and_print(f"CPU使用率が高いため待機中: {cpu_percent}% > {max_cpu}% (あと{wait_time:.0f}秒)")
            time.sleep(min(2, wait_time))  # 最大2秒待機
        
        return False  # タイムアウト
    
    def process_queued_files(self, transcription_engine):
        """キューにあるファイルを処理"""
        try:
            if not self.processing_queue:
                utils.logger.debug("処理すべきファイルはありません")
                return
            
            # リソース使用状況を確認
            if not self.wait_for_resources():
                utils.log_and_print("リソース待機がタイムアウトしました。次回に処理を延期します。", "warning")
                return
            
            # 同時処理数を確認
            max_concurrent = self.config.get("max_concurrent_files", 3)
            current_running = len(self.files_in_process)
            available_slots = max(0, max_concurrent - current_running)
            
            if available_slots <= 0:
                utils.logger.debug("同時処理数の上限に達しています")
                return
            
            # 処理するファイル数を決定
            files_to_process = self.processing_queue[:available_slots]
            
            # ファイルを処理
            for file_info in files_to_process:
                file_path = file_info["path"]
                # キューから削除
                self.processing_queue = [f for f in self.processing_queue if f["path"] != file_path]
                
                # 処理開始
                self.process_file(file_path, transcription_engine)
        
        except Exception as e:
            utils.log_and_print(f"キュー処理中にエラーが発生しました: {e}", "error")
    def process_file(self, file_path, transcription_engine):
        """ファイルを処理する"""
        start_time = time.time()
        try:
            # ファイルが存在するか確認
            if not os.path.exists(file_path):
                utils.log_and_print(f"ファイルが存在しません: {file_path}", "warning")
                return
            
            # 処理中リストに追加
            self.files_in_process.add(file_path)
            file_name = os.path.basename(file_path)
            utils.log_and_print(f"ファイル処理開始: {file_name}")
            
            # 文字起こし処理を実行
            transcription = transcription_engine.transcribe(file_path)
            
            if transcription:
                # 出力ファイルパスを生成
                output_folder = self.config.get("output_folder")
                output_path = Path(output_folder)
                output_path.mkdir(exist_ok=True)
                
                output_file = output_path / f"{Path(file_name).stem}.txt"
                
                # 結果を保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                
                # 処理時間を計算
                processing_time = time.time() - start_time
                utils.log_and_print(f"文字起こし完了: {file_name} -> {output_file} (処理時間: {processing_time:.2f}秒)")
                
                # アーカイブフォルダに移動
                archive_folder = self.config.get("archive_folder", "archive")
                utils.ensure_directory(archive_folder)
                
                archive_path = os.path.join(archive_folder, file_name)
                archive_path = utils.safe_move_file(file_path, archive_path)
                utils.log_and_print(f"アーカイブ: {file_name} -> {archive_path}")
                
                return str(output_file)
            else:
                utils.log_and_print(f"文字起こし失敗: {file_name}", "error")
                return None
        
        except Exception as e:
            utils.log_and_print(f"ファイル処理中にエラーが発生しました: {file_path} - {e}", "error")
            return None
        finally:
            # 処理中リストから削除
            if file_path in self.files_in_process:
                self.files_in_process.remove(file_path)
    
    def get_queue_status(self):
        """キューと処理中のファイル状況を取得"""
        return {
            "queued": len(self.processing_queue),
            "processing": len(self.files_in_process),
            "queue_items": self.processing_queue,
            "processing_items": list(self.files_in_process)
        }