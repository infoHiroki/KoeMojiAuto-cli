#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KoeMojiAuto - スタートアップ登録スクリプト
OS起動時の自動実行を設定
"""

import os
import sys
import platform
import shutil
import subprocess

def get_script_path():
    """実行スクリプトの絶対パスを取得"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if platform.system() == "Windows":
        return os.path.join(base_dir, "run.bat")
    else:
        return os.path.join(base_dir, "run.py")

def register_windows():
    """Windowsのスタートアップ登録"""
    try:
        # スタートアップフォルダのパス
        startup_path = os.path.join(
            os.environ['APPDATA'],
            'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
        )
        
        # ショートカットのパスを作成
        shortcut_name = "KoeMojiAuto.lnk"
        shortcut_path = os.path.join(os.path.dirname(__file__), shortcut_name)
        
        # ショートカットが存在する場合はコピー
        if os.path.exists(shortcut_path):
            dest_path = os.path.join(startup_path, shortcut_name)
            shutil.copy2(shortcut_path, dest_path)
            print(f"✓ スタートアップフォルダに登録しました: {dest_path}")
        else:
            print("！ ショートカットが見つかりません。")
            print("  先に create_shortcut.bat を実行してください。")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 登録エラー: {e}")
        return False

def register_macos():
    """macOSのログイン項目登録"""
    try:
        script_path = get_script_path()
        
        # AppleScriptでログイン項目に追加
        applescript = f'''
        tell application "System Events"
            make login item at end with properties {{path:"{script_path}", hidden:false}}
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ ログイン項目に登録しました: {script_path}")
            print("  システム環境設定 > ユーザとグループ > ログイン項目 で確認できます")
            return True
        else:
            print(f"✗ 登録エラー: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ 登録エラー: {e}")
        return False

def register_linux():
    """Linuxのcrontab登録"""
    try:
        script_path = get_script_path()
        python_path = sys.executable
        
        # crontabエントリ
        cron_entry = f'@reboot {python_path} {script_path}\n'
        
        # 現在のcrontabを取得
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        
        if result.returncode == 0:
            current_cron = result.stdout
        else:
            current_cron = ""
        
        # すでに登録されているか確認
        if script_path in current_cron:
            print("✓ すでにcrontabに登録されています")
            return True
        
        # 新しいエントリを追加
        new_cron = current_cron + cron_entry
        
        # crontabを更新
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode == 0:
            print(f"✓ crontabに登録しました")
            print(f"  エントリ: {cron_entry.strip()}")
            print("  確認: crontab -l")
            return True
        else:
            print("✗ crontab登録エラー")
            return False
            
    except Exception as e:
        print(f"✗ 登録エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("KoeMojiAuto - スタートアップ登録")
    print("=" * 40)
    
    system = platform.system()
    
    if system == "Windows":
        print("OS: Windows")
        success = register_windows()
    elif system == "Darwin":
        print("OS: macOS")
        success = register_macos()
    elif system == "Linux":
        print("OS: Linux")
        success = register_linux()
    else:
        print(f"✗ サポートされていないOS: {system}")
        success = False
    
    if success:
        print("\n設定完了！次回OS起動時から自動実行されます。")
        print("※ config.jsonで auto_start: true に設定してください。")
    else:
        print("\n登録に失敗しました。")
    
    return success

if __name__ == "__main__":
    success = main()
    input("\nEnterキーで終了...")
    sys.exit(0 if success else 1)