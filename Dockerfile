# Select the image to build based on SERVER_TYPE, defaulting to mc_server, or docker-compose build args
ARG SERVER_TYPE=mc_server

# === Python environment from uv ===
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

# Used for build Python packages (DL3008: pinning every .deb revision is brittle for this image)
# hadolint ignore=DL3008
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /mc

WORKDIR /mc

# Configure uv environment
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

# Install dependencies with cache
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-default-groups --group server --no-install-project

# === Runtime base server image ===
FROM python:3.10-slim-bookworm AS base_server

# hadolint ignore=DL3008
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates supervisor \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH" \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /mc /mc

COPY --from=builder /usr/local /usr/local

COPY deploy/backend/supervisor/supervisord.conf /etc/supervisor/supervisord.conf

# === FastAPI server image ===
FROM base_server AS mc_server

COPY deploy/backend/supervisor/mc_server.conf /etc/supervisor/conf.d/

RUN mkdir -p /var/log/mc

EXPOSE 8001

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

# === Celery Worker image ===
FROM base_server AS mc_celery_worker

COPY deploy/backend/supervisor/mc_celery_worker.conf /etc/supervisor/conf.d/

RUN mkdir -p /var/log/mc

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

# === Celery Beat image ===
FROM base_server AS mc_celery_beat

COPY deploy/backend/supervisor/mc_celery_beat.conf /etc/supervisor/conf.d/

RUN mkdir -p /var/log/mc

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

# === Celery Flower image ===
FROM base_server AS mc_celery_flower

COPY deploy/backend/supervisor/mc_celery_flower.conf /etc/supervisor/conf.d/

RUN mkdir -p /var/log/mc

EXPOSE 8555

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

# Build image (${SERVER_TYPE} is a local stage name, e.g. mc_server — not an untagged registry image)
# hadolint ignore=DL3006
FROM ${SERVER_TYPE}
