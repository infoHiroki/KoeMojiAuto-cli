#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoemojiAuto - コマンドラインインターフェース
シンプルなTUIでKoemojiAutoを操作
"""

import os
import time
import json
import subprocess
import utils

def clear_screen():
    """画面をクリア"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_recent_logs(lines=7):
    """最新のログを表示"""
    log_path = 'koemoji.log'
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
                for line in recent_lines:
                    print(line.strip())
        except:
            print("ログ読み込みエラー")
    else:
        print("ログファイルがありません")

def get_status_display():
    """ステータス表示文字列を取得"""
    running = utils.check_if_running()
    status = "実行中" if running else "停止中"
    status_symbol = "●" if running else "○"
    return f"{status_symbol} {status}"

def display_menu():
    """メニューを表示"""
    print("=" * 40)
    print("     KoeMojiAuto コマンドライン")
    print("=" * 40)
    print(f"状態: {get_status_display()}")
    print("-" * 40)
    print("  1. 開始      - 文字起こしを開始")
    print("  2. 停止      - 文字起こしを停止")
    print("  3. 設定表示  - 現在の設定を確認")
    print("  0. 終了      - プログラムを終了")
    print("-" * 40)

def main_loop():
    """メインループ"""
    while True:
        clear_screen()
        display_menu()
        
        # ログ表示領域
        print("\n最新ログ:")
        print("-" * 40)
        show_recent_logs(5)  # 最新の5行だけ表示
        print("-" * 40)
        
        # コマンド受付と処理
        choice = input("\n選択> ")
        
        if choice == "1":
            subprocess.run(["start_koemoji.bat"], shell=True)
            print("開始コマンドを実行しました")
            time.sleep(1)
        elif choice == "2":
            subprocess.run(["stop_koemoji.bat"], shell=True)
            print("停止コマンドを実行しました")
            time.sleep(1)
        elif choice == "3":
            try:
                with open("config.json", "r", encoding='utf-8') as f:
                    config = json.load(f)
                print("\n--- 設定内容 ---")
                for key, value in config.items():
                    print(f"{key}: {value}")
                input("\nEnterキーで戻る...")
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
                time.sleep(2)
        elif choice == "0":
            break
        else:
            print("無効な選択です")
            time.sleep(0.5)

# メインプログラム実行
if __name__ == "__main__":
    main_loop()