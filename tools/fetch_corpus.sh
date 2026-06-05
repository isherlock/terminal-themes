#!/usr/bin/env bash
# Fetch the mbadolato iTerm2-Color-Schemes corpus into ./corpus (gitignored).
# Only the schemes/ folder is pulled (blobless + sparse) to skip the repo's
# large preview images. Re-run to update, then `python3 tools/build_themes.py`.
#
# Usage: tools/fetch_corpus.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/mbadolato/iTerm2-Color-Schemes.git "$TMP"
git -C "$TMP" sparse-checkout set schemes

mkdir -p "$ROOT/corpus"
cp "$TMP"/schemes/*.itermcolors "$ROOT/corpus/"
echo "Fetched $(ls "$ROOT"/corpus/*.itermcolors | wc -l | tr -d ' ') schemes into corpus/"
