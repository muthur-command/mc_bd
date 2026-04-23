ARG SERVER_TYPE=api
ARG BUILD_FROM=python:3.12-alpine

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Used for build Python packages (DL3008: pinning every .deb revision is brittle for this image)
# hadolint ignore=DL3008
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /mc
WORKDIR /mc

ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-default-groups --group server --no-install-project \
    && uv pip install gunicorn

FROM ${BUILD_FROM}

ARG SERVER_TYPE=api

LABEL \
    io.mcio.type="mc_bd" \
    org.opencontainers.image.authors="Muthur Command Authors" \
    org.opencontainers.image.description="Muthur Command backend service on Python" \
    org.opencontainers.image.licenses="GPL-3.0-or-later" \
    org.opencontainers.image.title="Muthur Command Backend"

ENV \
    S6_SERVICES_GRACETIME=240000 \
    UV_SYSTEM_PYTHON=true \
    UV_NO_CACHE=true \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ROLE=${SERVER_TYPE}

COPY rootfs /
COPY --from=builder /mc /mc
COPY --from=builder /usr/local /usr/local

RUN chmod +x /init \
    && find /etc/cont-init.d -type f -exec chmod +x {} \; \
    && find /etc/services.d -name run -type f -exec chmod +x {} \;

WORKDIR /mc/backend

EXPOSE 8001 8555

ENTRYPOINT ["/init"]
