"""ファイルスキャン機能のテスト"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from main import KoemojiProcessor


class TestFileScanning:
    def test_scan_empty_directory(self):
        """空のディレクトリのスキャンテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            
            processor = KoemojiProcessor(config_path)
            processor.config["input_folder"] = input_dir
            
            # スキャンを実行
            processor.scan_and_queue_files()
            
            # キューが空であることを確認
            assert len(processor.processing_queue) == 0
    
    def test_scan_with_media_files(self):
        """メディアファイルのスキャンテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            
            # テスト用メディアファイルを作成
            test_files = ["test1.mp3", "test2.mp4", "test3.wav"]
            for filename in test_files:
                filepath = os.path.join(input_dir, filename)
                with open(filepath, 'w') as f:
                    f.write("dummy content")
            
            processor = KoemojiProcessor(config_path)
            processor.config["input_folder"] = input_dir
            
            # スキャンを実行
            processor.scan_and_queue_files()
            
            # すべてのファイルがキューに追加されたことを確認
            assert len(processor.processing_queue) == 3
            queued_filenames = [os.path.basename(f["path"]) for f in processor.processing_queue]
            for filename in test_files:
                assert filename in queued_filenames
    
    def test_scan_ignore_non_media_files(self):
        """非メディアファイルを無視するテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            
            # メディアファイルと非メディアファイルを作成
            test_files = {
                "media1.mp3": True,
                "document.txt": False,
                "image.jpg": False,
                "media2.wav": True,
                "spreadsheet.xlsx": False
            }
            
            for filename, is_media in test_files.items():
                filepath = os.path.join(input_dir, filename)
                with open(filepath, 'w') as f:
                    f.write("dummy content")
            
            processor = KoemojiProcessor(config_path)
            processor.config["input_folder"] = input_dir
            
            # スキャンを実行
            processor.scan_and_queue_files()
            
            # メディアファイルのみがキューに追加されたことを確認
            assert len(processor.processing_queue) == 2
            queued_filenames = [os.path.basename(f["path"]) for f in processor.processing_queue]
            
            for filename, is_media in test_files.items():
                if is_media:
                    assert filename in queued_filenames
                else:
                    assert filename not in queued_filenames
    
    def test_scan_skip_processed_files(self):
        """処理済みファイルをスキップするテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            
            # テスト用ファイルを作成
            test_files = ["processed.mp3", "new.mp3"]
            for filename in test_files:
                filepath = os.path.join(input_dir, filename)
                with open(filepath, 'w') as f:
                    f.write("dummy content")
            
            processor = KoemojiProcessor(config_path)
            processor.config["input_folder"] = input_dir
            
            # 処理済みファイルとして登録
            processed_file_path = os.path.join(input_dir, "processed.mp3")
            file_size = os.path.getsize(processed_file_path)
            file_id = f"processed.mp3_{file_size}"
            processor.processed_files.add(file_id)
            
            # スキャンを実行
            processor.scan_and_queue_files()
            
            # 新しいファイルのみがキューに追加されたことを確認
            assert len(processor.processing_queue) == 1
            assert os.path.basename(processor.processing_queue[0]["path"]) == "new.mp3"
    
    def test_scan_skip_files_in_process(self):
        """処理中のファイルをスキップするテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            
            # テスト用ファイルを作成
            test_files = ["in_process.mp3", "new.mp3"]
            for filename in test_files:
                filepath = os.path.join(input_dir, filename)
                with open(filepath, 'w') as f:
                    f.write("dummy content")
            
            processor = KoemojiProcessor(config_path)
            processor.config["input_folder"] = input_dir
            
            # 処理中ファイルとして登録
            in_process_file = os.path.join(input_dir, "in_process.mp3")
            processor.files_in_process.add(in_process_file)
            
            # スキャンを実行
            processor.scan_and_queue_files()
            
            # 新しいファイルのみがキューに追加されたことを確認
            assert len(processor.processing_queue) == 1
            assert os.path.basename(processor.processing_queue[0]["path"]) == "new.mp3"
    
    def test_scan_ignore_directories(self):
        """ディレクトリを無視するテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            
            # サブディレクトリとファイルを作成
            subdir = os.path.join(input_dir, "subdir")
            os.makedirs(subdir, exist_ok=True)
            
            # ファイルを作成
            test_file = os.path.join(input_dir, "test.mp3")
            with open(test_file, 'w') as f:
                f.write("dummy content")
            
            processor = KoemojiProcessor(config_path)
            processor.config["input_folder"] = input_dir
            
            # スキャンを実行
            processor.scan_and_queue_files()
            
            # ファイルのみがキューに追加されたことを確認
            assert len(processor.processing_queue) == 1
            assert os.path.basename(processor.processing_queue[0]["path"]) == "test.mp3"