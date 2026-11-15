#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="$HOME/.cache/euro-ai/llama.cpp"
MODEL_DIR="$HOME/.local/share/euro-ai/models"
MODEL="$MODEL_DIR/Qwen3.5-0.8B-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/axteam/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-Q4_K_M.gguf"
MODEL_SHA="b4e71cb32694733ba40c69e595a0524dfbc2cabe3c28fb7fef99eed4cf8730bf"

if [ ! -x "$PREFIX/bin/cmake" ] || [ ! -x "$PREFIX/bin/clang" ] || [ ! -x "$PREFIX/bin/make" ]; then
  pkg install -y git cmake clang make pkg-config curl coreutils
fi
mkdir -p "$(dirname "$CACHE")" "$MODEL_DIR"

if [ ! -d "$CACHE/.git" ]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$CACHE"
else
  git -C "$CACHE" pull --ff-only
fi

if [ ! -x "$CACHE/build/bin/llama-server" ]; then
  cmake -S "$CACHE" -B "$CACHE/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_OPENMP=OFF \
    -DGGML_NATIVE=ON \
    -DLLAMA_BUILD_SERVER=ON \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_CURL=OFF
  cmake --build "$CACHE/build" --config Release -j2 --target llama-server
fi

if [ ! -s "$MODEL" ]; then
  echo "Téléchargement du modèle Q4 (environ 542 Mo)…"
  curl -fL --retry 3 --retry-delay 2 "$MODEL_URL" -o "$MODEL.part"
  mv "$MODEL.part" "$MODEL"
fi

if command -v sha256sum >/dev/null 2>&1; then
  echo "$MODEL_SHA  $MODEL" | sha256sum -c -
else
  echo "sha256sum absent : installe coreutils puis vérifie le modèle."
  exit 1
fi

echo
echo "Installation du cerveau terminée."
echo "Lance : bash scripts/start-local-brain.sh"
