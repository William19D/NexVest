# NexVest backend - imagen multi-uso
# -----------------------------------
# La misma imagen se usa para dos servicios en docker-compose:
#   - api      : ejecuta uvicorn (default CMD).
#   - etl-cron : ejecuta supercronic con la planificacion del ETL.

FROM python:3.11-slim-bookworm

# Variables de entorno utiles para Python en contenedor.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema:
#   - curl: para bajar supercronic.
#   - ca-certificates: TLS para conexiones a Mongo Atlas y APIs.
#   - tini: PID 1 que reenvia senales correctamente.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

# Supercronic = "cron friendly con contenedores".
# Lee un crontab y ejecuta los comandos como proceso hijo.
ARG SUPERCRONIC_VERSION=v0.2.30
ARG SUPERCRONIC_SHA1SUM=9aeb41e00cc7b71d30d33c57a2333f2c2581a201
RUN curl -fsSLO \
        "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
    && echo "${SUPERCRONIC_SHA1SUM}  supercronic-linux-amd64" | sha1sum -c - \
    && chmod +x supercronic-linux-amd64 \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic

# Usuario no-root.
RUN groupadd --system nexvest \
    && useradd --system --gid nexvest --create-home --home-dir /home/nexvest nexvest

WORKDIR /app

# Instalar dependencias antes de copiar el codigo para aprovechar la cache.
COPY --chown=nexvest:nexvest requirements.txt ./
RUN pip install -r requirements.txt

# Codigo de la aplicacion.
COPY --chown=nexvest:nexvest . ./

USER nexvest

EXPOSE 8000

# tini gestiona senales para PID 1; el comando real lo decide compose.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--proxy-headers", \
     "--forwarded-allow-ips=*"]
