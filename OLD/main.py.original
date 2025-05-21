#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoemojiAuto - 自動文字起こしシステム
音声・動画ファイルの文字起こしを自動処理
"""

import os
import time
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime, time as datetime_time
import psutil
import signal
import sys
import platform

# OS判定  
IS_WINDOWS = platform.system() == 'Windows'

# ロギング設定
logging.basicConfig(
    filename='koemoji.log',
    level=logging.INFO,
    format='%(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M'
)
logger = logging.getLogger("KoemojiAuto")

class KoemojiProcessor:
    def __init__(self, config_path="config.json"):
        """初期化"""
        self.config_path = config_path
        self.load_config()
        self.processing_queue = []
        
        # 処理中のファイル
        self.files_in_process = set()
        
        # Whisperモデルのキャッシュ
        self._whisper_model = None
        self._model_config = None
    
    
    def load_config(self):
        """設定ファイルを読み込む（エンコーディング問題に対応）"""
        try:
            if not os.path.exists(self.config_path):
                # 初回使用時：デフォルト値を設定
                logger.info("設定ファイルが見つからないため、デフォルト設定を使用します。")
                
                # デフォルト設定を作成
                self.config = {
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
                # 設定を保存
                self.save_config()
                logger.info(f"設定を作成しました: {self.config_path}")
                print(f"\n設定が保存されました: {self.config_path}")
            else:
                # 複数のエンコーディングを試行
                encodings = ['utf-8', 'shift-jis', 'cp932', 'euc-jp']
                config_loaded = False
                
                for encoding in encodings:
                    try:
                        with open(self.config_path, 'r', encoding=encoding) as f:
                            self.config = json.load(f)
                        logger.info(f"設定を読み込みました（{encoding}）: {self.config_path}")
                        config_loaded = True
                        
                        # 読み込み成功したら、パスを正規化して UTF-8 で保存し直す
                        self.normalize_paths()
                        self.save_config()
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError) as e:
                        logger.debug(f"{encoding}でのデコード失敗: {e}")
                        continue
                
                if not config_loaded:
                    logger.error("設定ファイルを読み込めませんでした。デフォルト設定を使用します。")
                    # デフォルト設定
                    self.config = {
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
                    # 設定を保存
                    self.save_config()
                
                # 設定値の検証
                self.validate_config()
                
            # 入力・出力・アーカイブフォルダの確認と作成
            for folder_key in ["input_folder", "output_folder", "archive_folder"]:
                folder_path = self.config.get(folder_key)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)
                    logger.info(f"{folder_key}を作成しました: {folder_path}")
                    
            # レポートフォルダの作成（不要になったため削除）
                    
        except Exception as e:
            logger.error(f"設定の読み込み中にエラーが発生しました: {e}")
            # 最小限のデフォルト設定
            self.config = {
                "input_folder": "input",
                "output_folder": "output",
                "archive_folder": "archive",
                "max_concurrent_files": 1,
                "whisper_model": "tiny",
                "language": "ja"
            }
    
    def validate_config(self):
        """設定値の妥当性をチェック（必須項目がない場合はデフォルト値を設定）"""
        # 必須項目とデフォルト値を設定
        required_defaults = {
            "input_folder": "input",
            "output_folder": "output", 
            "whisper_model": "large",
            "language": "ja",
            "archive_folder": "archive",
            "scan_interval_minutes": 30,
            "max_concurrent_files": 3,
            "max_cpu_percent": 95,
            "compute_type": "int8"
        }
        
        # 必須項目がない場合はデフォルト値を設定
        for key, default in required_defaults.items():
            if key not in self.config:
                logger.warning(f"必須設定 '{key}' が見つかりません。デフォルト値 '{default}' を使用します。")
                self.config[key] = default
        
        # 設定更新後、再保存
        self.save_config()
                
    def normalize_paths(self):
        """パス設定を正規化する"""
        path_keys = ["input_folder", "output_folder", "archive_folder"]
        
        for key in path_keys:
            if key in self.config:
                try:
                    # パスオブジェクトに変換して正規化
                    path = Path(self.config[key]).resolve()
                    # 文字列に戻す（これによりプラットフォームに適したパス区切り文字が使用される）
                    self.config[key] = str(path)
                    logger.debug(f"パスを正規化: {key} = {self.config[key]}")
                except Exception as e:
                    logger.warning(f"パスの正規化に失敗: {key} = {self.config[key]}, エラー: {e}")
    
    def save_config(self):
        """設定ファイルを保存（UTF-8で確実に保存）"""
        try:
            # 保存前に必要な変換処理
            config_to_save = self.config.copy()
            
            # 一時ファイルに書き込み
            temp_path = f"{self.config_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            # 成功したら元のファイルを置き換え
            if os.path.exists(temp_path):
                if os.path.exists(self.config_path):
                    os.remove(self.config_path)
                os.rename(temp_path, self.config_path)
                logger.info(f"設定ファイルを保存しました: {self.config_path}")
            
        except Exception as e:
            logger.error(f"設定の保存中にエラーが発生しました: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
    
    
    
    
    def scan_and_queue_files(self):
        """入力フォルダをスキャンしてファイルをキューに追加"""
        try:
            logger.debug("入力フォルダのスキャンを開始します")
            
            input_folder = self.config.get("input_folder")
            if not os.path.exists(input_folder):
                logger.warning(f"入力フォルダが存在しません: {input_folder}")
                os.makedirs(input_folder, exist_ok=True)
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
                if file_path in self.files_in_process or any(f["path"] == file_path for f in self.processing_queue):
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
                    "queued_at": datetime.now().isoformat()
                }
                
                self.processing_queue.append(file_info)
                logger.info(f"キューに追加: {file_name}")
                
            
            logger.info(f"現在のキュー: {len(self.processing_queue)}件")
            
        except Exception as e:
            logger.error(f"キュースキャン中にエラーが発生しました: {e}")
    
    def process_queued_files(self):
        """キューにあるファイルを処理"""
        try:
            if not self.processing_queue:
                logger.debug("処理すべきファイルはありません")
                return
            
            # 同時処理数を確認
            max_concurrent = self.config.get("max_concurrent_files", 3)
            current_running = len(self.files_in_process)
            available_slots = max(0, max_concurrent - current_running)
            
            if available_slots <= 0:
                logger.debug("同時処理数の上限に達しています")
                return
            
            # リソース使用状況を確認
            cpu_percent = psutil.cpu_percent()
            max_cpu = self.config.get("max_cpu_percent", 95)
            
            if cpu_percent > max_cpu:
                logger.info(f"CPU使用率が高すぎるため、処理を延期します: {cpu_percent}%")
                return
            
            # 処理するファイル数を決定
            files_to_process = self.processing_queue[:available_slots]
            
            # Whisperモデルを取得
            model_size = self.config.get("whisper_model", "large")
            
            # ファイルを処理
            for file_info in files_to_process:
                file_path = file_info["path"]
                # キューから削除
                self.processing_queue = [f for f in self.processing_queue if f["path"] != file_path]
                
                # 処理開始
                self.process_file(file_path, model_size)
        
        except Exception as e:
            logger.error(f"キュー処理中にエラーが発生しました: {e}")
    
    def process_file(self, file_path, model_size=None):
        """ファイルを処理する"""
        start_time = time.time()
        try:
            # ファイルが存在するか確認
            if not os.path.exists(file_path):
                logger.warning(f"ファイルが存在しません: {file_path}")
                return
            
            # 処理中リストに追加
            self.files_in_process.add(file_path)
            file_name = os.path.basename(file_path)
            logger.info(f"ファイル処理開始: {file_name} (モデル: {model_size})")
            
            # 文字起こし処理を実行
            transcription = self.transcribe_audio(file_path, model_size)
            
            if transcription:
                # 出力ファイルパスを生成
                output_folder = self.config.get("output_folder")
                output_file = os.path.join(
                    output_folder, 
                    f"{os.path.splitext(file_name)[0]}.txt"
                )
                
                # 出力ディレクトリが存在するか確認
                os.makedirs(output_folder, exist_ok=True)
                
                # 結果を保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                
                # 処理時間を計算
                processing_time = time.time() - start_time
                logger.info(f"文字起こし完了: {file_name} -> {output_file} (処理時間: {processing_time:.2f}秒)")
                
                # アーカイブフォルダに移動
                archive_folder = self.config.get("archive_folder", "archive")
                os.makedirs(archive_folder, exist_ok=True)
                
                archive_path = os.path.join(archive_folder, file_name)
                shutil.move(file_path, archive_path)
                logger.info(f"アーカイブ: {file_name} -> {archive_path}")
                
                # 通知
                self.send_notification(
                    "Koemoji文字起こし完了",
                    f"ファイル: {file_name}\n出力: {output_file}\n処理時間: {processing_time:.2f}秒"
                )
            else:
                logger.error(f"文字起こし失敗: {file_name}")
                
                
                # エラー通知
                self.send_notification(
                    "Koemoji文字起こしエラー",
                    f"ファイル: {file_name}\n処理に失敗しました。"
                )
        
        except Exception as e:
            logger.error(f"ファイル処理中にエラーが発生しました: {file_path} - {e}")
            
            
            # エラー通知
            self.send_notification(
                "Koemoji処理エラー",
                f"ファイル: {os.path.basename(file_path)}\nエラー: {e}"
            )
        finally:
            # 処理中リストから削除
            if file_path in self.files_in_process:
                self.files_in_process.remove(file_path)
    
    def transcribe_audio(self, file_path, model_size=None):
        """音声ファイルを文字起こし"""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            logger.error("faster_whisperがインストールされていません。pip install faster-whisperを実行してください。")
            return None
        
        try:
            # モデルサイズとコンピュートタイプを設定
            model_size = model_size or self.config.get("whisper_model", "large")
            compute_type = self.config.get("compute_type", "int8")
            
            # モデルが未ロードか設定が変わった場合のみ再ロード
            if (self._whisper_model is None or 
                self._model_config != (model_size, compute_type)):
                logger.info(f"Whisperモデルをロード中: {model_size}")
                self._whisper_model = WhisperModel(model_size, compute_type=compute_type)
                self._model_config = (model_size, compute_type)
            
            # ファイル名を取得（ログ表示用）
            file_name = os.path.basename(file_path)
            logger.info(f"文字起こし開始: {file_name}")
            
            # 文字起こし実行
            segments, info = self._whisper_model.transcribe(
                file_path,
                language=self.config.get("language", "ja"),
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
                    logger.info(f"文字起こし進行中: {file_name} - {segment_count}セグメント処理済み")
            
            # 完了ログ
            logger.info(f"文字起こし完了: {file_name} - 合計{segment_count}セグメント")
            
            return "\n".join(transcription)
        
        except Exception as e:
            logger.error(f"文字起こし処理中にエラーが発生しました: {e}")
            return None
    
    def send_notification(self, title, message):
        """通知をログに記録する"""
        logger.info(f"{title} - {message}")
    
    def is_already_running(self):
        """既に実行中かチェック"""
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
                                logger.debug(f"既存のプロセスを検出: PID={proc.pid}")
                                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return False
    
    
    def run(self):
        """メイン処理ループ"""
        try:
            # 停止フラグファイルのパスを設定（カレントディレクトリを基準）
            base_dir = os.path.dirname(os.path.abspath(__file__))
            stop_flag_path = os.path.join(base_dir, "stop_koemoji.flag")
            
            # 既に実行中かチェック
            if self.is_already_running():
                logger.error("既に別のKoemojiAutoプロセスが実行中です。")
                self.send_notification(
                    "KoemojiAutoエラー",
                    "既に別のプロセスが実行中です。"
                )
                return
            
            # 起動時に古い停止フラグを削除
            if os.path.exists(stop_flag_path):
                os.remove(stop_flag_path)
                logger.info("古い停止フラグを削除しました")
            
            logger.info("KoemojiAuto処理を開始しました")
            
            # 開始通知
            self.send_notification(
                "KoemojiAuto",
                "自動文字起こしサービスが開始されました"
            )
            
            # 24時間連続モードで動作
            logger.info("24時間連続モードで動作します")
            
            scan_interval = self.config.get("scan_interval_minutes", 30) * 60  # 秒に変換
            last_scan_time = 0
            
            # 初回スキャン
            self.scan_and_queue_files()
            self.process_queued_files()
            
            # メインループ（24時間動作）
            while True:
                # 停止フラグを確認
                if os.path.exists(stop_flag_path):
                    logger.info("停止フラグが検出されました。処理を終了します")
                    break
                
                current_time = time.time()
                
                # 定期的にファイルをスキャン
                if current_time - last_scan_time >= scan_interval:
                    self.scan_and_queue_files()
                    last_scan_time = current_time
                
                # キューのファイルを処理
                self.process_queued_files()
                
                # 短い待機（フラグファイルチェックの頻度も兼ねる）
                time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("停止シグナルを受信しました")
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")
        finally:
            # 終了時にフラグファイルを削除
            if 'stop_flag_path' in locals() and os.path.exists(stop_flag_path):
                os.remove(stop_flag_path)
                logger.info("停止フラグを削除しました")
            
            logger.info("KoemojiAutoを終了しました")


# 実行例
if __name__ == "__main__":
    processor = KoemojiProcessor()
    
    # シグナルハンドラーの設定
    def signal_handler(sig, frame):
        logger.info("停止シグナルを受信しました")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    processor.run()