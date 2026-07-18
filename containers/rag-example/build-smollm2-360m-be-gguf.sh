#!/usr/bin/env bash
# Self-convert bartowski/SmolLM2-360M-Instruct-GGUF/SmolLM2-360M-Instruct-Q4_K_M.gguf
# (little-endian) to a big-endian copy that runs under llama.cpp on s390x.
#
# SmolLM2-360M-Instruct is ~3.6x smaller than Llama-3.2-1B (default RAG model),
# so on memory-bandwidth-bound s390x CPU it decodes ~3x faster while still
# being instruction-tuned and adequate for RAG over short policy chunks.
#
# Run on Mac (or any LE host); the resulting BE Q4_K_M file is portable to any
# big-endian host (z14 / z15 / z16 / z17). zDNN/NNPA does not accelerate
# quantized tensors -- this build targets the CPU/VXE2 path for hosts without
# NNPA (e.g. z14/z15) where it gives the biggest practical speedup.
#
# Prereqs: python3 (>=3.9), ~1 GB free disk. One-time pip install of
# huggingface_hub + gguf into a venv inside $OUT_DIR (no system-wide changes).
#
# Usage:
#   ./containers/rag-example/build-smollm2-360m-be-gguf.sh
#   OUT_DIR=$HOME/llama_models ./containers/rag-example/build-smollm2-360m-be-gguf.sh
#
# Optional overrides (env):
#   OUT_DIR    Where to keep both files (default: $HOME/llama_models)
#   SRC_REPO   HF repo holding the LE GGUF (default: bartowski/SmolLM2-360M-Instruct-GGUF)
#   SRC_FILE   File name in that repo      (default: SmolLM2-360M-Instruct-Q4_K_M.gguf)
#   OUT_FILE   Final BE file name           (default: smollm2-360m-instruct-be.Q4_K_M.gguf)

set -euo pipefail

# Q8_0 is the default because gguf_convert_endian only supports a subset of
# quant types -- Q4_K_M / Q5_K_M and other "K-quants" from bartowski's repo
# embed Q5_0 sub-tensors that the byte-swap script rejects with
# "Cannot handle type Q5_0 for tensor ...". Q8_0 is a pure int8 quant with one
# fp16 scale per block, converts cleanly, and is still ~57% smaller than the
# default Llama-3.2-1B-Q5_K_S baked into the RAG image (~900 MB -> ~386 MB).
# If you want a smaller / faster file, the safer route is convert_hf_to_gguf.py
# --bigendian on the safetensors repo (HuggingFaceTB/SmolLM2-360M-Instruct).
SRC_REPO="${SRC_REPO:-bartowski/SmolLM2-360M-Instruct-GGUF}"
SRC_FILE="${SRC_FILE:-SmolLM2-360M-Instruct-Q8_0.gguf}"
OUT_DIR="${OUT_DIR:-$HOME/llama_models}"
OUT_FILE="${OUT_FILE:-smollm2-360m-instruct-be.Q8_0.gguf}"

mkdir -p "$OUT_DIR"
cd "$OUT_DIR"

echo "==> Output dir: $OUT_DIR"
echo "==> Source:     $SRC_REPO/$SRC_FILE"
echo "==> Target:     $OUT_FILE"

if [ ! -x ".venv/bin/python" ]; then
  echo "==> Creating venv at $OUT_DIR/.venv"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet --upgrade "huggingface_hub" "gguf"

if [ ! -f "$SRC_FILE" ]; then
  echo "==> Downloading $SRC_FILE (~250 MB) ..."
  python - <<PY
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id="$SRC_REPO", filename="$SRC_FILE", local_dir="$OUT_DIR")
PY
else
  echo "==> Reusing cached $SRC_FILE"
fi

echo "==> Copying $SRC_FILE -> $OUT_FILE"
cp -f "$SRC_FILE" "$OUT_FILE"

echo "==> Byte-swapping $OUT_FILE to big-endian (rewrites in place) ..."
echo "YES" | python -m gguf.scripts.gguf_convert_endian "$OUT_FILE" big

echo "==> Verifying $OUT_FILE is big-endian ..."
python -m gguf.scripts.gguf_convert_endian --dry-run "$OUT_FILE" big

echo
echo "Done."
ls -la "$OUT_DIR/$OUT_FILE"

cat <<EOF

To deploy on LinuxONE (override the default Llama-3.2-1B path):

  # 1) One-time: scp the BE Q8_0 to the LinuxONE host
  scp "$OUT_DIR/$OUT_FILE" root@<server>:/root/llama_models/$OUT_FILE

  # 2) Re-run the RAG container with -v /root/llama_models:/opt/models and
  #    -e LLAMA_CPP_MODEL_REPO= -e LLAMA_CPP_MODEL_FILE=$OUT_FILE
  #    -e LLAMA_CPP_MODEL_DIR=/opt/models
  #    (empty LLAMA_CPP_MODEL_REPO tells query_rag.py to load straight from the
  #    mount instead of downloading from Hugging Face -- see
  #    examples/rag-example/open_llm/query_rag.py lines ~187-205.)
EOF
