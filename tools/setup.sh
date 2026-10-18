#!/bin/sh
# Prepara la sesión: dependencias del generador y del motor de voz.
set -e
cd "$(dirname "$0")"
[ -d node_modules/playwright-core ] || npm i -q --no-audit --no-fund
python3 -c "import sherpa_onnx, soundfile" 2>/dev/null || pip install -q --break-system-packages sherpa-onnx soundfile
command -v ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -qq ffmpeg)
echo "listo"
