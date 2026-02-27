#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "No se encontro python3/python en PATH"
    exit 1
  fi
fi

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -r requirements.txt pyinstaller

"${PYTHON_BIN}" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name TecladoOcular \
  --distpath dist-macos \
  --workpath build/pyinstaller-macos \
  --specpath build/pyinstaller-spec \
  main.py

if [[ -f "settings.yml" ]]; then
  cp "settings.yml" "dist-macos/settings.yml"
fi

echo "Build listo: dist-macos/TecladoOcular.app"
