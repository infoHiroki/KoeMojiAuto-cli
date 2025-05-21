#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoemojiAuto - 文字起こしエンジンモジュール
Whisperモデルを使用した音声・動画からの文字起こし処理
"""

import os
import time
from pathlib import Path
import utils

class TranscriptionEngine:
    def __init__(self, config_manager):
        """初期化"""
        self.config = config_manager
        self._whisper_model = None
        self._model_config = None
    
    def transcribe(self, file_path):
        """音声ファイルを文字起こし"""
        start_time = time.time()
        file_name = os.path.basename(file_path)
        
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            utils.log_and_print("faster_whisperがインストールされていません。pip install faster-whisperを実行してください。", "error")
            return None
        
        try:
            # モデルサイズとコンピュートタイプを設定
            model_size = self.config.get("whisper_model", "large")
            compute_type = self.config.get("compute_type", "int8")
            
            # モデルが未ロードか設定が変わった場合のみ再ロード
            if (self._whisper_model is None or 
                self._model_config != (model_size, compute_type)):
                utils.log_and_print(f"Whisperモデルをロード中: {model_size}")
                self._whisper_model = WhisperModel(model_size, compute_type=compute_type)
                self._model_config = (model_size, compute_type)
            
            utils.log_and_print(f"文字起こし開始: {file_name}")
            
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
                    utils.log_and_print(f"文字起こし進行中: {file_name} - {segment_count}セグメント処理済み")
            
            # 処理時間を計算
            processing_time = time.time() - start_time
            utils.log_and_print(f"文字起こし完了: {file_name} - 合計{segment_count}セグメント (処理時間: {processing_time:.2f}秒)")
            
            return "\n".join(transcription)
        
        except Exception as e:
            utils.log_and_print(f"文字起こし処理中にエラーが発生しました: {e}", "error")
            return None