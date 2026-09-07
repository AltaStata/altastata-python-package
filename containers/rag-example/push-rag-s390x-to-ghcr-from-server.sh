#!/usr/bin/env bash
# Push the RAG s390x image from LinuxONE to GHCR.
# Run from repo root:
#   SSH_HOST=ubuntu@linuxone ./containers/rag-example/push-rag-s390x-to-ghcr-from-server.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$REPO_ROOT/version.sh"

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
: "${SSH_HOST:?Set SSH_HOST=user@your-linuxone-host}"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=accept-new -o GSSAPIAuthentication=no -o PreferredAuthentications=publickey"
GHCR_USER="${GHCR_USER:-$(gh api user --jq .login 2>/dev/null || true)}"
GHCR_TOKEN="${GHCR_TOKEN:-$(gh auth token 2>/dev/null || true)}"
: "${GHCR_USER:?Set GHCR_USER or authenticate gh}"
: "${GHCR_TOKEN:?Set GHCR_TOKEN or authenticate gh with write:packages}"

if [ "${ENABLE_ZDNN:-0}" = "1" ]; then
  SOURCE="altastata/rag-open-llm-s390x:${RAG_VERSION}_zdnn"
  DESTINATIONS="ghcr.io/altastata/rag-open-llm-s390x:${RAG_VERSION}_zdnn"
else
  SOURCE="altastata/rag-open-llm-s390x:${RAG_VERSION}"
  DESTINATIONS="ghcr.io/altastata/rag-open-llm-s390x:${RAG_VERSION} ghcr.io/altastata/rag-open-llm-s390x:latest"
fi

printf '%s' "$GHCR_TOKEN" |
  ssh $SSH_OPTS "$SSH_HOST" "docker login ghcr.io -u '$GHCR_USER' --password-stdin"

for destination in $DESTINATIONS; do
  ssh $SSH_OPTS "$SSH_HOST" \
    "docker tag '$SOURCE' '$destination' && docker push '$destination'"
done

echo "Published: $DESTINATIONS"
