#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoeMojiAuto - スタートアップ登録解除スクリプト
OS起動時の自動実行を解除
"""

import os
import sys
import platform
import subprocess

def get_script_path():
    """実行スクリプトの絶対パスを取得"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if platform.system() == "Windows":
        return os.path.join(base_dir, "run.bat")
    else:
        return os.path.join(base_dir, "run.py")

def remove_windows():
    """Windowsのスタートアップ解除"""
    try:
        # スタートアップフォルダのパス
        startup_path = os.path.join(
            os.environ['APPDATA'],
            'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
        )
        
        # ショートカットのパス
        shortcut_path = os.path.join(startup_path, "KoeMojiAuto.lnk")
        
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print(f"✓ スタートアップから削除しました: {shortcut_path}")
            return True
        else:
            print("✓ スタートアップに登録されていません")
            return True
            
    except Exception as e:
        print(f"✗ 削除エラー: {e}")
        return False

def remove_macos():
    """macOSのログイン項目解除"""
    try:
        script_path = get_script_path()
        
        # AppleScriptでログイン項目から削除
        applescript = f'''
        tell application "System Events"
            try
                delete login item "{os.path.basename(script_path)}"
            end try
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True
        )
        
        print(f"✓ ログイン項目から削除しました")
        print("  システム環境設定 > ユーザとグループ > ログイン項目 で確認できます")
        return True
            
    except Exception as e:
        print(f"✗ 削除エラー: {e}")
        return False

def remove_linux():
    """Linuxのcrontab解除"""
    try:
        script_path = get_script_path()
        
        # 現在のcrontabを取得
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("✓ crontabに登録されていません")
            return True
        
        current_cron = result.stdout
        
        # KoeMojiAutoのエントリを削除
        new_cron_lines = []
        removed = False
        
        for line in current_cron.splitlines():
            if script_path not in line:
                new_cron_lines.append(line)
            else:
                removed = True
        
        if not removed:
            print("✓ crontabに登録されていません")
            return True
        
        # crontabを更新
        new_cron = '\n'.join(new_cron_lines) + '\n' if new_cron_lines else ''
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode == 0:
            print(f"✓ crontabから削除しました")
            print("  確認: crontab -l")
            return True
        else:
            print("✗ crontab更新エラー")
            return False
            
    except Exception as e:
        print(f"✗ 削除エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("KoeMojiAuto - スタートアップ登録解除")
    print("=" * 40)
    
    system = platform.system()
    
    if system == "Windows":
        print("OS: Windows")
        success = remove_windows()
    elif system == "Darwin":
        print("OS: macOS")
        success = remove_macos()
    elif system == "Linux":
        print("OS: Linux")
        success = remove_linux()
    else:
        print(f"✗ サポートされていないOS: {system}")
        success = False
    
    if success:
        print("\n解除完了！OS起動時の自動実行が無効になりました。")
    else:
        print("\n解除に失敗しました。")
    
    return success

if __name__ == "__main__":
    success = main()
    input("\nEnterキーで終了...")
    sys.exit(0 if success else 1)