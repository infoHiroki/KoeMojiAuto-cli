#!/bin/bash
# KoeMoji エイリアス設定スクリプト

# プロジェクトのパスを取得
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# シェルの種類を確認
SHELL_TYPE=$(basename "$SHELL")
CONFIG_FILE=""

if [ "$SHELL_TYPE" = "zsh" ]; then
    CONFIG_FILE="$HOME/.zshrc"
elif [ "$SHELL_TYPE" = "bash" ]; then
    # macOSの場合は.bash_profile、Linuxの場合は.bashrc
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CONFIG_FILE="$HOME/.bash_profile"
    else
        CONFIG_FILE="$HOME/.bashrc"
    fi
else
    echo "❌ Unsupported shell: $SHELL_TYPE"
    exit 1
fi

echo "🔧 Setting up KoeMoji aliases..."
echo "📁 Project directory: $PROJECT_DIR"
echo "🐚 Shell config file: $CONFIG_FILE"

# エイリアスを追加
cat >> "$CONFIG_FILE" << EOF

# KoeMoji Aliases (added by setup_aliases.sh)
alias koemoji='cd $PROJECT_DIR && python3 run.py'
alias koemoji-input='open $PROJECT_DIR/input'  # Finderで入力フォルダを開く
alias koemoji-output='open $PROJECT_DIR/output'  # Finderで出力フォルダを開く
alias koemoji-log='tail -f $PROJECT_DIR/koemoji.log'  # ログをリアルタイム表示
alias koemoji-config='${EDITOR:-nano} $PROJECT_DIR/config.json'  # 設定ファイルを編集

# 短縮版
alias km='koemoji'
alias kmi='koemoji-input'
alias kmo='koemoji-output'
alias kml='koemoji-log'
EOF

echo "✅ Aliases added to $CONFIG_FILE"
echo ""
echo "📝 Added aliases:"
echo "  koemoji       - KoeMojiを起動"
echo "  koemoji-input - 入力フォルダを開く"
echo "  koemoji-output - 出力フォルダを開く"
echo "  koemoji-log   - ログをリアルタイム表示"
echo "  koemoji-config - 設定ファイルを編集"
echo "  km           - koemoji の短縮版"
echo ""
echo "🔄 To activate now, run:"
echo "  source $CONFIG_FILE"
echo ""
echo "💡 Or restart your terminal"