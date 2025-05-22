"""ファイル処理のテスト"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from main import KoemojiProcessor


class TestFileProcessing:
    @patch('faster_whisper.WhisperModel')
    def test_transcribe_audio_success(self, mock_whisper_model):
        """音声ファイルの文字起こし成功テスト"""
        # モックの設定
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance
        
        # 文字起こし結果のモック
        mock_segment = MagicMock()
        mock_segment.text = "これはテストの文字起こしです"
        mock_model_instance.transcribe.return_value = ([mock_segment], MagicMock())
        
        processor = KoemojiProcessor()
        result = processor.transcribe_audio("/path/to/test.mp3")
        
        # 結果の確認
        assert result == "これはテストの文字起こしです"
        mock_whisper_model.assert_called_once_with("large", compute_type="int8")
        mock_model_instance.transcribe.assert_called_once()
    
    @patch('faster_whisper.WhisperModel')
    def test_transcribe_audio_error(self, mock_whisper_model):
        """音声ファイルの文字起こしエラーテスト"""
        # モックがエラーを発生させる
        mock_whisper_model.side_effect = Exception("モデルロードエラー")
        
        processor = KoemojiProcessor()
        result = processor.transcribe_audio("/path/to/test.mp3")
        
        # エラー時はNoneが返される
        assert result is None
    
    @patch('faster_whisper.WhisperModel')
    def test_process_file_success(self, mock_whisper_model):
        """ファイル処理成功テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 設定の準備
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            
            # テストファイルの作成
            test_file = os.path.join(input_dir, "test.mp3")
            with open(test_file, 'w') as f:
                f.write("dummy audio content")
            
            # モックの設定
            mock_model_instance = MagicMock()
            mock_whisper_model.return_value = mock_model_instance
            mock_segment = MagicMock()
            mock_segment.text = "テスト文字起こし"
            mock_model_instance.transcribe.return_value = ([mock_segment], MagicMock())
            
            processor = KoemojiProcessor(config_path)
            processor.config["output_folder"] = output_dir
            
            # ファイル処理を実行
            processor.process_file(test_file)
            
            # 出力ファイルが作成されたことを確認
            output_file = os.path.join(output_dir, "test.txt")
            assert os.path.exists(output_file)
            
            # 出力内容を確認
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert content == "テスト文字起こし"
            
            # 処理済みファイルに追加されたことを確認
            file_size = os.path.getsize(test_file)
            file_id = f"test.mp3_{file_size}"
            assert file_id in processor.processed_files
    
    @patch('faster_whisper.WhisperModel')
    def test_process_file_error_handling(self, mock_whisper_model):
        """ファイル処理エラーハンドリングテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # テストファイルを作成
            test_file = os.path.join(temp_dir, "error_test.mp3")
            with open(test_file, 'w') as f:
                f.write("dummy")
            
            # モックがエラーを発生させる
            mock_whisper_model.side_effect = Exception("処理エラー")
            
            processor = KoemojiProcessor()
            
            # エラーが発生するファイルの処理
            processor.process_file(test_file)
            
            # エラーが発生しても例外が発生しないことを確認
            assert processor.today_stats["failed"] == 1
    
    def test_process_nonexistent_file(self):
        """存在しないファイルの処理テスト"""
        processor = KoemojiProcessor()
        
        # ファイルが処理中リストに追加されないことを確認
        initial_count = len(processor.files_in_process)
        processor.process_file("/nonexistent/file.mp3")
        
        # 処理中リストが変更されていないことを確認
        assert len(processor.files_in_process) == initial_count
    
    @patch('psutil.cpu_percent')
    def test_process_with_high_cpu(self, mock_cpu_percent):
        """高CPU使用率での処理テスト"""
        # CPU使用率を高く設定
        mock_cpu_percent.return_value = 99.0
        
        processor = KoemojiProcessor()
        processor.config["max_cpu_percent"] = 95
        
        # キューにファイルを追加
        processor.processing_queue.append({
            "path": "/path/test.mp3",
            "name": "test.mp3",
            "priority": 0
        })
        
        # 処理を試みる
        processor.process_queued_files()
        
        # CPU使用率が高いため、ファイルが処理されないことを確認
        assert len(processor.processing_queue) == 1
    
    @patch('main.KoemojiProcessor.transcribe_audio')
    def test_multiple_segments_transcription(self, mock_transcribe):
        """複数セグメントの文字起こしテスト"""
        # 複数行の文字起こし結果をモック
        mock_transcribe.return_value = "第1セグメント\n第2セグメント\n第3セグメント"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            processor = KoemojiProcessor(config_path)
            processor.config["output_folder"] = output_dir
            
            # テストファイルを作成
            test_file = os.path.join(temp_dir, "test.mp3")
            with open(test_file, 'w') as f:
                f.write("dummy")
            
            # ファイルを処理
            processor.process_file(test_file)
            
            # 出力ファイルの内容を確認
            output_file = os.path.join(output_dir, "test.txt")
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "第1セグメント" in content
            assert "第2セグメント" in content
            assert "第3セグメント" in content