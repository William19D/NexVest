#!/usr/bin/env bash
#
# NexVest - bootstrap completo en VPS Hetzner (Ubuntu 24.04 LTS recomendado).
# -------------------------------------------------------------------------
# Ejecutar como root la primera vez:
#
#     curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/deploy/setup.sh | bash
#
# o despues de clonar el repo manualmente:
#
#     sudo bash deploy/setup.sh
#
# Variables que se pueden sobreescribir antes de ejecutar:
#     REPO_URL    : URL del repositorio git (default: ver abajo).
#     NEXVEST_DIR : ruta de instalacion           (default: /opt/nexvest).
#     APP_USER    : usuario de sistema sin shell  (default: nexvest).
#     NODE_MAJOR  : version mayor de Node.js      (default: 20).

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/CHANGE_ME/NexVest.git}"
NEXVEST_DIR="${NEXVEST_DIR:-/opt/nexvest}"
APP_USER="${APP_USER:-nexvest}"
NODE_MAJOR="${NODE_MAJOR:-20}"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

if [[ $EUID -ne 0 ]]; then
    echo "Este script necesita root. Ejecuta con sudo." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
log "1/8  Actualizando paquetes del sistema"
# ---------------------------------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# ---------------------------------------------------------------------------
log "2/8  Instalando dependencias del sistema"
# ---------------------------------------------------------------------------
apt-get install -y \
    git curl ca-certificates gnupg lsb-release \
    python3 python3-venv python3-pip \
    build-essential ufw fail2ban

# Node.js via NodeSource.
if ! command -v node >/dev/null 2>&1; then
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
    apt-get install -y nodejs
fi

# Caddy v2.
if ! command -v caddy >/dev/null 2>&1; then
    apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
        | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
        | tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
    apt-get update -y
    apt-get install -y caddy
fi

# ---------------------------------------------------------------------------
log "3/8  Creando usuario de sistema '$APP_USER'"
# ---------------------------------------------------------------------------
if ! id "$APP_USER" >/dev/null 2>&1; then
    useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
fi
mkdir -p "$NEXVEST_DIR"
chown -R "$APP_USER":"$APP_USER" "$NEXVEST_DIR"

# ---------------------------------------------------------------------------
log "4/8  Clonando/actualizando repositorio en $NEXVEST_DIR"
# ---------------------------------------------------------------------------
if [[ -d "$NEXVEST_DIR/.git" ]]; then
    sudo -u "$APP_USER" git -C "$NEXVEST_DIR" pull --ff-only
else
    sudo -u "$APP_USER" git clone "$REPO_URL" "$NEXVEST_DIR"
fi

# ---------------------------------------------------------------------------
log "5/8  Backend: virtualenv + dependencias"
# ---------------------------------------------------------------------------
sudo -u "$APP_USER" python3 -m venv "$NEXVEST_DIR/.venv"
sudo -u "$APP_USER" "$NEXVEST_DIR/.venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$NEXVEST_DIR/.venv/bin/pip" install \
    -r "$NEXVEST_DIR/Nexvest-Back-FASTAPI/requirements.txt"

# .env (placeholder si no existe).
if [[ ! -f "$NEXVEST_DIR/Nexvest-Back-FASTAPI/.env" ]]; then
    cat <<EOF | sudo -u "$APP_USER" tee "$NEXVEST_DIR/Nexvest-Back-FASTAPI/.env" >/dev/null
# Editar antes de arrancar el servicio:
MONGO_URI=mongodb+srv://USUARIO:PASSWORD@CLUSTER/?appName=NexVest
MONGO_DB_NAME=nexvest
EOF
    echo "    !! Edita $NEXVEST_DIR/Nexvest-Back-FASTAPI/.env con tu MONGO_URI real."
fi
chmod 600 "$NEXVEST_DIR/Nexvest-Back-FASTAPI/.env"

# ---------------------------------------------------------------------------
log "6/8  Frontend: build estatico"
# ---------------------------------------------------------------------------
# VITE_API_URL apunta al mismo dominio bajo /api (Caddy lo reenvia).
sudo -u "$APP_USER" bash -c "cd $NEXVEST_DIR/Nexvest-Front && \
    rm -rf node_modules && \
    npm install && \
    VITE_API_URL=/api npm run build"
mkdir -p /var/www/nexvest
rm -rf /var/www/nexvest/*
cp -r "$NEXVEST_DIR/Nexvest-Front/dist/"* /var/www/nexvest/
chown -R caddy:caddy /var/www/nexvest

# ---------------------------------------------------------------------------
log "7/8  systemd: instalando units"
# ---------------------------------------------------------------------------
install -m 0644 "$NEXVEST_DIR/deploy/systemd/nexvest-api.service" /etc/systemd/system/
install -m 0644 "$NEXVEST_DIR/deploy/systemd/nexvest-etl.service" /etc/systemd/system/
install -m 0644 "$NEXVEST_DIR/deploy/systemd/nexvest-etl.timer"   /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now nexvest-api.service
systemctl enable --now nexvest-etl.timer

# ---------------------------------------------------------------------------
log "8/8  Caddy: copiando Caddyfile"
# ---------------------------------------------------------------------------
echo "    !! Edita /etc/caddy/Caddyfile y reemplaza TU_DOMINIO antes de recargar."
install -m 0644 "$NEXVEST_DIR/deploy/Caddyfile" /etc/caddy/Caddyfile.nexvest
echo "    Plantilla copiada a /etc/caddy/Caddyfile.nexvest"
echo "    Para activar:  sudo mv /etc/caddy/Caddyfile.nexvest /etc/caddy/Caddyfile && sudo systemctl reload caddy"

# Firewall.
ufw allow OpenSSH || true
ufw allow http    || true
ufw allow https   || true
ufw --force enable

cat <<EOF

==============================================================
  NexVest instalado.

  Estado:
    systemctl status nexvest-api.service
    systemctl status nexvest-etl.timer
    systemctl list-timers nexvest-etl.timer

  Logs en vivo:
    journalctl -u nexvest-api.service -f
    journalctl -u nexvest-etl.service -f

  Forzar un ETL ahora:
    sudo systemctl start nexvest-etl.service

  Pasos pendientes:
    1) Editar /opt/nexvest/Nexvest-Back-FASTAPI/.env con MONGO_URI real.
    2) Editar /etc/caddy/Caddyfile.nexvest cambiando TU_DOMINIO.
    3) sudo mv /etc/caddy/Caddyfile.nexvest /etc/caddy/Caddyfile
    4) sudo systemctl reload caddy

==============================================================
EOF
