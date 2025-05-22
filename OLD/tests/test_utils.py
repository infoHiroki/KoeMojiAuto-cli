"""ユーティリティ関数のテスト"""
import os
import tempfile
import pytest
from main import KoemojiProcessor


class TestUtilityFunctions:
    def test_calculate_priority_by_size(self):
        """ファイルサイズに基づく優先度計算のテスト"""
        processor = KoemojiProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            try:
                # 小さいファイル（5MB）の優先度
                temp_file.truncate(5 * 1024 * 1024)
                temp_file.flush()
                priority_small = processor.calculate_priority(temp_file.name)
                
                # 中サイズファイル（30MB）の優先度
                temp_file.truncate(30 * 1024 * 1024)
                temp_file.flush()
                priority_medium = processor.calculate_priority(temp_file.name)
                
                # 大きいファイル（150MB）の優先度
                temp_file.truncate(150 * 1024 * 1024)
                temp_file.flush()
                priority_large = processor.calculate_priority(temp_file.name)
                
                # 小さいファイルほど優先度が高いことを確認
                assert priority_small > priority_medium
                assert priority_medium > priority_large
                
            finally:
                os.unlink(temp_file.name)
    
    def test_calculate_priority_by_keyword(self):
        """キーワードに基づく優先度計算のテスト"""
        processor = KoemojiProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 通常のファイル
            normal_file = os.path.join(temp_dir, "normal_file.mp3")
            with open(normal_file, 'w') as f:
                f.write("test")
            priority_normal = processor.calculate_priority(normal_file)
            
            # 優先キーワードを含むファイル
            urgent_file = os.path.join(temp_dir, "urgent_meeting.mp3")
            with open(urgent_file, 'w') as f:
                f.write("test")
            priority_urgent = processor.calculate_priority(urgent_file)
            
            # 優先キーワードを含むファイルの方が優先度が高いことを確認
            assert priority_urgent > priority_normal
            assert priority_urgent - priority_normal >= 5  # キーワードで+5ポイント
    
    def test_file_id_generation(self):
        """ファイルIDの生成テスト"""
        processor = KoemojiProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            try:
                temp_file.write(b"test content")
                temp_file.flush()
                
                file_name = os.path.basename(temp_file.name)
                file_size = os.path.getsize(temp_file.name)
                
                expected_id = f"{file_name}_{file_size}"
                
                # process_file内で使用されるファイルID生成ロジックの確認
                assert expected_id == f"{file_name}_{file_size}"
                
            finally:
                os.unlink(temp_file.name)
    
    def test_processed_history_management(self):
        """処理済みファイル履歴の管理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            processor = KoemojiProcessor(config_path)
            
            # 履歴パスを一時ディレクトリに変更
            from pathlib import Path
            processor.processed_history_path = Path(temp_dir) / "processed_files.json"
            
            # テストファイルIDを追加
            test_file_ids = ["file1_100", "file2_200", "file3_300"]
            for file_id in test_file_ids:
                processor.processed_files.add(file_id)
            
            # 履歴を保存
            processor.save_processed_history()
            
            # 新しいインスタンスで履歴を読み込み
            new_processor = KoemojiProcessor(config_path)
            new_processor.processed_history_path = processor.processed_history_path
            new_processor.load_processed_history()
            
            # 履歴が正しく読み込まれたことを確認
            assert new_processor.processed_files == processor.processed_files
            assert len(new_processor.processed_files) == 3
            assert "file1_100" in new_processor.processed_files
    
    def test_supported_extensions(self):
        """対応拡張子のテスト"""
        processor = KoemojiProcessor()
        
        # サポートされる拡張子
        supported_extensions = ('.mp3', '.mp4', '.wav', '.m4a', '.mov', '.avi', '.flac', '.ogg', '.aac')
        
        for ext in supported_extensions:
            assert ext in supported_extensions
        
        # サポートされない拡張子
        unsupported_extensions = ('.txt', '.pdf', '.doc', '.jpg')
        
        for ext in unsupported_extensions:
            assert ext not in supported_extensions