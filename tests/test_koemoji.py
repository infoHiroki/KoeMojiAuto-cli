import unittest
import tempfile
import os
import json
import shutil
import sys
import logging # <--- Import logging
from unittest.mock import patch, MagicMock

# Add project root to sys.path to allow importing koemoji
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import koemoji
from koemoji import (
    load_config, save_config, validate_config, 
    DEFAULT_CONFIG, config as koemoji_config, # Import and alias to avoid clash
    log_and_print, setup_logging, BASE_DIR as KOEMOJI_BASE_DIR
)


# class TestKoeMoji(unittest.TestCase): # Removed
#     pass


# Helper functions for testing
# def create_temp_dir_helper(name="test_temp_dir"): # Unused
#     """Creates a temporary directory and returns its path."""
#     temp_dir = tempfile.mkdtemp(prefix=name)
#     return temp_dir

# def remove_temp_dir_helper(directory_path): # Unused
#     """Removes a temporary directory."""
#     if os.path.exists(directory_path):
#         shutil.rmtree(directory_path)

def create_temp_config_file_helper(base_dir, config_data=None, filename="config.json"): # Used by TestKoeMojiConfig
    """Creates a temporary config.json file in the given base_dir."""
    
    # Adjust default paths to be relative to the provided base_dir
    default_input = os.path.join(base_dir, "input")
    default_output = os.path.join(base_dir, "output")
    default_archive = os.path.join(base_dir, "archive")

    if config_data is None:
        config_data = {
            "input_folder": default_input,
            "output_folder": default_output,
            "archive_folder": default_archive,
            "supported_extensions": [".txt", ".md"],
            "emoji_mapping": {
                "smile": "😊",
                "heart": "❤️"
            }
        }
    
    config_file_path = os.path.join(base_dir, filename)
    with open(config_file_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)
    
    # Create the input, output, and archive directories if they are in config
    # This is more aligned with what load_config is expected to do/check
    if "input_folder" in config_data:
        os.makedirs(config_data["input_folder"], exist_ok=True)
    if "output_folder" in config_data:
        os.makedirs(config_data["output_folder"], exist_ok=True)
    if "archive_folder" in config_data:
        os.makedirs(config_data["archive_folder"], exist_ok=True)
            
    return config_file_path


class TestKoeMojiConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir_context = tempfile.TemporaryDirectory()
        self.test_dir = self.test_dir_context.name
        self.config_file_path = os.path.join(self.test_dir, "config.json")

        # It's crucial to patch BASE_DIR *before* koemoji.DEFAULT_CONFIG is accessed
        # by load_config if it uses BASE_DIR to construct default paths.
        self.base_dir_patcher = patch('koemoji.BASE_DIR', self.test_dir)
        self.mock_base_dir = self.base_dir_patcher.start()

        # Patch koemoji.setup_logging to prevent actual log file creation/config
        self.setup_logging_patcher = patch('koemoji.setup_logging', MagicMock())
        self.mock_setup_logging = self.setup_logging_patcher.start()

        # Patch koemoji.logger BEFORE log_and_print is used or koemoji.py initializes it.
        # This single mock_logger will capture all calls to logger.info, .error etc.
        # whether from log_and_print or directly.
        # Use spec=logging.Logger to ensure the mock behaves like a Logger instance.
        self.logger_patcher = patch('koemoji.logger', MagicMock(spec=logging.Logger))
        self.mock_logger = self.logger_patcher.start()
        
        # Patch koemoji.log_and_print as it's used for console output and some log calls.
        # We can use this to verify calls to log_and_print specifically.
        self.log_and_print_patcher = patch('koemoji.log_and_print', MagicMock())
        self.mock_log_and_print = self.log_and_print_patcher.start()

        # Reset koemoji.config before each test
        koemoji.config.clear()
        
        # Store a pristine copy of the original DEFAULT_CONFIG from koemoji.py
        self.original_koemoji_default_config = koemoji.DEFAULT_CONFIG.copy()

        # Create a temporary DEFAULT_CONFIG for tests, modifying paths
        self.test_default_config = koemoji.DEFAULT_CONFIG.copy() # Start with koemoji's actual defaults
        self.test_default_config["input_folder"] = os.path.join(self.test_dir, "input")
        self.test_default_config["output_folder"] = os.path.join(self.test_dir, "output")
        self.test_default_config["archive_folder"] = os.path.join(self.test_dir, "archive")
        
        # Patch koemoji.DEFAULT_CONFIG to use our test-specific version
        self.default_config_patcher = patch('koemoji.DEFAULT_CONFIG', self.test_default_config)
        self.mock_default_config = self.default_config_patcher.start()


    def tearDown(self):
        self.test_dir_context.cleanup()
        self.base_dir_patcher.stop()
        self.setup_logging_patcher.stop()
        self.logger_patcher.stop()
        self.log_and_print_patcher.stop()
        self.default_config_patcher.stop() # Stop patching DEFAULT_CONFIG
        koemoji.config.clear()


    def test_load_config_non_existent(self):
        koemoji.load_config(self.config_file_path)
        self.assertTrue(os.path.exists(self.config_file_path))
        with open(self.config_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        expected_config = self.test_default_config.copy()
        self.assertEqual(loaded_data, expected_config)
        self.assertEqual(koemoji.config, expected_config)
        
        self.assertTrue(os.path.exists(koemoji.config["input_folder"]))
        self.assertTrue(os.path.exists(koemoji.config["output_folder"]))
        self.assertTrue(os.path.exists(koemoji.config["archive_folder"]))
        # This message goes through log_and_print
        self.mock_log_and_print.assert_any_call("設定ファイルが見つからないため、デフォルト設定を使用します。")

    def test_load_config_existing_utf8(self):
        custom_data_written = {
            "input_folder": os.path.join(self.test_dir, "custom_input"),
            "output_folder": os.path.join(self.test_dir, "custom_output"),
            "archive_folder": os.path.join(self.test_dir, "custom_archive"),
            "supported_extensions": [".test1", ".test2"], 
            "emoji_mapping": {"custom_test": "🧪"},
            "language": "en" 
        }
        create_temp_config_file_helper(self.test_dir, config_data=custom_data_written.copy())
        
        koemoji.load_config(self.config_file_path)

        expected_config_in_memory = self.test_default_config.copy()
        expected_config_in_memory.update(custom_data_written) 

        self.assertEqual(koemoji.config, expected_config_in_memory)
        
        self.assertTrue(os.path.exists(custom_data_written["input_folder"]))
        self.assertTrue(os.path.exists(custom_data_written["output_folder"]))
        self.assertTrue(os.path.exists(custom_data_written["archive_folder"]))
        # This message goes through log_and_print
        self.mock_log_and_print.assert_any_call(f"設定を読み込みました: {self.config_file_path}")


    def test_load_config_existing_sjis(self):
        sjis_data_py = {
            "input_folder": os.path.join(self.test_dir, "sjis_input"),
            "output_folder": os.path.join(self.test_dir, "sjis_output"),
            "archive_folder": os.path.join(self.test_dir, "sjis_archive"),
            "language": "ja", 
            "emoji_mapping_sjis_test": {"テスト": "SJIS_OK"} 
        }
        sjis_json_string = json.dumps(sjis_data_py, ensure_ascii=False) 
        
        with open(self.config_file_path, 'w', encoding='shift_jis') as f:
            f.write(sjis_json_string)

        os.makedirs(sjis_data_py["input_folder"], exist_ok=True)
        os.makedirs(sjis_data_py["output_folder"], exist_ok=True)
        os.makedirs(sjis_data_py["archive_folder"], exist_ok=True)

        koemoji.load_config(self.config_file_path)
        
        # In-memory config should have defaults applied after SJIS load and validation
        expected_config_in_memory = self.test_default_config.copy()
        expected_config_in_memory.update(sjis_data_py)
        self.assertEqual(koemoji.config, expected_config_in_memory)
        
        # Log message for successful SJIS load (goes via log_and_print)
        self.mock_log_and_print.assert_any_call(f"設定を読み込みました（shift-jis）: {self.config_file_path}")
        
        # Verify the file is saved back as UTF-8, but *before* validation adds defaults to it,
        # as per koemoji.py's current logic.
        with open(self.config_file_path, 'r', encoding='utf-8') as f:
            reloaded_data_from_file = json.load(f)
        self.assertEqual(reloaded_data_from_file, sjis_data_py) # File has original SJIS content, but UTF8 encoded


    def test_load_config_corrupted_json(self):
        # This specific string will cause JSONDecodeError with UTF-8,
        # and will not be caught by UnicodeDecodeError, thus hitting the outer Exception.
        corrupted_content = '{"key": "value", "malformed": True,' 
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            f.write(corrupted_content)

        koemoji.load_config(self.config_file_path)
        
        expected_config = self.test_default_config.copy()
        self.assertEqual(koemoji.config, expected_config)
        
        # Check that the generic error message from the outer exception handler in load_config was logged
        # This goes to koemoji.logger.error via log_and_print(..., level="error")
        self.assertTrue(self.mock_log_and_print.called)
        call_args_list = self.mock_log_and_print.call_args_list
        found_error_log = False
        for call in call_args_list:
            args, kwargs = call # Actual call from koemoji.py is log_and_print(message, "error")
            if args and len(args) >=2 and "設定の読み込み中にエラーが発生しました:" in args[0] and args[1] == "error":
                found_error_log = True
                break
        self.assertTrue(found_error_log, "Expected error log for corrupted JSON not found.")
        
        # In this specific error path (outer Exception in load_config),
        # koemoji.py currently populates config with defaults but DOES NOT create the directories
        # nor does it save the config. So, we only check if koemoji.config is correct.
        # self.assertTrue(os.path.exists(expected_config["input_folder"]))
        # self.assertTrue(os.path.exists(expected_config["output_folder"]))
        # self.assertTrue(os.path.exists(expected_config["archive_folder"]))


    def test_save_config(self):
        koemoji.load_config(self.config_file_path) 
        
        if "emoji_mapping" not in koemoji.config: 
            koemoji.config["emoji_mapping"] = {}
        
        koemoji.config["emoji_mapping"]["smile_save_test"] = "😁"
        koemoji.config["new_key_save_test"] = "new_value_save"
        koemoji.config["language"] = "fr" 
        
        current_config_copy = koemoji.config.copy() 
        koemoji.save_config(self.config_file_path)
        
        with open(self.config_file_path, 'r', encoding='utf-8') as f:
            saved_data_from_file = json.load(f)
        
        self.assertEqual(saved_data_from_file, current_config_copy) 
        self.assertEqual(saved_data_from_file["emoji_mapping"]["smile_save_test"], "😁")
        self.assertEqual(saved_data_from_file["new_key_save_test"], "new_value_save")
        self.assertEqual(saved_data_from_file["language"], "fr")
        # This message goes directly to logger.info in koemoji.py
        self.mock_logger.info.assert_any_call(f"設定ファイルを保存しました: {self.config_file_path}")


    def test_validate_config_missing_keys(self):
        current_config_in_memory = {
            "input_folder": os.path.join(self.test_dir, "input_val"), 
            "language": "custom_lang", 
            "extra_custom_key": "extra_value" 
        }
        koemoji.config.clear()
        koemoji.config.update(current_config_in_memory)

        os.makedirs(current_config_in_memory["input_folder"], exist_ok=True)

        koemoji.validate_config() 

        expected_validated_config = self.test_default_config.copy()
        expected_validated_config.update(current_config_in_memory) 

        self.assertEqual(koemoji.config["language"], "custom_lang") 
        self.assertEqual(koemoji.config["input_folder"], current_config_in_memory["input_folder"]) 
        self.assertEqual(koemoji.config["extra_custom_key"], "extra_value") 
        
        self.assertEqual(koemoji.config["output_folder"], self.test_default_config["output_folder"])
        self.assertEqual(koemoji.config["archive_folder"], self.test_default_config["archive_folder"])
        self.assertEqual(koemoji.config["whisper_model"], self.test_default_config["whisper_model"])
        
        for key, default_value in self.test_default_config.items():
            if key not in current_config_in_memory: 
                # This message goes through log_and_print
                self.mock_log_and_print.assert_any_call(f"必須設定 '{key}' が見つかりません。デフォルト値 '{default_value}' を使用します。", "warning")


from pathlib import Path
from koemoji import ensure_directory, safe_move_file, scan_and_queue_files, is_file_queued_or_processing
import time # For checking queued_at format, if needed

class TestKoeMojiFileUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir_context = tempfile.TemporaryDirectory()
        self.main_temp_dir = Path(self.temp_dir_context.name)
        self.source_dir = self.main_temp_dir / "source_dir"
        self.dest_dir = self.main_temp_dir / "dest_dir"
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.dest_dir, exist_ok=True)

    def tearDown(self):
        self.temp_dir_context.cleanup()

    # Tests for ensure_directory
    def test_ensure_directory_creates_new(self):
        new_dir_path = self.main_temp_dir / "new_single_dir"
        self.assertFalse(new_dir_path.exists())
        returned_path = ensure_directory(str(new_dir_path))
        self.assertTrue(new_dir_path.exists())
        self.assertTrue(new_dir_path.is_dir())
        self.assertEqual(returned_path, new_dir_path)

    def test_ensure_directory_already_exists(self):
        existing_dir_path = self.main_temp_dir / "already_exists_dir"
        os.makedirs(existing_dir_path, exist_ok=True)
        self.assertTrue(existing_dir_path.exists())
        returned_path = ensure_directory(str(existing_dir_path))
        self.assertTrue(existing_dir_path.exists()) # Should still be there
        self.assertTrue(existing_dir_path.is_dir())
        self.assertEqual(returned_path, existing_dir_path)


    def test_ensure_directory_creates_nested(self):
        nested_dir_path = self.main_temp_dir / "parent_dir" / "child_dir"
        parent_dir_path = self.main_temp_dir / "parent_dir"
        self.assertFalse(parent_dir_path.exists())
        self.assertFalse(nested_dir_path.exists())
        
        returned_path = ensure_directory(str(nested_dir_path))
        
        self.assertTrue(parent_dir_path.exists())
        self.assertTrue(parent_dir_path.is_dir())
        self.assertTrue(nested_dir_path.exists())
        self.assertTrue(nested_dir_path.is_dir())
        self.assertEqual(returned_path, nested_dir_path)

    # Tests for safe_move_file
    def test_safe_move_file_basic_move(self):
        source_file_path = self.source_dir / "test_file.txt"
        with open(source_file_path, "w") as f:
            f.write("test content")
        
        dest_file_path_str = str(self.dest_dir / "test_file.txt")
        
        returned_dest_path = safe_move_file(str(source_file_path), dest_file_path_str)
        
        self.assertFalse(source_file_path.exists())
        self.assertTrue(returned_dest_path.exists())
        self.assertEqual(returned_dest_path.name, "test_file.txt")
        self.assertEqual(returned_dest_path, Path(dest_file_path_str))
        with open(returned_dest_path, "r") as f:
            self.assertEqual(f.read(), "test content")

    def test_safe_move_file_renames_on_conflict(self):
        source_file_name = "conflict.txt"
        source_file_path = self.source_dir / source_file_name
        with open(source_file_path, "w") as f:
            f.write("source content")
            
        existing_dest_file_path = self.dest_dir / source_file_name
        with open(existing_dest_file_path, "w") as f:
            f.write("original dest content")
            
        target_dest_path_str = str(self.dest_dir / source_file_name) # Target the same name
        
        returned_dest_path = safe_move_file(str(source_file_path), target_dest_path_str)
        
        self.assertFalse(source_file_path.exists()) # Source is moved
        self.assertTrue(existing_dest_file_path.exists()) # Original destination file is still there
        with open(existing_dest_file_path, "r") as f:
            self.assertEqual(f.read(), "original dest content") # Check content of original
            
        self.assertTrue(returned_dest_path.exists()) # New file exists
        self.assertEqual(returned_dest_path.name, "conflict_1.txt") # New file is renamed
        self.assertEqual(returned_dest_path, self.dest_dir / "conflict_1.txt")
        with open(returned_dest_path, "r") as f:
            self.assertEqual(f.read(), "source content") # Check content of moved file

    def test_safe_move_file_renames_multiple_conflicts(self):
        source_file_name = "multi_conflict.txt"
        source_file_path = self.source_dir / source_file_name
        with open(source_file_path, "w") as f:
            f.write("source content for multi")

        # Create existing files in destination
        existing_dest_file_path = self.dest_dir / source_file_name
        with open(existing_dest_file_path, "w") as f:
            f.write("original content 0")
            
        existing_dest_file_1_path = self.dest_dir / "multi_conflict_1.txt"
        with open(existing_dest_file_1_path, "w") as f:
            f.write("original content 1")

        target_dest_path_str = str(self.dest_dir / source_file_name) # Target the base name
        
        returned_dest_path = safe_move_file(str(source_file_path), target_dest_path_str)
        
        self.assertFalse(source_file_path.exists())
        self.assertTrue(existing_dest_file_path.exists()) # Original multi_conflict.txt
        self.assertTrue(existing_dest_file_1_path.exists()) # Original multi_conflict_1.txt
        
        self.assertTrue(returned_dest_path.exists())
        self.assertEqual(returned_dest_path.name, "multi_conflict_2.txt")
        self.assertEqual(returned_dest_path, self.dest_dir / "multi_conflict_2.txt")
        with open(returned_dest_path, "r") as f:
            self.assertEqual(f.read(), "source content for multi")


