#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="arteuro07/EURO-AI"
WORKFLOW="build-android-llama.yml"
ARTIFACT="llama-server-android-arm64"
BIN_DIR="$HOME/.local/bin/euro-ai"
MODEL_DIR="$HOME/.local/share/euro-ai/models"
MODEL="$MODEL_DIR/Qwen3.5-0.8B-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/axteam/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-Q4_K_M.gguf"
MODEL_SHA="b4e71cb32694733ba40c69e595a0524dfbc2cabe3c28fb7fef99eed4cf8730bf"

for tool in gh curl sha256sum unzip; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Outil manquant : $tool"
    echo "Installe-le avec : pkg install gh curl coreutils unzip"
    exit 1
  fi
done

gh auth status >/dev/null 2>&1 || {
  echo "GitHub CLI n'est pas connecté."
  echo "Lance : gh auth login"
  exit 1
}

echo "Recherche du dernier build Android réussi sur GitHub Actions…"
RUN_ID="$(gh run list --repo "$REPO" --workflow "$WORKFLOW" --status success --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
if [ -z "$RUN_ID" ]; then
  echo "Aucun build Android réussi trouvé."
  echo "Lance d'abord le workflow : $WORKFLOW"
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
gh run download "$RUN_ID" --repo "$REPO" --name "$ARTIFACT" --dir "$TMP_DIR"

mkdir -p "$BIN_DIR" "$MODEL_DIR"
FOUND_SERVER=0
while IFS= read -r -d '' FILE; do
  BASE="$(basename "$FILE")"
  case "$BASE" in
    llama-server|*.so)
      install -m 755 "$FILE" "$BIN_DIR/$BASE"
      [ "$BASE" != "llama-server" ] || FOUND_SERVER=1
      ;;
  esac
done < <(find "$TMP_DIR" -type f -print0)

[ "$FOUND_SERVER" -eq 1 ] || { echo "llama-server absent de l'artefact."; exit 1; }
[ -s "$BIN_DIR/libllama-server-impl.so" ] || {
  echo "Bibliothèque libllama-server-impl.so absente de l'artefact."
  exit 1
}
echo "Serveur et bibliothèques Android installés dans : $BIN_DIR"
ls -lh "$BIN_DIR"/llama-server "$BIN_DIR"/*.so

if [ ! -s "$MODEL" ]; then
  echo "Téléchargement du modèle Q4 (environ 542 Mo)…"
  curl -fL --retry 3 --retry-delay 2 "$MODEL_URL" -o "$MODEL.part"
  mv "$MODEL.part" "$MODEL"
fi

echo "$MODEL_SHA  $MODEL" | sha256sum -c -
echo
echo "Installation terminée."
echo "Lance : bash scripts/start-local-brain.sh"
