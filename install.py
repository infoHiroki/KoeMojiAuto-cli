#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoeMoji クロスプラットフォーム インストーラー
Windows/Mac/Linux対応
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header():
    """ヘッダーを表示"""
    print("=" * 40)
    print("         KoeMoji Setup")
    print("=" * 40)
    print(f"Platform: {platform.system()}")
    print()

def install_dependencies():
    """依存関係をインストール"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        print("  Make sure Python and pip are installed correctly")
        return False

def create_directories():
    """必要なディレクトリを作成"""
    print("\nCreating directories...")
    directories = ["input", "output", "archive"]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ Created {dir_name}/")

def create_config():
    """設定ファイルを作成"""
    print("\nCreating config...")
    
    if not Path("config.json").exists() and Path("config.sample").exists():
        shutil.copy("config.sample", "config.json")
        print("✓ Created config.json from config.sample")
    elif Path("config.json").exists():
        print("✓ config.json already exists")
    else:
        print("⚠ config.sample not found, config.json will be created on first run")

def create_executable_scripts():
    """実行用スクリプトを作成"""
    print("\nCreating executable scripts...")
    
    # Windowsの場合はバッチファイルは既存のものを使用
    if platform.system() == "Windows":
        print("✓ Using existing batch files for Windows")
    else:
        # Mac/Linux用のシェルスクリプトを作成
        shell_script = """#!/bin/bash
cd "$(dirname "$0")"
echo "Starting KoeMoji..."
python3 koemoji.py
"""
        
        with open("run.sh", "w") as f:
            f.write(shell_script)
        
        # 実行権限を付与
        os.chmod("run.sh", 0o755)
        print("✓ Created run.sh for Mac/Linux")

def main():
    """メイン処理"""
    print_header()
    
    # 依存関係のインストール
    if not install_dependencies():
        print("\n✗ Installation failed")
        sys.exit(1)
    
    # ディレクトリ作成
    create_directories()
    
    # 設定ファイル作成
    create_config()
    
    # 実行スクリプト作成
    create_executable_scripts()
    
    print("\n" + "=" * 40)
    print("      Setup Complete! 🎉")
    print("=" * 40)
    
    if platform.system() == "Windows":
        print("\nTo start KoeMoji, run: run.bat")
        print("Or double-click run.bat in Explorer")
    else:
        print("\nTo start KoeMoji, run: ./run.sh")
        print("Or: python3 koemoji.py")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()