class TestKoeMojiQueueScanning(unittest.TestCase):
    def setUp(self):
        # Store original global states from koemoji module
        self.original_koemoji_config = koemoji.config
        self.original_koemoji_processing_queue = koemoji.processing_queue
        self.original_koemoji_files_in_process = koemoji.files_in_process

        # Mock logger and log_and_print
        self.mock_logger_object = MagicMock(spec=logging.Logger)
        self.mock_log_and_print_object = MagicMock()

        self.patcher_koemoji_logger = patch('koemoji.logger', self.mock_logger_object)
        self.patcher_koemoji_log_and_print = patch('koemoji.log_and_print', self.mock_log_and_print_object)
        
        self.patcher_koemoji_logger.start()
        self.patcher_koemoji_log_and_print.start()

        # Setup temporary directory
        self.td_context = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.td_context.name)
        self.input_dir = self.temp_dir / "test_input_scan" # Unique name
        os.makedirs(self.input_dir, exist_ok=True)

        # Set koemoji global states for the test
        koemoji.config = {
            "input_folder": str(self.input_dir),
            "output_folder": str(self.temp_dir / "test_output_scan"),
            "archive_folder": str(self.temp_dir / "test_archive_scan"),
            # Minimal other keys, scan_and_queue_files doesn't use them directly
        }
        koemoji.processing_queue = []
        koemoji.files_in_process = set()
        
        # Media extensions from koemoji.py (as of writing)
        self.media_extensions = ('.mp3', '.mp4', '.wav', '.m4a', '.mov', '.avi', '.flac', '.ogg', '.aac')

    def tearDown(self):
        # Restore original global states
        koemoji.config = self.original_koemoji_config
        koemoji.processing_queue = self.original_koemoji_processing_queue
        koemoji.files_in_process = self.original_koemoji_files_in_process

        # Stop patchers
        self.patcher_koemoji_logger.stop()
        self.patcher_koemoji_log_and_print.stop()

        # Cleanup temporary directory
        self.td_context.cleanup()

    def _create_dummy_file(self, dir_path, filename, content="dummy"):
        file_path = Path(dir_path) / filename
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    # Tests for scan_and_queue_files
    def test_scan_input_folder_not_exists(self):
        shutil.rmtree(self.input_dir) # Remove the input folder
        self.assertFalse(self.input_dir.exists())

        scan_and_queue_files()

        self.assertTrue(self.input_dir.exists()) # Should be recreated
        self.mock_log_and_print_object.assert_any_call(f"入力フォルダが存在しません: {str(self.input_dir)}", "warning")
        self.assertEqual(len(koemoji.processing_queue), 0)

    def test_scan_empty_input_folder(self):
        scan_and_queue_files()
        self.assertEqual(len(koemoji.processing_queue), 0)
        self.mock_logger_object.debug.assert_any_call("新しいファイルはありません")

    def test_scan_finds_media_files(self):
        file1_path = self._create_dummy_file(self.input_dir, "audio.mp3")
        file2_path = self._create_dummy_file(self.input_dir, "video.mp4", content="larger")

        scan_and_queue_files()

        self.assertEqual(len(koemoji.processing_queue), 2)
        
        queued_files_info = sorted(koemoji.processing_queue, key=lambda x: x['name']) # Sort for consistent order
        
        self.assertEqual(queued_files_info[0]['name'], "audio.mp3")
        self.assertEqual(queued_files_info[0]['path'], str(file1_path))
        self.assertEqual(queued_files_info[0]['size'], len("dummy"))
        self.assertTrue(isinstance(queued_files_info[0]['queued_at'], str))

        self.assertEqual(queued_files_info[1]['name'], "video.mp4")
        self.assertEqual(queued_files_info[1]['path'], str(file2_path))
        self.assertEqual(queued_files_info[1]['size'], len("larger"))
        self.assertTrue(isinstance(queued_files_info[1]['queued_at'], str))

        self.mock_log_and_print_object.assert_any_call("キュー追加: audio.mp3", category="キュー", print_console=False)
        self.mock_log_and_print_object.assert_any_call("キュー追加: video.mp4", category="キュー", print_console=False)
        self.mock_log_and_print_object.assert_any_call(f"キュー状態: 2件待機中", category="キュー", print_console=False)


    def test_scan_ignores_non_media_files(self):
        self._create_dummy_file(self.input_dir, "audio.wav") # Media
        self._create_dummy_file(self.input_dir, "notes.txt") # Non-media
        self._create_dummy_file(self.input_dir, "image.jpg") # Non-media

        scan_and_queue_files()

        self.assertEqual(len(koemoji.processing_queue), 1)
        self.assertEqual(koemoji.processing_queue[0]['name'], "audio.wav")

    def test_scan_ignores_already_queued_files(self):
        file1_path = self._create_dummy_file(self.input_dir, "file1.mp3")
        file2_path = self._create_dummy_file(self.input_dir, "file2.mp3") # Not initially queued

        # Pre-queue file1
        koemoji.processing_queue.append({
            'path': str(file1_path), 
            'name': 'file1.mp3', 
            'size': 0, # os.path.getsize(file1_path), 
            'queued_at': time.strftime("%Y-%m-%d %H:%M:%S")
        })

        scan_and_queue_files()
        
        self.assertEqual(len(koemoji.processing_queue), 2)
        queued_names = sorted([item['name'] for item in koemoji.processing_queue])
        self.assertListEqual(queued_names, ["file1.mp3", "file2.mp3"])


    def test_scan_ignores_files_in_process(self):
        file1_path = self._create_dummy_file(self.input_dir, "file1.mp3") # To be "in process"
        file2_path = self._create_dummy_file(self.input_dir, "file2.mp3") # To be queued

        koemoji.files_in_process.add(str(file1_path))

        scan_and_queue_files()

        self.assertEqual(len(koemoji.processing_queue), 1)
        self.assertEqual(koemoji.processing_queue[0]['name'], "file2.mp3")
        self.assertIn(str(file1_path), koemoji.files_in_process)

    # Tests for is_file_queued_or_processing
    def test_is_file_queued(self):
        test_path = str(self.input_dir / "queued_file.mp3")
        koemoji.processing_queue = [{'path': test_path, 'name': 'queued_file.mp3', 'size': 0, 'queued_at': '...'}]
        self.assertTrue(is_file_queued_or_processing(test_path))

    def test_is_file_processing(self):
        test_path = str(self.input_dir / "processing_file.mp3")
        koemoji.files_in_process = {test_path}
        self.assertTrue(is_file_queued_or_processing(test_path))

    def test_is_file_not_queued_or_processing(self):
        test_path = str(self.input_dir / "other_file.mp3")
        koemoji.processing_queue = []
        koemoji.files_in_process = set()
        self.assertFalse(is_file_queued_or_processing(test_path))


