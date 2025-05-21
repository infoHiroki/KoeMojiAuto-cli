@echo off
echo KoemojiAutoに停止信号を送信しています...

rem 停止フラグファイルを作成
echo 1 > stop_koemoji.flag

echo 停止フラグを作成しました。
echo プログラムは次のサイクルで終了します（最大5秒）

timeout /t 5 /nobreak > nul
echo Done