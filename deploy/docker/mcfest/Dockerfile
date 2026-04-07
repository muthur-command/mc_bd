FROM alpine:3.20
WORKDIR /workspace
RUN apk add --no-cache bash
COPY deploy/docker/mcfest/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
