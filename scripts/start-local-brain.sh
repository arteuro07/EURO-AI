#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BIN_DIR="$HOME/.local/bin/euro-ai"
SERVER="$BIN_DIR/llama-server"
MODEL="$HOME/.local/share/euro-ai/models/Qwen3.5-0.8B-Q4_K_M.gguf"

[ -x "$SERVER" ] || { echo "llama-server absent. Lance d'abord bash scripts/setup-local-brain.sh"; exit 1; }
[ -s "$BIN_DIR/libllama-server-impl.so" ] || { echo "Bibliothèques manquantes. Relance bash scripts/setup-local-brain.sh après le nouveau build GitHub."; exit 1; }
[ -s "$MODEL" ] || { echo "Modèle absent. Lance d'abord bash scripts/setup-local-brain.sh"; exit 1; }

export LD_LIBRARY_PATH="$BIN_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$SERVER" \
  --model "$MODEL" \
  --host 127.0.0.1 \
  --port 8080 \
  --ctx-size 4096 \
  --threads 3 \
  --batch-size 128 \
  --ubatch-size 64 \
  --parallel 1 \
  --jinja
