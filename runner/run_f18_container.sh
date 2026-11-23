#!/usr/bin/env bash
# F18 evidence run inside the pinned image (owner decisions D-002a, D-002, D-003).
#
# All evaluation runs in the container's CPython 3.11.18; no host Python is used. This
# script only (1) builds/identifies the image, (2) starts the runner container and
# (3) acts as a broker: when the runner writes a line
#     OPENVEF_SANDBOX_REQUEST <timeout_seconds> <base64 request JSON>
# on its stdout, the broker starts one artifact container (runner/artifact-container.args)
# running the fixed command `python -I /opt/openvef/harness.py` with the decoded request
# on stdin, and writes back exactly one line on the runner's stdin:
#     OPENVEF_SANDBOX_REPLY TIMEOUT
#     OPENVEF_SANDBOX_REPLY DONE <exit code> <base64 stdout> <base64 stderr tail>
# The broker never interprets results. On timeout it kills and removes the container by
# its unique name. The runner cannot choose the command, image or flags.
#
# Usage: runner/run_f18_container.sh <run_class>
set -euo pipefail

RUN_CLASS=${1:?usage: run_f18_container.sh <run_class>}
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BASELINE="$REPO/baseline/OpenVEF_Planning_v1_3_6"
HARNESS_DIR="$REPO/sandbox"

# --- image -------------------------------------------------------------------------
# Tag = first 16 hex of SHA-256 over `sha256sum sandbox/Dockerfile requirements.lock`
# (same rule as openvef.sandbox.image_tag).
TAG="openvef-sandbox:$(cd "$REPO" && sha256sum sandbox/Dockerfile requirements.lock | sha256sum | cut -c1-16)"
if ! docker image inspect "$TAG" >/dev/null 2>&1; then
  docker build -q -t "$TAG" -f "$REPO/sandbox/Dockerfile" "$REPO" >/dev/null
fi
IMAGE_ID=$(docker image inspect "$TAG" --format '{{.Id}}')
BASE_DIGEST=$(sed -n 's/^FROM \(python@sha256:[0-9a-f]\{64\}\)$/\1/p' "$REPO/sandbox/Dockerfile")
[ -n "$BASE_DIGEST" ] || { echo "Dockerfile FROM is not pinned by digest" >&2; exit 2; }

# --- harness permission guard (see docs/sandbox.md) -----------------------------------
if find "$HARNESS_DIR" \( -perm -g+w -o -perm -o+w \) | grep -q .; then
  echo "harness directory has group- or other-writable entries" >&2; exit 2
fi

# --- flags -------------------------------------------------------------------------
read_args() {  # read_args <file> -> one flag per line, comments and blanks removed
  grep -v -e '^#' -e '^[[:space:]]*$' "$1"
}

GIT_COMMIT=$(git -C "$REPO" rev-parse HEAD)
if [ -n "$(git -C "$REPO" status --porcelain -- src runner sandbox requirements.lock)" ]; then
  GIT_COMMIT="$GIT_COMMIT+UNCOMMITTED_CHANGES"
fi

STARTED=$(date -u +%Y%m%dT%H%M%SZ)
# OPENVEF_EVIDENCE_ROOT is for smoke tests outside the append-only evidence/ tree.
OUT="${OPENVEF_EVIDENCE_ROOT:-$REPO/evidence}/run-$STARTED"
mkdir "$OUT"   # fails if it exists: evidence is append-only

RNAME="openvef-runner-$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')"
mapfile -t RUNNER_FLAGS < <(read_args "$REPO/runner/runner-container.args" \
  | sed -e "s|{REPO}|$REPO|g" -e "s|{BASELINE}|$BASELINE|g" -e "s|{OUT}|$OUT|g" \
        -e "s|{UID_GID}|$(id -u):$(id -g)|g" -e "s|{NAME}|$RNAME|g")

ARTIFACT_ARGS_FILE="$REPO/runner/artifact-container.args"
artifact_flags() {  # artifact_flags <name>
  read_args "$ARTIFACT_ARGS_FILE" | sed -e "s|{HARNESS_DIR}|$HARNESS_DIR|g" -e "s|{NAME}|$1|g"
}

# Identity passed to the runner for its evidence record (the runner computes the
# interpreter, toolchain and source hashes itself, inside the container).
b64() { base64 -w0; }
ENV_ARGS=(
  "--env=OPENVEF_RUN_STARTED=$STARTED"
  "--env=OPENVEF_GIT_COMMIT=$GIT_COMMIT"
  "--env=OPENVEF_IMAGE_TAG=$TAG"
  "--env=OPENVEF_IMAGE_ID=$IMAGE_ID"
  "--env=OPENVEF_BASE_IMAGE_DIGEST=$BASE_DIGEST"
  "--env=OPENVEF_DOCKER_VERSION=$(docker version --format '{{.Server.Version}}')"
  "--env=OPENVEF_HOST_KERNEL=$(uname -sr)"
  "--env=OPENVEF_LOCK_SHA256=$(sha256sum "$REPO/requirements.lock" | cut -c1-64)"
  "--env=OPENVEF_DOCKERFILE_SHA256=$(sha256sum "$REPO/sandbox/Dockerfile" | cut -c1-64)"
  "--env=OPENVEF_RUNNER_FLAGS_B64=$(printf '%s\n' "${RUNNER_FLAGS[@]}" | b64)"
  "--env=OPENVEF_ARTIFACT_FLAGS_B64=$(artifact_flags '<name>' | b64)"
  "--env=OPENVEF_BROKER_SHA256=$(sha256sum "${BASH_SOURCE[0]}" | cut -c1-64)"
)

# --- broker ------------------------------------------------------------------------
run_artifact() {  # run_artifact <timeout_s> <b64 request>  -> prints one reply line
  local t=$1 req=$2 name out err rc
  name="openvef-$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')"
  out=$(mktemp); err=$(mktemp)
  local -a flags
  mapfile -t flags < <(artifact_flags "$name")
  set +e
  printf '%s' "$req" | base64 -d | timeout "$t" docker run "${flags[@]}" "$TAG" python -I /opt/openvef/harness.py \
    >"$out" 2>"$err"
  rc=$?
  set -e
  if [ "$rc" -eq 124 ]; then
    docker kill "$name" >/dev/null 2>&1 || true
    docker rm -f "$name" >/dev/null 2>&1 || true
    echo "OPENVEF_SANDBOX_REPLY TIMEOUT"
  else
    echo "OPENVEF_SANDBOX_REPLY DONE $rc $(b64 <"$out") $(tail -c 2000 "$err" | b64)"
  fi
  rm -f "$out" "$err"
}

cleanup() { docker rm -f "$RNAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

coproc RUNNER { docker run "${RUNNER_FLAGS[@]}" "${ENV_ARGS[@]}" "$TAG" \
  python -I /opt/openvef-repo/runner/run_f18.py /baseline /evidence "$RUN_CLASS"; }
RUNNER_IN=${RUNNER[1]}
RPID=$RUNNER_PID
while IFS= read -r line <&"${RUNNER[0]}"; do
  case "$line" in
    "OPENVEF_SANDBOX_REQUEST "*)
      read -r _ t req <<<"$line"
      [[ "$t" =~ ^[0-9]+(\.[0-9]+)?$ ]] || { echo "bad timeout from runner" >&2; exit 2; }
      run_artifact "$t" "$req" >&"$RUNNER_IN"
      ;;
    *) printf '%s\n' "$line" ;;
  esac
done
set +e
wait "$RPID"
status=$?
set -e
# Evidence must not stay writable by other local users (files here have been created 646).
chmod -R go-w "$OUT"
exit "$status"
