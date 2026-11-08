# syntax=docker/dockerfile:1.7
# Production builds use the default tag; core-qa passes a digest-pinned BASE_IMAGE (image-lock.json game_base).
ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE} AS build
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILD_JOBS=3
ENV VCPKG_ROOT=/opt/vcpkg VCPKG_MAX_CONCURRENCY=3 VCPKG_BINARY_SOURCES=clear
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake ninja-build git curl ca-certificates zip unzip tar pkg-config autoconf automake libtool python3 perl bison flex linux-libc-dev && rm -rf /var/lib/apt/lists/*
COPY vcpkg.json /manifest/vcpkg.json
RUN git init /opt/vcpkg && cd /opt/vcpkg && git remote add origin https://github.com/microsoft/vcpkg.git && git fetch --depth=1 origin 66c0373dc7fca549e5803087b9487edfe3aca0a1 && git checkout FETCH_HEAD && ./bootstrap-vcpkg.sh -disableMetrics
RUN --mount=type=cache,target=/opt/vcpkg/downloads --mount=type=cache,target=/root/.cache/vcpkg /opt/vcpkg/vcpkg install --x-manifest-root=/manifest --x-install-root=/opt/installed --triplet=x64-linux
WORKDIR /source
ARG SOURCE_REVISION=unknown
# Keep Git metadata out of image layers, while both native targets see the same
# complete, read-only source tree and independently supplied local Git context.
RUN --mount=type=bind,target=/source \
    --mount=type=bind,from=gitmeta,target=/source-git \
    export GIT_DIR=/source-git GIT_WORK_TREE=/source && \
    git config --global --add safe.directory /source && \
    python3 deployment/wsl/verify-build-source.py --source /source --revision "$SOURCE_REVISION" && \
    cmake -S . -B /build -G Ninja -DCMAKE_TOOLCHAIN_FILE=/opt/vcpkg/scripts/buildsystems/vcpkg.cmake -DVCPKG_INSTALLED_DIR=/opt/installed -DVCPKG_MANIFEST_INSTALL=OFF -DCMAKE_BUILD_TYPE=Release -DTOGGLE_BIN_FOLDER=ON -DCANARY_BUILD_TESTS=OFF -DOPTIONS_ENABLE_IPO=OFF -DOPTIONS_ENABLE_CCACHE=OFF -DOPTIONS_ENABLE_SCCACHE=OFF -DSPEED_UP_BUILD_UNITY=OFF && \
    cmake --build /build --target canary bot_engine -j ${BUILD_JOBS}

FROM ${BASE_IMAGE} AS game
ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.revision=$SOURCE_REVISION
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libmariadb3 libluajit-5.1-2 libssl3t64 zlib1g libcurl4t64 libgomp1 curl python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /canary
COPY --from=build /build/bin/canary /build/bin/libbot_engine.so ./
COPY data ./data
COPY data-canary ./data-canary
COPY data-otservbr-global ./data-otservbr-global
COPY config.lua.dist key.pem schema.sql ./
COPY deployment/wsl/game-entrypoint.py /usr/local/bin/game-entrypoint.py
ENTRYPOINT ["python3", "/usr/local/bin/game-entrypoint.py"]

FROM python:3.12-slim AS brain
ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.revision=$SOURCE_REVISION
WORKDIR /app
COPY deployment/brain /app
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps .
ENTRYPOINT ["canary-brain", "serve", "--config", "/etc/canary-brain/worker.json"]
