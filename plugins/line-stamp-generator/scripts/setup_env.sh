#!/usr/bin/env bash
# 仮想環境を作り、design-parts-generator スクリプトの依存を入れる。
# 既に .venv が存在する場合はインストールのみ更新する。

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] $VENV_DIR を作成します"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install --upgrade openai Pillow numpy scipy

echo "[setup] 完了しました。以降は $VENV_DIR/bin/python を使ってください。"
