#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import subprocess
import sys

def check_command_exists(command):
    """コマンドが既にインストールされているかどうかをチェックする"""
    try:
        subprocess.run([command, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def install_ffmpeg():
    """システムに応じてFFmpegをインストールする"""
    system = platform.system().lower()
    
    print("FFmpegをインストールしています...")
    
    if system == "linux":
        # 各種Linuxディストリビューションに対応
        if os.path.exists("/etc/debian_version"):
            # Debian/Ubuntu系
            try:
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
                print("FFmpegのインストールが完了しました。")
            except subprocess.CalledProcessError:
                print("FFmpegのインストールに失敗しました。手動でインストールしてください。")
                sys.exit(1)
        elif os.path.exists("/etc/redhat-release"):
            # RedHat/CentOS/Fedora系
            try:
                subprocess.run(["sudo", "yum", "install", "-y", "ffmpeg"], check=True)
                print("FFmpegのインストールが完了しました。")
            except subprocess.CalledProcessError:
                # Fedoraの場合はdnfを試す
                try:
                    subprocess.run(["sudo", "dnf", "install", "-y", "ffmpeg"], check=True)
                    print("FFmpegのインストールが完了しました。")
                except subprocess.CalledProcessError:
                    print("FFmpegのインストールに失敗しました。手動でインストールしてください。")
                    sys.exit(1)
        elif os.path.exists("/etc/arch-release"):
            # Arch Linux
            try:
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"], check=True)
                print("FFmpegのインストールが完了しました。")
            except subprocess.CalledProcessError:
                print("FFmpegのインストールに失敗しました。手動でインストールしてください。")
                sys.exit(1)
        else:
            print("Linuxディストリビューションを特定できませんでした。")
            print("手動でFFmpegをインストールしてください。")
            sys.exit(1)
    
    elif system == "darwin":  # macOS
        try:
            # Homebrewがインストールされているか確認
            try:
                subprocess.run(["brew", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                print("Homebrewがインストールされていません。インストールしています...")
                homebrew_install = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                subprocess.run(homebrew_install, shell=True, check=True)
            
            # FFmpegをインストール
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
            print("FFmpegのインストールが完了しました。")
        except subprocess.CalledProcessError:
            print("FFmpegのインストールに失敗しました。手動でインストールしてください。")
            sys.exit(1)
    
    elif system == "windows":
        # まずChocolateyでインストールを試みる
        try:
            # Chocolateyがインストールされているか確認
            subprocess.run(["choco", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("Chocolateyが検出されました。FFmpegをインストールしています...")
            
            try:
                # 管理者権限が必要な場合があるので、エラーハンドリングを追加
                subprocess.run(["choco", "install", "ffmpeg", "-y", "--no-progress"], check=True)
                print("FFmpegのインストールが完了しました。")
                print("新しいコマンドプロンプトを開いて使用してください。")
            except subprocess.CalledProcessError:
                print("Chocolateyでのインストールに失敗しました。")
                print("管理者権限でコマンドプロンプトを開いて実行するか、手動インストールをお試しください。")
                raise
                
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Chocolateyがない、または失敗した場合は手動インストールの案内
            print("\nChocolateyがインストールされていないか、インストールに失敗しました。")
            print("\n以下の方法でFFmpegを手動インストールしてください:")
            print("1. https://ffmpeg.org/download.html からWindows用バイナリをダウンロード")
            print("2. ZIPファイルを展開し、適当な場所（例: C:\\ffmpeg）に配置")
            print("3. システム環境変数のPATHに ffmpeg.exe のあるフォルダを追加")
            print("4. コマンドプロンプトを再起動して 'ffmpeg -version' で確認")
            print("\n詳細な手順は https://ffmpeg.org/download.html#build-windows を参照してください。")
            sys.exit(1)
    else:
        print(f"サポートされていないシステム: {system}")
        print("FFmpegを手動でインストールしてください。")
        sys.exit(1)

def install_faster_whisper():
    """Faster Whisperをインストールする"""
    print("Faster Whisperをインストールしています...")
    
    try:
        # 必要な依存関係をインストール
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # CUDAがインストールされているかチェック
        cuda_available = False
        try:
            import torch
            cuda_available = torch.cuda.is_available()
        except ImportError:
            # PyTorchがインストールされていない場合、CUDAは利用できないと仮定
            pass
        
        # Faster Whisperをインストール
        if cuda_available:
            subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], check=True)
            print("Faster Whisper (CUDA対応版) のインストールが完了しました。")
        else:
            subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], check=True)
            print("Faster Whisper (CPU版) のインストールが完了しました。")
            print("注意: GPU加速を利用するには、CUDAとPyTorchのCUDA版が必要です。")
    
    except subprocess.CalledProcessError:
        print("Faster Whisperのインストールに失敗しました。手動でインストールしてください。")
        sys.exit(1)

def install_other_dependencies():
    """その他の必要な依存関係をインストールする"""
    print("\nその他の依存関係をインストールしています...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        # faster-whisperは既にインストール済みなので除外
        requirements = [r for r in requirements if 'faster-whisper' not in r and r.strip()]
        
        if requirements:
            subprocess.run([sys.executable, "-m", "pip", "install"] + requirements, check=True)
            print("すべての依存関係のインストールが完了しました。")
    except FileNotFoundError:
        print("requirements.txt が見つかりません。")
    except subprocess.CalledProcessError:
        print("一部の依存関係のインストールに失敗しました。")

def verify_installations():
    """インストールが成功したかどうかを確認する"""
    ffmpeg_installed = check_command_exists("ffmpeg")
    
    # Faster Whisperがインストールされているかどうかを確認
    try:
        subprocess.run([sys.executable, "-c", "import faster_whisper"], check=True)
        faster_whisper_installed = True
    except subprocess.CalledProcessError:
        faster_whisper_installed = False
    
    print("\n=============== 検証結果 ===============")
    print(f"FFmpeg: {'✅ インストール済み' if ffmpeg_installed else '❌ インストールされていません'}")
    print(f"Faster Whisper: {'✅ インストール済み' if faster_whisper_installed else '❌ インストールされていません'}")
    
    # その他の依存関係を確認
    dependencies_ok = True
    try:
        subprocess.run([sys.executable, "-c", "import psutil; import flask"], check=True)
        print("その他の依存関係: ✅ インストール済み")
    except subprocess.CalledProcessError:
        print("その他の依存関係: ❌ 一部不足しています")
        dependencies_ok = False
    
    print("========================================")
    
    if ffmpeg_installed and faster_whisper_installed and dependencies_ok:
        print("\n🎉 すべてのツールが正常にインストールされました！")
        print("\nKoemojiAutoを開始するには:")
        print("  ./tui.sh    # macOS/Linux")
        print("  tui.bat     # Windows")
    else:
        print("\n⚠️  一部のツールがインストールされていません。")
        print("手動でインストールする必要があるかもしれません。")

def main():
    print("=====================================")
    print("KoemojiAuto 依存関係インストーラー")
    print("=====================================\n")
    
    system = platform.system()
    python_version = sys.version.split()[0]
    
    print(f"システム: {system}")
    print(f"Python: {python_version}")
    print()
    
    # FFmpegがすでにインストールされているかチェック
    if check_command_exists("ffmpeg"):
        print("✓ FFmpegはすでにインストールされています。")
    else:
        install_ffmpeg()
    
    # Faster Whisperがすでにインストールされているかチェック
    try:
        subprocess.run([sys.executable, "-c", "import faster_whisper"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✓ Faster Whisperはすでにインストールされています。")
    except subprocess.CalledProcessError:
        install_faster_whisper()
    
    # その他の依存関係をインストール
    install_other_dependencies()
    
    # インストールを検証
    verify_installations()

if __name__ == "__main__":
    main()