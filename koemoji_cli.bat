@echo off
REM CLIモードでkoemoji.pyを実行
echo KoeMojiAuto CLIを起動中...
python "%~dp0koemoji.py" --cli
REM コマンドの終了コードをチェック
if %ERRORLEVEL% NEQ 0 (
    echo エラーが発生しました（エラーコード: %ERRORLEVEL%）
    pause
)