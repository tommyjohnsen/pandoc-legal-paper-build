# PROVENANCE: modified-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
# Linux amd64; immutable Python image and frozen Debian package universe.
FROM --platform=linux/amd64 python:3.12.3-slim-bookworm@sha256:fd3817f3a855f6c2ada16ac9468e5ee93e361005bd226fd5a5ee1a504e038c84
RUN rm -f /etc/apt/sources.list.d/debian.sources \
 && printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20240501T000000Z bookworm main\n' > /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends make ca-certificates fontconfig libgraphite2-3 libssl3 libstdc++6 diffutils dpkg \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
COPY . /work
RUN python3 tools/setup.py \
 && mkdir -p /work/build \
 && chmod -R a+rwX /work/.tools /work/node_modules /work/build
ENTRYPOINT ["bash", "-c", "source /work/tools/env.sh; exec \"$@\"", "--"]
CMD ["make", "demo"]
