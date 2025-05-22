@echo off
echo KoeMojiAuto EXE ビルド開始...

echo.
echo 依存関係をチェック中...
pip list | find "pyinstaller" >nul
if errorlevel 1 (
    echo PyInstallerがインストールされていません。インストール中...
    pip install pyinstaller
)

pip list | find "faster-whisper" >nul
if errorlevel 1 (
    echo faster-whisperがインストールされていません。インストール中...
    pip install -r requirements.txt
)

echo.
echo ビルド中...
pyinstaller build.spec

echo.
echo ビルド完了！
echo EXEファイルは dist フォルダに生成されました。
echo.
pause
