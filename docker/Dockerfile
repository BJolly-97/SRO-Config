# syntax=docker/dockerfile:1
#
# Headless image for the command-line / batch workflow (dict, config). The
# interactive `vis` viewer and the desktop GUI need a display and are not usable
# from a container.
#
#   docker run --rm -v "$PWD:/data" sro-config config --dict-dir . --sublattice 0 --rmc6f run.rmc6f

# ---- build: produce the wheel (version comes from git via setuptools-scm) ----
FROM python:3.14-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .
RUN pip install --no-cache-dir build \
    && python -m build --wheel --outdir /wheels

# ---- runtime: slim image with just the package ----
FROM python:3.14-slim AS runtime

LABEL org.opencontainers.image.title="sro-config" \
      org.opencontainers.image.description="Clapp-style configurational analysis of RMCProfile large-box atomic models" \
      org.opencontainers.image.source="https://github.com/BJolly-97/SRO-Config" \
      org.opencontainers.image.licenses="MIT"

ENV MPLBACKEND=Agg \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=build /wheels/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl

RUN useradd --create-home --uid 1000 analyst \
    && mkdir -p /data \
    && chown analyst:analyst /data
USER analyst
WORKDIR /data

ENTRYPOINT ["sro-config"]
CMD ["--help"]
