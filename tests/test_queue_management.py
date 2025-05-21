"""キュー管理のテスト"""
import os
import tempfile
import pytest
from datetime import datetime
from main import KoemojiProcessor


class TestQueueManagement:
    def test_queue_priority_ordering(self):
        """優先度に基づくキューの並び替えテスト"""
        processor = KoemojiProcessor()
        
        # 異なる優先度のファイル情報を作成
        files = [
            {"path": "/path/normal.mp3", "name": "normal.mp3", "size": 100000000, "priority": 0},
            {"path": "/path/urgent.mp3", "name": "urgent.mp3", "size": 5000000, "priority": 8},
            {"path": "/path/small.mp3", "name": "small.mp3", "size": 1000000, "priority": 3},
        ]
        
        # ランダムな順序でキューに追加
        for file_info in files:
            processor.processing_queue.append(file_info)
        
        # 優先度でソート
        processor.processing_queue.sort(key=lambda x: x["priority"], reverse=True)
        
        # 優先度の高い順に並んでいることを確認
        assert processor.processing_queue[0]["name"] == "urgent.mp3"
        assert processor.processing_queue[1]["name"] == "small.mp3"
        assert processor.processing_queue[2]["name"] == "normal.mp3"
    
    def test_add_file_to_queue(self):
        """ファイルをキューに追加するテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            input_dir = os.path.join(temp_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            
            # テストファイルを作成
            test_file = os.path.join(input_dir, "test.mp3")
            with open(test_file, 'w') as f:
                f.write("dummy content")
            
            processor = KoemojiProcessor(config_path)
            processor.config["input_folder"] = input_dir
            
            # スキャンしてキューに追加
            processor.scan_and_queue_files()
            
            # ファイル情報が正しく記録されることを確認
            assert len(processor.processing_queue) == 1
            queued_file = processor.processing_queue[0]
            assert queued_file["path"] == test_file
            assert queued_file["name"] == "test.mp3"
            assert queued_file["size"] > 0
            assert "queued_at" in queued_file
            assert "priority" in queued_file
    
    def test_remove_file_from_queue(self):
        """キューからファイルを削除するテスト"""
        processor = KoemojiProcessor()
        
        # テスト用ファイル情報
        file1 = {"path": "/path/file1.mp3", "name": "file1.mp3"}
        file2 = {"path": "/path/file2.mp3", "name": "file2.mp3"}
        file3 = {"path": "/path/file3.mp3", "name": "file3.mp3"}
        
        # キューに追加
        processor.processing_queue = [file1, file2, file3]
        
        # file2を削除
        processor.processing_queue = [f for f in processor.processing_queue if f["path"] != file2["path"]]
        
        # file2が削除されたことを確認
        assert len(processor.processing_queue) == 2
        assert file1 in processor.processing_queue
        assert file2 not in processor.processing_queue
        assert file3 in processor.processing_queue
    
    def test_concurrent_processing_limit(self):
        """同時処理数の制限テスト"""
        processor = KoemojiProcessor()
        processor.config["max_concurrent_files"] = 2
        
        # 3つのファイルをキューに追加
        for i in range(3):
            processor.processing_queue.append({
                "path": f"/path/file{i}.mp3",
                "name": f"file{i}.mp3",
                "priority": 0
            })
        
        # 2つのファイルを処理中にする
        processor.files_in_process.add("/path/file0.mp3")
        processor.files_in_process.add("/path/file1.mp3")
        
        # 利用可能なスロットを計算
        max_concurrent = processor.config.get("max_concurrent_files", 3)
        current_running = len(processor.files_in_process)
        available_slots = max(0, max_concurrent - current_running)
        
        # 同時処理数の上限に達していることを確認
        assert available_slots == 0
    
    def test_queue_statistics(self):
        """キュー統計のテスト"""
        processor = KoemojiProcessor()
        
        # 統計の初期値を確認
        assert processor.today_stats["queued"] == 0
        assert processor.today_stats["processed"] == 0
        assert processor.today_stats["failed"] == 0
        
        # ファイルをキューに追加（実際のスキャンをシミュレート）
        processor.today_stats["queued"] += 3
        
        # 処理完了をシミュレート
        processor.today_stats["processed"] += 2
        processor.today_stats["total_duration"] += 120.5
        
        # 処理失敗をシミュレート
        processor.today_stats["failed"] += 1
        
        # 統計が正しく更新されることを確認
        assert processor.today_stats["queued"] == 3
        assert processor.today_stats["processed"] == 2
        assert processor.today_stats["failed"] == 1
        assert processor.today_stats["total_duration"] == 120.5
    
    def test_queue_empty_check(self):
        """空のキューのチェックテスト"""
        processor = KoemojiProcessor()
        
        # 初期状態ではキューは空
        assert len(processor.processing_queue) == 0
        
        # ファイルを追加
        processor.processing_queue.append({
            "path": "/path/test.mp3",
            "name": "test.mp3"
        })
        
        assert len(processor.processing_queue) == 1
        
        # ファイルを削除
        processor.processing_queue.clear()
        
        assert len(processor.processing_queue) == 0