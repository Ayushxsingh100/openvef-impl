# OpenVEF F18 image (owner decisions D-002, D-002a, D-003; docs/sandbox.md).
# One image serves both roles: the F18 runner (all evaluation stages, D-002a) and each
# artifact-execution container (D-002). Its CPython 3.11.18 is the pinned interpreter for
# all F18 evidence (D-002a).
# Base pinned by digest: python:3.11.18-slim, linux/amd64 manifest-list digest resolved
# with `docker pull` on 23 Nov 2026 (Debian 13.7 "trixie").

# --- Stage 1: build Yosys and fetch MCY (D-004) ---------------------------------------
# Build tools come from snapshot.debian.org at 20261104T212339Z, the snapshot the base
# image itself was built from (recorded in its /etc/apt/sources.list.d/debian.sources),
# so they match the runtime libraries in the final image. Nothing from this stage
# reaches the final image except the installed Yosys/MCY tree.
FROM python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535 AS eda-build
ARG DEBIAN_SNAPSHOT=20261104T212339Z
# Yosys v0.71 (latest stable release, 12 Nov 2026): release tarball yosys.tar.gz
# (includes ABC and the other bundled libraries), SHA-256 as published by GitHub. Tag
# v0.71 -> commit b4c586fd37d0ec61bb38fc1a85fd6a2fde48fcd1; the tarball's .gitcommit is
# CI merge commit 5628c13240f670b97aaaca3d47940c4afb8ff572, which GitHub's compare shows
# has no file differences from the tag commit.
ARG YOSYS_VERSION=0.71
ARG YOSYS_URL=https://github.com/YosysHQ/yosys/releases/download/v0.71/yosys.tar.gz
ARG YOSYS_SHA256=2ec7c2ee63bb9b4065d6d5fff2786a1455e834f90ede8eb1d47791153ebef2a5
# MCY tag v0.71 (tag object b062a44a...): no release asset, so pinned by its commit
# (a content hash).
ARG MCY_COMMIT=5a2cad0cbefceb7f23051c08348bd23128fd1046
RUN set -eux; \
    printf 'Types: deb\nURIs: https://snapshot.debian.org/archive/debian/%s\nSuites: trixie trixie-updates\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.pgp\nCheck-Valid-Until: no\n\nTypes: deb\nURIs: https://snapshot.debian.org/archive/debian-security/%s\nSuites: trixie-security\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.pgp\nCheck-Valid-Until: no\n' \
        "${DEBIAN_SNAPSHOT}" "${DEBIAN_SNAPSHOT}" > /etc/apt/sources.list.d/debian.sources; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential bison flex gawk pkg-config \
        libreadline-dev libffi-dev zlib1g-dev git ca-certificates cmake; \
    cd /tmp; \
    python -I -c 'import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])' "${YOSYS_URL}" yosys.tar.gz; \
    echo "${YOSYS_SHA256}  yosys.tar.gz" | sha256sum -c -; \
    mkdir yosys; tar xzf yosys.tar.gz -C yosys; cd yosys; \
    test "$(cat .gitcommit)" = "5628c13240f670b97aaaca3d47940c4afb8ff572"; \
    cmake --preset release -DYOSYS_WITHOUT_TCL=ON -DYOSYS_WITHOUT_EDITLINE=ON -DBUILD_SHARED_LIBS=OFF \
        -DYOSYS_ENABLE_UNIT_TESTS=OFF -DYOSYS_WITH_PYTHON=OFF; \
    cmake --build build-rel --config Release --parallel "$(nproc)"; \
    cmake --install build-rel --prefix /opt/eda; \
    /opt/eda/bin/yosys -V | grep -F "Yosys ${YOSYS_VERSION}"; \
    cd /tmp; git clone --quiet https://github.com/YosysHQ/mcy.git mcy; \
    git -C mcy checkout --quiet "${MCY_COMMIT}"; \
    test "$(git -C mcy rev-parse HEAD)" = "${MCY_COMMIT}"; \
    install -D -m 0755 mcy/mcy.py /opt/eda/bin/mcy; \
    mkdir -p /opt/eda/share/mcy; cp -r mcy/scripts /opt/eda/share/mcy/scripts; \
    printf '%s\n' "${MCY_COMMIT}" > /opt/eda/share/mcy/COMMIT; \
    printf 'yosys %s %s\nmcy %s\ndebian_snapshot %s\n' "${YOSYS_VERSION}" "${YOSYS_SHA256}" "${MCY_COMMIT}" "${DEBIAN_SNAPSHOT}" > /opt/eda/share/EDA_PINS

# --- Stage 2: the F18 image -------------------------------------------------------------
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

# D-004: Yosys v0.71 and MCY v0.71 (command-line tool and scripts only; mcy-dash needs
# Flask and the GUI needs Qt, neither is installed). Built without Tcl, pyosys or plugins,
# so they need no shared library the base image lacks. MCY's mcy.py imports `click`,
# which comes from requirements.lock below (owner decision D-004a). The null-netlist
# export uses Yosys only.
COPY --from=eda-build /opt/eda/ /usr/local/

# Exactly the pinned lock file, every artifact hash-checked (CLAUDE.md hard rule 3);
# includes cocotb (D-003) and click (D-004a). pip settings are scoped to this step so they
# do not reach the runtime environment.
# Build-network workaround, also scoped to this step: the base image's OpenSSL 3.5 offers
# a post-quantum key share, and the resulting large TLS ClientHello is dropped on this
# Codespace's path to PyPI (handshake timeout). Limiting the groups to X25519/P-256 for
# the download avoids that. It changes no installed byte: every file is hash-checked.
COPY requirements.lock /tmp/requirements.lock
RUN printf 'openssl_conf = i\n[i]\nssl_conf = s\n[s]\nsystem_default = d\n[d]\nGroups = X25519:P-256\n' > /tmp/ossl.cnf \
 && OPENSSL_CONF=/tmp/ossl.cnf PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 \
    pip install --require-hashes --no-deps -r /tmp/requirements.lock \
 && rm /tmp/requirements.lock /tmp/ossl.cnf

# Fixed non-root identity; the launchers also pass --user explicitly.
RUN groupadd --gid 10001 sandbox && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin sandbox
USER 10001:10001
WORKDIR /tmp
