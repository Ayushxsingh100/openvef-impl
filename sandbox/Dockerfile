# OpenVEF F18 artifact-execution image (owner decision D-002; docs/sandbox.md).
# Base pinned by digest: python:3.11.18-slim, linux/amd64 manifest-list digest resolved
# with `docker pull` on 23 Nov 2026.
FROM python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Exactly the pinned lock file, every artifact hash-checked (CLAUDE.md hard rule 3).
# pip settings are scoped to this step so they do not reach the runtime environment.
COPY requirements.lock /tmp/requirements.lock
RUN PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 \
    pip install --require-hashes --no-deps -r /tmp/requirements.lock \
 && rm /tmp/requirements.lock

# Fixed non-root identity; the launcher also passes --user explicitly.
RUN groupadd --gid 10001 sandbox && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin sandbox
USER 10001:10001
WORKDIR /tmp
