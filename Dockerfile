# Reproducible build image: pandoc (with built-in citeproc) + XeLaTeX + Node for citeproc-js.
# Pandoc version is pinned by the image tag; bump deliberately.
FROM pandoc/latex:3.11.0.0-debian
RUN apt-get update \
 && apt-get install -y --no-install-recommends make curl ca-certificates nodejs npm diffutils \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
ENTRYPOINT []
CMD ["make", "all"]
