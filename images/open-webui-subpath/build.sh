#!/usr/bin/env bash
# Builds the subpath-patched Open WebUI image used by manifests/open-webui/deployment.yaml.
# Upstream Open WebUI does not support serving behind a reverse-proxy
# subpath; this clones the official source at a pinned tag and applies
# patch/webui-subpath.patch on top, rather than trusting a third-party fork.
set -euo pipefail

TAG="${WEBUI_TAG:-v0.12.5}"
SUBPATH="${WEBUI_SUBPATH:-/webui}"
IMAGE="${IMAGE:-registry:5000/open-webui-subpath:${TAG}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

git clone --depth 1 --branch "$TAG" https://github.com/open-webui/open-webui.git "$WORKDIR"
git -C "$WORKDIR" apply "$SCRIPT_DIR/patch/webui-subpath.patch"

docker build \
  --build-arg WEBUI_SUBPATH="$SUBPATH" \
  --build-arg BUILD_HASH="${TAG}-subpath" \
  -t "$IMAGE" \
  "$WORKDIR"

echo "Built $IMAGE"
echo "Push with: docker push $IMAGE"