from koemoji import transcribe_audio, process_file, wait_for_resources
# Note: psutil and faster_whisper are conditionally imported in koemoji.py,
# so we mock them via sys.modules.

class TestKoeMojiCoreProcessing(unittest.TestCase):
    def setUp(self):
        self.td_context = tempfile.TemporaryDirectory()
        self.main_temp_dir = Path(self.td_context.name)
        self.input_dir = self.main_temp_dir / "input"
        self.output_dir = self.main_temp_dir / "output"
        self.archive_dir = self.main_temp_dir / "archive"

        for d in [self.input_dir, self.output_dir, self.archive_dir]:
            os.makedirs(d, exist_ok=True)

        # Store original global states
        self.original_config = koemoji.config.copy()
        self.original_whisper_model = koemoji.whisper_model
        self.original_model_config = koemoji.model_config
        self.original_processing_queue = koemoji.processing_queue[:]
        self.original_files_in_process = koemoji.files_in_process.copy()
        self.original_stop_requested = koemoji.stop_requested

        # Set up mock koemoji.config
        koemoji.config = {
            "input_folder": str(self.input_dir),
            "output_folder": str(self.output_dir),
            "archive_folder": str(self.archive_dir),
            "whisper_model": "test_model",
            "language": "test_lang",
            "compute_type": "test_compute",
            "max_cpu_percent": 80, # For wait_for_resources
            "scan_interval_minutes": 5, # For other parts if they use it
            "max_concurrent_files": 1 # For other parts
        }

        # Reset other relevant koemoji globals
        koemoji.whisper_model = None
        koemoji.model_config = None
        koemoji.processing_queue = []
        koemoji.files_in_process = set()
        
        # Patch koemoji.stop_requested - this will be the default state for tests
        self.stop_requested_patcher = patch('koemoji.stop_requested', False)
        self.stop_requested_patcher.start()

        # Mock logger and log_and_print
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.logger_patcher = patch('koemoji.logger', self.mock_logger)
        self.logger_patcher.start()

        self.mock_log_and_print = MagicMock()
        self.log_and_print_patcher = patch('koemoji.log_and_print', self.mock_log_and_print)
        self.log_and_print_patcher.start()

        # Mock for faster_whisper module and its WhisperModel class
        self.mock_faster_whisper_module = MagicMock()
        self.mock_WhisperModel_class = self.mock_faster_whisper_module.WhisperModel
        self.mock_whisper_instance = self.mock_WhisperModel_class.return_value
        # Setup default return for transcribe
        self.mock_segments = [MagicMock(text="Hello"), MagicMock(text="world")]
        self.mock_info = MagicMock()
        self.mock_whisper_instance.transcribe.return_value = (self.mock_segments, self.mock_info)
        
        # Mock for psutil module
        self.mock_psutil_module = MagicMock()
        self.mock_psutil_module.cpu_percent = MagicMock(return_value=10) # Default low CPU

        # Mocks for functions called by process_file
        self.patch_transcribe_audio = patch('koemoji.transcribe_audio')
        self.mock_transcribe_audio = self.patch_transcribe_audio.start()

        self.patch_safe_move_file = patch('koemoji.safe_move_file')
        self.mock_safe_move_file = self.patch_safe_move_file.start()
        self.mock_safe_move_file.side_effect = lambda source, dest: Path(dest) # Simple mock

        self.patch_time_sleep = patch('time.sleep', MagicMock())
        self.mock_time_sleep = self.patch_time_sleep.start()


    def tearDown(self):
        # Restore original global states
        koemoji.config = self.original_config
        koemoji.whisper_model = self.original_whisper_model
        koemoji.model_config = self.original_model_config
        koemoji.processing_queue = self.original_processing_queue
        koemoji.files_in_process = self.original_files_in_process
        koemoji.stop_requested = self.original_stop_requested

        self.stop_requested_patcher.stop()
        self.logger_patcher.stop()
        self.log_and_print_patcher.stop()
        
        self.patch_transcribe_audio.stop()
        self.patch_safe_move_file.stop()
        self.patch_time_sleep.stop()

        self.td_context.cleanup()

    def _create_dummy_file(self, filename="test.mp3", content="dummy audio"):
        file_path = self.input_dir / filename
        with open(file_path, "w") as f:
            f.write(content)
        return str(file_path)

    # --- Tests for transcribe_audio ---
    def test_transcribe_audio_success(self): 
        # Override faster_whisper in sys.modules for this test
        with patch.dict(sys.modules, {'faster_whisper': self.mock_faster_whisper_module}, clear=True):
            dummy_file_path = self._create_dummy_file()
            result = transcribe_audio(dummy_file_path)

            self.assertEqual(result, "Hello\nworld")
            self.mock_whisper_instance.transcribe.assert_called_once_with(
                dummy_file_path,
                language=koemoji.config["language"],
                beam_size=5,
                best_of=5,
                vad_filter=True
            )
            self.mock_log_and_print.assert_any_call(f"音声認識開始: {Path(dummy_file_path).name}", category="処理", print_console=False)
            
            # Check for dynamic log message "文字起こし完了"
            found_completion_log = False
            for call_args in self.mock_log_and_print.call_args_list:
                args, kwargs = call_args
                if args and args[0].startswith(f"文字起こし完了: {Path(dummy_file_path).name}") and kwargs.get('category') is None:
                    found_completion_log = True
                    break
            self.assertTrue(found_completion_log, "Completion log not found or category mismatch.")


    def test_transcribe_audio_model_loading_initial(self): 
        with patch.dict(sys.modules, {'faster_whisper': self.mock_faster_whisper_module}, clear=True):
            koemoji.whisper_model = None # Ensure model is not loaded
            self._create_dummy_file()
            transcribe_audio("dummy_path.mp3") # Use a consistent dummy name or the created one
            self.mock_WhisperModel_class.assert_called_once_with(
                koemoji.config["whisper_model"],
                compute_type=koemoji.config["compute_type"]
            )
            self.assertIsNotNone(koemoji.whisper_model) # Should be set

    def test_transcribe_audio_model_reloading_on_config_change(self): 
        with patch.dict(sys.modules, {'faster_whisper': self.mock_faster_whisper_module}, clear=True):
            # Initial load
            koemoji.whisper_model = "old_mock_model" # Can be any non-None value to signify loaded
            koemoji.model_config = ("old_model_name", "old_compute_type")
            
            koemoji.config["whisper_model"] = "new_model_name" # Change config
            dummy_file_path = self._create_dummy_file()
            transcribe_audio(dummy_file_path)
            
            self.mock_WhisperModel_class.assert_called_once_with("new_model_name", compute_type=koemoji.config["compute_type"])

    def test_transcribe_audio_model_not_reloaded_if_config_same(self): 
        with patch.dict(sys.modules, {'faster_whisper': self.mock_faster_whisper_module}, clear=True):
            # Initial load
            transcribe_audio(self._create_dummy_file("first.mp3"))
            self.mock_WhisperModel_class.assert_called_once() 
            self.mock_whisper_instance.transcribe.assert_called_once()

            # Second call, config is the same
            transcribe_audio(self._create_dummy_file("second.mp3"))
            self.mock_WhisperModel_class.assert_called_once() 
            self.assertEqual(self.mock_whisper_instance.transcribe.call_count, 2)


    def test_transcribe_audio_faster_whisper_not_installed(self):
        with patch.dict(sys.modules, {'faster_whisper': None}, clear=True): 
            result = transcribe_audio(self._create_dummy_file())
            self.assertIsNone(result)
            self.mock_log_and_print.assert_any_call("faster_whisperがインストールされていません。pip install faster-whisperを実行してください。", "error")

    def test_transcribe_audio_stop_requested_before_transcribe(self): 
        # This test previously caused an ImportError. Trying a more manual way to set stop_requested.
        self.stop_requested_patcher.stop() # Stop the default patch (koemoji.stop_requested = False)
        original_module_stop_requested_value = koemoji.stop_requested # Save koemoji's actual current value
        koemoji.stop_requested = True # Directly set to True for this test

        try:
            with patch.dict(sys.modules, {'faster_whisper': self.mock_faster_whisper_module}, clear=True):
                result = transcribe_audio(self._create_dummy_file())
                self.assertIsNone(result)
                self.mock_log_and_print.assert_any_call("停止要求を検出したため、文字起こしをキャンセルします", "info", print_console=False)
                self.mock_WhisperModel_class.assert_not_called() 
        finally:
            koemoji.stop_requested = original_module_stop_requested_value # Restore original value
            self.stop_requested_patcher.start() # Restart the default patch for other tests


    # --- Tests for process_file ---
    def test_process_file_success(self):
        dummy_path = self._create_dummy_file("test.mp3")
        self.mock_transcribe_audio.return_value = "mock transcription"
        
        returned_output_path_str = process_file(dummy_path)
        
        # Path should be added and then removed by the finally block in process_file
        # So, after the call, it should not be in files_in_process.
        self.mock_transcribe_audio.assert_called_once_with(dummy_path)
        
        expected_output_file = self.output_dir / "test.txt"
        self.assertTrue(expected_output_file.exists())
        with open(expected_output_file, "r", encoding='utf-8') as f:
            self.assertEqual(f.read(), "mock transcription")
        
        self.mock_safe_move_file.assert_called_once()
        self.assertEqual(self.mock_safe_move_file.call_args[0][0], dummy_path) 
        self.assertTrue(str(self.mock_safe_move_file.call_args[0][1]).startswith(str(self.archive_dir))) 
        
        self.assertEqual(str(Path(returned_output_path_str)), str(expected_output_file))
        self.assertNotIn(str(Path(dummy_path)), koemoji.files_in_process) 
        
        # Check for dynamic log message "処理完了"
        found_proc_completion_log = False
        for call_args in self.mock_log_and_print.call_args_list:
            args, kwargs = call_args
            if args and args[0].startswith(f"処理完了: test.mp3 → {expected_output_file}") and kwargs.get('category') == "ファイル":
                found_proc_completion_log = True
                break
        self.assertTrue(found_proc_completion_log, "Process completion log not found or category mismatch.")


    def test_process_file_transcription_fails(self):
        dummy_path = self._create_dummy_file("fail.mp3")
        self.mock_transcribe_audio.return_value = None # Transcription fails
        
        result = process_file(dummy_path)
        
        self.assertIsNone(result)
        self.assertFalse((self.output_dir / "fail.txt").exists())
        self.mock_safe_move_file.assert_not_called()
        self.mock_log_and_print.assert_any_call("処理失敗: fail.mp3", "error", category="ファイル")
        self.assertNotIn(str(Path(dummy_path)), koemoji.files_in_process)

    def test_process_file_input_file_not_exists(self):
        non_existent_path = str(self.input_dir / "ghost.mp3")
        result = process_file(non_existent_path)
        self.assertIsNone(result)
        self.mock_log_and_print.assert_any_call(f"ファイルが存在しません: {non_existent_path}", "warning", category="ファイル")
        self.mock_transcribe_audio.assert_not_called()

    def test_process_file_stop_requested_during_transcribe(self):
        dummy_path = self._create_dummy_file("interrupt.mp3")
        # Simulate stop_requested becoming True after transcribe_audio is called but before it completes
        def transcribe_side_effect(*args):
            koemoji.stop_requested = True # Simulate stop during transcription
            return "partial transcription" 
        self.mock_transcribe_audio.side_effect = transcribe_side_effect
        
        result = process_file(dummy_path)
        
        self.assertIsNone(result) # Should indicate failure or interruption
        self.mock_log_and_print.assert_any_call("処理中断: interrupt.mp3", "warning", category="ファイル")
        self.assertFalse((self.output_dir / "interrupt.txt").exists())
        self.mock_safe_move_file.assert_not_called()


    # --- Tests for wait_for_resources ---
    def test_wait_for_resources_cpu_low(self):
        with patch.dict(sys.modules, {'psutil': self.mock_psutil_module}):
            koemoji.config['max_cpu_percent'] = 90
            self.mock_psutil_module.cpu_percent.return_value = 50
            self.assertTrue(wait_for_resources())
            self.mock_time_sleep.assert_not_called()

    def test_wait_for_resources_cpu_high_then_low(self):
        with patch.dict(sys.modules, {'psutil': self.mock_psutil_module}):
            koemoji.config['max_cpu_percent'] = 90
            self.mock_psutil_module.cpu_percent.side_effect = [95, 92, 60] # High, High, Low
            self.assertTrue(wait_for_resources(max_wait_seconds=5)) # Provide timeout
            self.assertEqual(self.mock_time_sleep.call_count, 2) # Waits for first two high values

    def test_wait_for_resources_cpu_high_timeout(self):
        with patch.dict(sys.modules, {'psutil': self.mock_psutil_module}):
            koemoji.config['max_cpu_percent'] = 90
            self.mock_psutil_module.cpu_percent.return_value = 99 # Consistently high
            self.assertFalse(wait_for_resources(max_wait_seconds=1)) # Short timeout
            self.mock_time_sleep.assert_called() # Should have slept at least once

    def test_wait_for_resources_psutil_not_available(self):
        with patch.dict(sys.modules, {'psutil': None}, clear=True): # Simulate psutil not installed
            self.assertTrue(wait_for_resources())
            self.mock_time_sleep.assert_not_called() # Should not sleep if psutil is unavailable

    def test_wait_for_resources_stop_requested(self):
         with patch.dict(sys.modules, {'psutil': self.mock_psutil_module}):
            with patch('koemoji.stop_requested', True):
                self.mock_psutil_module.cpu_percent.return_value = 99 # CPU is high
                self.assertFalse(wait_for_resources())
                self.mock_time_sleep.assert_not_called() # Should exit quickly due to stop_requested


