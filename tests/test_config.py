"""設定ファイル関連のテスト"""
import json
import os
import tempfile
import pytest
from unittest.mock import patch
from main import KoemojiProcessor


class TestConfig:
    def test_load_default_config(self):
        """デフォルト設定の読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            
            # 存在しない設定ファイルの場合、デフォルト設定が作成される
            processor = KoemojiProcessor(config_path)
            
            # デフォルト設定の確認
            assert processor.config["input_folder"] == "input"
            assert processor.config["output_folder"] == "output"
            # process_end_time removed
            assert processor.config["whisper_model"] == "large"
            assert processor.config["language"] == "ja"
            
            # 設定ファイルが作成されたことを確認
            assert os.path.exists(config_path)
    
    def test_load_existing_config(self):
        """既存設定ファイルの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            
            # テスト用設定を作成
            test_config = {
                "input_folder": "test_input",
                "output_folder": "test_output",
                "whisper_model": "small",
                "language": "en"
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # 設定の読み込み
            processor = KoemojiProcessor(config_path)
            
            # 設定が正しく読み込まれたことを確認
            assert processor.config["input_folder"] == "test_input"
            assert processor.config["output_folder"] == "test_output"
            assert processor.config["whisper_model"] == "small"
            assert processor.config["language"] == "en"
    
    def test_invalid_config_file(self):
        """不正な設定ファイルのハンドリングテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            
            # 不正なJSONを作成
            with open(config_path, 'w') as f:
                f.write("invalid json {")
            
            # エラーハンドリングの確認
            processor = KoemojiProcessor(config_path)
            
            # 最小限のデフォルト設定が使用されることを確認
            assert processor.config["input_folder"] == "input"
            assert processor.config["output_folder"] == "output"
    
    def test_create_directories(self):
        """必要なディレクトリの自動作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            
            # 入力・出力フォルダのパスを設定
            test_config = {
                "input_folder": os.path.join(temp_dir, "test_input"),
                "output_folder": os.path.join(temp_dir, "test_output")
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # プロセッサー初期化時にディレクトリが作成される
            processor = KoemojiProcessor(config_path)
            
            # ディレクトリが作成されたことを確認
            assert os.path.exists(test_config["input_folder"])
            assert os.path.exists(test_config["output_folder"])
    
    # test_get_end_time removed as time mode is no longer supported
    
    # test_continuous_mode_setting removed as time mode is no longer supported
