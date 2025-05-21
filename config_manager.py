#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoemojiAuto - 設定管理モジュール
設定ファイルの読み込み・保存・検証を担当
"""

import os
import json
from pathlib import Path
import utils

class ConfigManager:
    def __init__(self, config_path="config.json"):
        """初期化"""
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """設定ファイルを読み込む（エンコーディング問題に対応）"""
        try:
            if not os.path.exists(self.config_path):
                # 初回使用時：デフォルト値を設定
                utils.log_and_print("設定ファイルが見つからないため、デフォルト設定を使用します。")
                
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
                utils.log_and_print(f"設定を作成しました: {self.config_path}")
            else:
                # まずUTF-8で試す（最も一般的）
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                    utils.log_and_print(f"設定を読み込みました: {self.config_path}")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # 失敗したら日本語環境で一般的なSHIFT-JISを試す
                    try:
                        with open(self.config_path, 'r', encoding='shift-jis') as f:
                            self.config = json.load(f)
                        utils.log_and_print(f"設定を読み込みました（shift-jis）: {self.config_path}")
                        # 成功したらUTF-8で保存し直す
                        self.save_config()
                    except:
                        utils.log_and_print("設定ファイルを読み込めませんでした。デフォルト設定を使用します。", "error")
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
                utils.ensure_directory(folder_path)
                utils.log_and_print(f"{folder_key}を確認しました: {folder_path}")
                    
        except Exception as e:
            utils.log_and_print(f"設定の読み込み中にエラーが発生しました: {e}", "error")
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
                utils.log_and_print(f"必須設定 '{key}' が見つかりません。デフォルト値 '{default}' を使用します。", "warning")
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
                    utils.logger.debug(f"パスを正規化: {key} = {self.config[key]}")
                except Exception as e:
                    utils.log_and_print(f"パスの正規化に失敗: {key} = {self.config[key]}, エラー: {e}", "warning")
    
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
                utils.logger.info(f"設定ファイルを保存しました: {self.config_path}")
            
        except Exception as e:
            utils.log_and_print(f"設定の保存中にエラーが発生しました: {e}", "error")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
    
    def get(self, key, default=None):
        """設定値を取得"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """設定値を更新"""
        self.config[key] = value
        self.save_config()
        return value