class TestKoeMojiIntegration(unittest.TestCase):
    def _create_dummy_file(self, dir_path, filename, content="dummy_content"):
        file_path = Path(dir_path) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path)

    def setUp(self):
        # Store original global states
        self.original_koemoji_config = koemoji.config.copy()
        self.original_koemoji_processing_queue = list(koemoji.processing_queue)
        self.original_koemoji_files_in_process = set(koemoji.files_in_process)
        self.original_koemoji_stop_requested = koemoji.stop_requested
        self.original_koemoji_logger = koemoji.logger
        self.original_koemoji_DEFAULT_CONFIG = koemoji.DEFAULT_CONFIG.copy()
        self.original_koemoji_BASE_DIR = koemoji.BASE_DIR
        self.original_koemoji_is_running = koemoji.is_running # Store is_running

        # Create temporary directories
        self.td_context = tempfile.TemporaryDirectory()
        self.main_temp_dir = Path(self.td_context.name)
        self.input_dir = self.main_temp_dir / "input_integration"
        self.output_dir = self.main_temp_dir / "output_integration"
        self.archive_dir = self.main_temp_dir / "archive_integration"

        # Note: Directories will be created by load_config via ensure_directory

        self.temp_config_file_path = self.main_temp_dir / "config_integration.json"

        self.test_config_data = {
            "input_folder": str(self.input_dir),
            "output_folder": str(self.output_dir),
            "archive_folder": str(self.archive_dir),
            "scan_interval_minutes": 1,
            "max_concurrent_files": 1,
            "whisper_model": "tiny", 
            "language": "en",
            "compute_type": "int8",
            "max_cpu_percent": 90 
            # Ensure all keys from koemoji.DEFAULT_CONFIG are here to avoid merging issues
            # or ensure DEFAULT_CONFIG is also patched if needed.
        }
        # Add any missing keys from actual DEFAULT_CONFIG to ensure full override
        for key, value in koemoji.DEFAULT_CONFIG.items():
            if key not in self.test_config_data:
                self.test_config_data[key] = value
        
        # Update paths for the test config data after merging
        self.test_config_data["input_folder"] = str(self.input_dir)
        self.test_config_data["output_folder"] = str(self.output_dir)
        self.test_config_data["archive_folder"] = str(self.archive_dir)


        with open(self.temp_config_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_config_data, f, indent=2)

        # Patch BASE_DIR before load_config
        self.patch_base_dir = patch('koemoji.BASE_DIR', str(self.main_temp_dir))
        self.mock_base_dir = self.patch_base_dir.start()

        # Load the test configuration
        koemoji.load_config(str(self.temp_config_file_path))

        # Reset runtime states
        koemoji.processing_queue = []
        koemoji.files_in_process = set()
        koemoji.stop_requested = False
        koemoji.is_running = True # Set is_running to True for the test

        # Start patches for dependencies
        self.mock_transcribe_audio = patch('koemoji.transcribe_audio', return_value="mocked transcription result").start()
        self.addCleanup(self.mock_transcribe_audio.stop)

        self.mock_wait_for_resources = patch('koemoji.wait_for_resources', return_value=True).start()
        self.addCleanup(self.mock_wait_for_resources.stop)
        
        self.mock_log_and_print = patch('koemoji.log_and_print', MagicMock()).start()
        self.addCleanup(self.mock_log_and_print.stop)

        self.mock_setup_logging = patch('koemoji.setup_logging', MagicMock()).start()
        self.addCleanup(self.mock_setup_logging.stop)
        
        # Ensure koemoji.logger is also a mock if setup_logging is fully mocked
        # and koemoji.py might try to use koemoji.logger directly.
        # If setup_logging is mocked, koemoji.logger might not be initialized as expected.
        # The TestKoeMojiCoreProcessing setup for logger is more robust.
        # For now, let's assume setup_logging mock is enough.
        # If direct koemoji.logger calls fail, this needs refinement.
        self.patcher_koemoji_logger = patch('koemoji.logger', MagicMock(spec=logging.Logger))
        self.mock_koemoji_logger = self.patcher_koemoji_logger.start()
        self.addCleanup(self.patcher_koemoji_logger.stop)


    def tearDown(self):
        # patch.stopall() # Stops all patches started with start()
        # Individual patches are stopped by addCleanup

        # Restore original global states
        koemoji.config = self.original_koemoji_config
        koemoji.processing_queue = self.original_koemoji_processing_queue
        koemoji.files_in_process = self.original_koemoji_files_in_process
        koemoji.stop_requested = self.original_koemoji_stop_requested
        koemoji.logger = self.original_koemoji_logger 
        koemoji.DEFAULT_CONFIG = self.original_koemoji_DEFAULT_CONFIG
        koemoji.BASE_DIR = self.original_koemoji_BASE_DIR
        koemoji.is_running = self.original_koemoji_is_running # Restore is_running
        
        self.patch_base_dir.stop() # Stop the BASE_DIR patcher specifically

        # Clean up temporary directory
        self.td_context.cleanup()

    def test_end_to_end_file_processing(self):
        dummy_file_name = "test_audio.mp3"
        input_file_path_str = self._create_dummy_file(self.input_dir, dummy_file_name)
        input_file_path = Path(input_file_path_str)

        # 1. Scan files
        koemoji.scan_and_queue_files()
        
        self.assertEqual(len(koemoji.processing_queue), 1)
        self.assertEqual(koemoji.processing_queue[0]['name'], dummy_file_name)
        self.assertEqual(koemoji.processing_queue[0]['path'], input_file_path_str)

        # 2. Process the file
        result = koemoji.process_next_file()
        self.assertTrue(result, "process_next_file should return True on successful processing")

        # 3. Assertions
        self.mock_transcribe_audio.assert_called_once_with(input_file_path_str)
        
        self.assertEqual(len(koemoji.files_in_process), 0, "files_in_process should be empty after processing")
        
        self.assertFalse(input_file_path.exists(), "Input file should be moved from input_dir")
        
        archived_file_path = self.archive_dir / dummy_file_name
        self.assertTrue(archived_file_path.exists(), "Input file should be moved to archive_dir")

        output_file_name = Path(dummy_file_name).stem + ".txt"
        output_file_path = self.output_dir / output_file_name
        self.assertTrue(output_file_path.exists(), "Output .txt file should exist")

        with open(output_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "mocked transcription result")

        self.assertEqual(len(koemoji.processing_queue), 0, "processing_queue should be empty after processing")

        # Check for key log messages
        # Example: Check if "処理完了" (processing complete) and "アーカイブ" (archived) were logged.
        # These messages are logged with categories.
        log_calls = self.mock_log_and_print.call_args_list
        
        expected_log_processing_complete_start = f"処理完了: {dummy_file_name} → {output_file_path}"
        found_processing_complete = any(
            call[0][0].startswith(expected_log_processing_complete_start) and call[1].get('category') == "ファイル"
            for call in log_calls
        )
        self.assertTrue(found_processing_complete, f"Log message for '処理完了' not found or incorrect. Searched for: '{expected_log_processing_complete_start}' with category 'ファイル'")

        expected_log_archived = f"アーカイブ: {dummy_file_name}"
        found_archived = any(
            call[0][0] == expected_log_archived and call[1].get('category') == "ファイル"
            for call in log_calls
        )
        self.assertTrue(found_archived, f"Log message for 'アーカイブ' not found or incorrect. Searched for: '{expected_log_archived}' with category 'ファイル'")


if __name__ == '__main__':
    unittest.main()
