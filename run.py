#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoeMoji クロスプラットフォーム ランチャー
Windows/Mac/Linux対応
"""

import os
import sys
import platform
import subprocess

def main():
    """メイン処理"""
    # 現在のディレクトリに移動
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("KOEMOJI Starting...")
    
    try:
        # Pythonスクリプトを実行
        subprocess.run([sys.executable, "koemoji.py"])
    except KeyboardInterrupt:
        print("\nKoeMoji stopped by user")
    except Exception as e:
        print(f"Error occurred while running koemoji.py: {e}")
        if platform.system() == "Windows":
            input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()