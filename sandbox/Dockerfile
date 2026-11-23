# OpenVEF F18 image (owner decisions D-002, D-002a, D-003; docs/sandbox.md).
# One image serves both roles: the F18 runner (all evaluation stages, D-002a) and each
# artifact-execution container (D-002). Its CPython 3.11.18 is the pinned interpreter for
# all F18 evidence (D-002a).
# Base pinned by digest: python:3.11.18-slim, linux/amd64 manifest-list digest resolved
# with `docker pull` on 23 Nov 2026 (Debian 13.7 "trixie").
FROM python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# D-003: Icarus Verilog, latest stable in this image's package manager, exact version and
# .deb SHA-256 pinned. The .deb is fetched from snapshot.debian.org (archive timestamp
# 20240313T032420Z, the first snapshot containing this file), so the build does not
# depend on the live Debian archive still carrying this version. The SHA-256 is checked
# before installation. Its run-time dependencies (libbz2-1.0, libc6, libgcc-s1,
# libreadline8t64, libstdc++6, zlib1g) are already in the base image; dpkg fails the
# build if any is missing.
ARG IVERILOG_VERSION=12.0-2+b1
ARG IVERILOG_DEB_URL=https://snapshot.debian.org/archive/debian/20240313T032420Z/pool/main/i/iverilog/iverilog_12.0-2%2Bb1_amd64.deb
ARG IVERILOG_DEB_SHA256=febe027d2d3f5a7e570844d55758339ab5490acc09f404f214a8719d89d07056
RUN set -eux; cd /tmp; \
    python -I -c 'import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])' \
        "${IVERILOG_DEB_URL}" iverilog.deb; \
    echo "${IVERILOG_DEB_SHA256}  iverilog.deb" | sha256sum -c -; \
    dpkg -i iverilog.deb; \
    test "$(dpkg-query -W -f='${Version}' iverilog)" = "${IVERILOG_VERSION}"; \
    rm -f /tmp/iverilog.deb

# Exactly the pinned lock file, every artifact hash-checked (CLAUDE.md hard rule 3);
# includes cocotb (D-003). pip settings are scoped to this step so they do not reach the
# runtime environment.
COPY requirements.lock /tmp/requirements.lock
RUN PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 \
    pip install --require-hashes --no-deps -r /tmp/requirements.lock \
 && rm /tmp/requirements.lock

# Fixed non-root identity; the launchers also pass --user explicitly.
RUN groupadd --gid 10001 sandbox && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin sandbox
USER 10001:10001
WORKDIR /tmp
