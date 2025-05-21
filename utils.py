#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoemojiAuto - ユーティリティモジュール
共通の機能やヘルパー関数を提供
"""

import os
import logging
import shutil
from pathlib import Path
import platform

# OS判定
IS_WINDOWS = platform.system() == 'Windows'

# ロギング設定
logger = None

def setup_logging(log_file='koemoji.log', level=logging.INFO):
    """ロギングの設定"""
    global logger
    
    logging.basicConfig(
        filename=log_file,
        level=level,
        format='%(asctime)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M'
    )
    
    logger = logging.getLogger("KoemojiAuto")
    return logger

def log_and_print(message, level="info"):
    """ログとコンソールの両方に出力"""
    global logger
    
    if logger is None:
        logger = setup_logging()
    
    if level == "info":
        logger.info(message)
    elif level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
        return  # デバッグメッセージはコンソールには出さない
        
    print(message)  # コンソールにも出力

def ensure_directory(path_str):
    """ディレクトリの存在を確認し、必要に応じて作成"""
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_move_file(source, destination):
    """ファイルを安全に移動（同名ファイル対応）"""
    dest_path = Path(destination)
    
    # 同名ファイルがある場合は名前を変更
    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            dest_path = dest_path.with_name(new_name)
            counter += 1
    
    # 移動実行
    shutil.move(source, str(dest_path))
    return dest_path

def get_stop_flag_path():
    """停止フラグファイルのパスを取得"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "stop_koemoji.flag")

def check_if_running():
    """実行中かどうかを確認（停止フラグがない場合は実行中）"""
    return not os.path.exists(get_stop_flag_path())

# 初期設定
logger = setup_logging()
