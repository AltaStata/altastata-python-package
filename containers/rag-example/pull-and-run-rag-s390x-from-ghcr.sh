#!/usr/bin/env bash
# Pull and run the RAG s390x image from GHCR on a LinuxONE host.
#
# Required:
#   SSH_HOST=ubuntu@host
#   ACCOUNT_NAME=amazon.rsa.hpcs.serge678
# Optional private-package auth:
#   GHCR_USER=... GHCR_TOKEN=...

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$REPO_ROOT/version.sh"

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
: "${SSH_HOST:?Set SSH_HOST=user@your-linuxone-host}"
: "${ACCOUNT_NAME:?Set ACCOUNT_NAME to an AltaStata account directory name}"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=accept-new -o GSSAPIAuthentication=no -o PreferredAuthentications=publickey"

RAG_IMAGE="${RAG_IMAGE:-ghcr.io/altastata/rag-open-llm-s390x:${RAG_VERSION}}"
CONTAINER_NAME="${CONTAINER_NAME:-altastata-rag-s390x}"
REMOTE_ALTASTATA_ACCOUNTS="${REMOTE_ALTASTATA_ACCOUNTS:-/root/.altastata/accounts}"
REMOTE_MODELS_DIR="${REMOTE_MODELS_DIR:-/root/llama_models}"
REMOTE_INDEX_DIR="${REMOTE_INDEX_DIR:-/opt/altastata-rag-index}"
REMOTE_GREP11_YAML="${REMOTE_GREP11_YAML:-/etc/ep11client/grep11client.yaml}"
REMOTE_HPCS_DIR="${REMOTE_HPCS_DIR:-/home/jovyan/hpcs}"
ALTASTATA_ACCOUNT_ID="${ALTASTATA_ACCOUNT_ID:-${ACCOUNT_NAME##*.}}"
RAG_INDEX_PATH="${RAG_INDEX_PATH:-RAGDocs/policies}"
QUERY_TIMEOUT="${QUERY_TIMEOUT:-400}"

if [ -n "${GHCR_TOKEN:-}" ]; then
  : "${GHCR_USER:?Set GHCR_USER when GHCR_TOKEN is set}"
  printf '%s' "$GHCR_TOKEN" |
    ssh $SSH_OPTS "$SSH_HOST" "docker login ghcr.io -u '$GHCR_USER' --password-stdin"
fi

ssh $SSH_OPTS "$SSH_HOST" \
  "test -d '$REMOTE_ALTASTATA_ACCOUNTS/$ACCOUNT_NAME' &&
   mkdir -p '$REMOTE_MODELS_DIR' '$REMOTE_INDEX_DIR' &&
   docker pull '$RAG_IMAGE'"

HPCS_ENV=""
HPCS_MOUNTS=""
case "$ACCOUNT_NAME" in
  *hpcs*)
    ssh $SSH_OPTS "$SSH_HOST" \
      "test -f '$REMOTE_GREP11_YAML' && test -f '$REMOTE_HPCS_DIR/hpcs-privkey.blob'"
    HPCS_ENV="-e ALTASTATA_USE_HPCS=1 -e GREP11_YAML=/etc/ep11client/grep11client.yaml -e HPCS_PRIV_KEY_BLOB_PATH=/home/jovyan/hpcs/hpcs-privkey.blob"
    HPCS_MOUNTS="-v $REMOTE_GREP11_YAML:/etc/ep11client/grep11client.yaml:ro -v $REMOTE_HPCS_DIR:/home/jovyan/hpcs:ro"
    ;;
esac

LLAMA_OPTS=""
[ -n "${LLAMA_CPP_MODEL_REPO+x}" ] && LLAMA_OPTS="$LLAMA_OPTS -e LLAMA_CPP_MODEL_REPO=$LLAMA_CPP_MODEL_REPO"
[ -n "${LLAMA_CPP_MODEL_FILE:-}" ] && LLAMA_OPTS="$LLAMA_OPTS -e LLAMA_CPP_MODEL_FILE=$LLAMA_CPP_MODEL_FILE"
[ -n "${LLAMA_CPP_N_CTX:-}" ] && LLAMA_OPTS="$LLAMA_OPTS -e LLAMA_CPP_N_CTX=$LLAMA_CPP_N_CTX"
[ -n "${LLAMA_CPP_MAX_TOKENS:-}" ] && LLAMA_OPTS="$LLAMA_OPTS -e LLAMA_CPP_MAX_TOKENS=$LLAMA_CPP_MAX_TOKENS"

ssh $SSH_OPTS "$SSH_HOST" \
  "docker rm -f '$CONTAINER_NAME' >/dev/null 2>&1 || true
   docker run -d --name '$CONTAINER_NAME' --restart unless-stopped --user root \
     -p 127.0.0.1:8000:8000 -p 127.0.0.1:9878:9877 \
     -e ALTASTATA_ACCOUNT_DIR='$REMOTE_ALTASTATA_ACCOUNTS/$ACCOUNT_NAME' \
     -e ALTASTATA_ACCOUNT_ID='$ALTASTATA_ACCOUNT_ID' \
     -e RAG_INDEX_PATH='$RAG_INDEX_PATH' \
     -e QUERY_TIMEOUT='$QUERY_TIMEOUT' \
     $HPCS_ENV $LLAMA_OPTS \
     -v '$REMOTE_ALTASTATA_ACCOUNTS:$REMOTE_ALTASTATA_ACCOUNTS:ro' \
     -v '$REMOTE_MODELS_DIR:/models' \
     -v '$REMOTE_INDEX_DIR:/app/open_llm/local_index' \
     $HPCS_MOUNTS \
     '$RAG_IMAGE'"

for _ in $(seq 1 60); do
  if ssh $SSH_OPTS "$SSH_HOST" "curl -fsS http://127.0.0.1:8000/ >/dev/null"; then
    echo "RAG is running at 127.0.0.1:8000 on $SSH_HOST"
    exit 0
  fi
  sleep 5
done

ssh $SSH_OPTS "$SSH_HOST" "docker logs --tail 100 '$CONTAINER_NAME'"
exit 1
