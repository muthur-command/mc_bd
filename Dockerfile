ARG SERVER_TYPE=api
ARG BUILD_FROM=ghcr.io/muthur-command/base-python:3.14-alpine3.23-2026.06.2

# hadolint ignore=DL3006
FROM ${BUILD_FROM} AS builder

COPY . /mc
WORKDIR /mc

ARG UV_HTTP_TIMEOUT=180
ARG UV_HTTP_RETRIES=5

# Install deps into the same Alpine Python that runs the container (not Debian).
# hadolint ignore=DL3018
RUN apk add --no-cache \
        build-base \
        libffi-dev \
        linux-headers \
        musl-dev \
    && pip3 install --no-cache-dir uv==0.10.9

ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_HTTP_TIMEOUT=${UV_HTTP_TIMEOUT} \
    UV_HTTP_RETRIES=${UV_HTTP_RETRIES} \
    UV_SYSTEM_PYTHON=true \
    UV_PYTHON=/usr/local/bin/python3

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-default-groups --group server --no-install-project --python /usr/local/bin/python3

# Runtime base image is passed as BUILD_FROM (pinned in builder.yml).
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

ARG SERVER_TYPE=api

LABEL \
    io.mcos.type="mc_bd" \
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
