# NexVest - Deploy con Docker Compose

Guia paso a paso para correr todo el stack en contenedores sobre un VPS que
ya tienes (Hetzner u otro). Tres servicios:

| Servicio | Imagen | Funcion |
|---|---|---|
| `api` | `nexvest-api` (build local) | FastAPI + uvicorn |
| `etl-cron` | `nexvest-api` (misma imagen, comando = supercronic) | ETL incremental Lun-Vie 22:00 UTC |
| `web` | `nexvest-web` (build local, base `caddy:2-alpine`) | SPA + reverse proxy + HTTPS Let's Encrypt |

Solo `web` expone puertos al exterior (80 y 443). `api` y `etl-cron`
hablan por la red interna `nexvest`.

---

## 1. Prerrequisitos en el VPS

Asumo Ubuntu 22.04 / 24.04 (cualquier distro con Docker sirve).

```bash
ssh root@<IP-DEL-SERVER>

# Docker + plugin compose (instalador oficial)
curl -fsSL https://get.docker.com | sh

# Verificar
docker --version
docker compose version

# Firewall: solo 22, 80, 443
ufw allow OpenSSH
ufw allow http
ufw allow https
ufw --force enable
```

---

## 2. Clonar el repositorio

```bash
mkdir -p /opt
cd /opt
git clone https://github.com/<owner>/NexVest.git nexvest
cd /opt/nexvest
```

Estructura relevante:

```
/opt/nexvest/
├── docker-compose.yml
├── .env.example                          # variables del stack
├── Nexvest-Back-FASTAPI/
│   ├── Dockerfile
│   ├── .env.example                      # variables del backend
│   └── ...
├── Nexvest-Front/
│   ├── Dockerfile
│   └── ...
└── deploy/
    ├── Caddyfile
    └── crontab
```

---

## 3. (Recomendado) Apuntar un dominio al server

Caddy emite HTTPS automatico via Let's Encrypt, pero necesita que el dominio
resuelva al VPS por DNS.

Opciones:

- **Dominio propio:** crea un registro **A** `nexvest.tudominio.com -> <IP>`.
- **Sin dominio:** usa `nip.io`. Si tu IP es `5.75.123.45`, ya existe
  `5.75.123.45.nip.io` apuntando a tu IP. Caddy emite cert valido.
- **Solo HTTP (debug):** poner `DOMAIN=:80` en el `.env`. Sin HTTPS pero util
  para una prueba rapida con curl.

---

## 4. Configurar las dos variables de entorno

### 4.a `/opt/nexvest/.env`

```bash
cp /opt/nexvest/.env.example /opt/nexvest/.env
nano /opt/nexvest/.env
```

Poner el dominio real:

```env
DOMAIN=nexvest.tudominio.com
```

### 4.b `/opt/nexvest/Nexvest-Back-FASTAPI/.env`

```bash
cp /opt/nexvest/Nexvest-Back-FASTAPI/.env.example \
   /opt/nexvest/Nexvest-Back-FASTAPI/.env
nano /opt/nexvest/Nexvest-Back-FASTAPI/.env
```

Pegar la URI de Mongo Atlas (la misma que usas en local):

```env
MONGO_URI=mongodb+srv://USUARIO:PASSWORD@CLUSTER.mongodb.net/?appName=NexVest
MONGO_DB_NAME=nexvest
```

Asegurar permisos:

```bash
chmod 600 /opt/nexvest/Nexvest-Back-FASTAPI/.env
chmod 600 /opt/nexvest/.env
```

### 4.c Whitelist en MongoDB Atlas

En <https://cloud.mongodb.com> -> Security -> **Network Access** -> Add IP.
Pega la IP del VPS. (`0.0.0.0/0` funciona pero abre tu cluster a internet;
no recomendado.)

---

## 5. Build y arranque

Desde `/opt/nexvest`:

```bash
docker compose build
docker compose up -d
```

El primer build tarda 3-5 minutos (imagen del backend + imagen del frontend).

Verificar:

```bash
docker compose ps
# api        Up (healthy)
# etl-cron   Up
# web        Up    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

## 6. Verificacion end-to-end

### 6.a Web responde

```bash
curl -I https://<tu-dominio>
# 200 OK, content-type: text/html
```

Abrir en navegador: debe verse el Dashboard de NexVest cargando datos
reales.

### 6.b API responde

```bash
curl https://<tu-dominio>/api/
# {"status":"ok","message":"NexVest API corriendo"}

curl https://<tu-dominio>/api/analisis/mnemonicos
# {"mnemonicos":["CELSIA","CEMARGOS",...]}
```

### 6.c El cron del ETL esta agendado

```bash
docker compose logs etl-cron --tail 20
```

Deberias ver al arranque algo como:

```
level=info msg="read crontab: /etc/cron/crontab"
level=info msg="job will run next at ... (Mon, ... 22:00 UTC)"
```

### 6.d Forzar una ejecucion inmediata del ETL

```bash
docker compose exec api python -m etl.scheduled
```

Salida tipica si todo esta al dia:

```
[2026-05-14T22:00:01.234Z] scheduled.py iniciado
Rango pendiente: 2026-05-07 -> 2026-05-14
[BVC] descarga lista en 6.0s
[Yahoo] descarga lista en 15.1s
{ ..., "upserted": 0, "modified": 0 }
OK en 24.44s
```

---

## 7. Operacion diaria

### Logs en vivo

```bash
# Todos los contenedores
docker compose logs -f

# Solo la API
docker compose logs -f api

# Solo el cron
docker compose logs -f etl-cron

# Solo Caddy
docker compose logs -f web
```

### Forzar un ETL manual

```bash
docker compose exec api python -m etl.scheduled
```

### Reiniciar un servicio

```bash
docker compose restart api
docker compose restart web
```

### Actualizar el codigo

```bash
cd /opt/nexvest
git pull --ff-only
docker compose build
docker compose up -d
```

Compose detecta cambios en las imagenes y reemplaza los contenedores. La SPA
estatica se actualiza al rebuild del servicio `web`.

### Hacer rollback

```bash
git checkout <commit-anterior>
docker compose build && docker compose up -d
```

---

## 8. Eliminar todo al final del semestre

```bash
# Detener y borrar contenedores + red + volumenes locales
cd /opt/nexvest
docker compose down -v

# Borrar las imagenes
docker rmi nexvest-api:latest nexvest-web:latest

# Borrar el repo
rm -rf /opt/nexvest

# (Opcional) Desinstalar Docker:  apt purge docker-ce docker-ce-cli
```

La data persiste en MongoDB Atlas; el VPS queda limpio. Si vas a destruir el
VPS, simplemente eliminalo desde la consola de Hetzner.

---

## 9. Resolucion de problemas

### `api` no esta healthy

```bash
docker compose logs api --tail 100
```

Causas tipicas:

- `MONGO_URI is not set`: revisar que `Nexvest-Back-FASTAPI/.env` exista con
  la URI correcta.
- Connection timeout a Mongo: la IP del VPS no esta whitelisted en Atlas
  (paso 4.c).

### Caddy no emite certificado HTTPS

```bash
docker compose logs web --tail 100 | grep -iE "error|certificate"
```

Causas tipicas:

- El dominio en `DOMAIN` no resuelve al VPS. Verifica con `dig <DOMAIN>`.
- Puerto 80 bloqueado: el ACME challenge necesita el 80 abierto. Revisa
  `ufw status` y la red de Hetzner.
- Reach limit: si reiniciaste muchas veces, Let's Encrypt te bloquea por una
  hora. Usar `tls internal` o esperar.

### El cron no esta corriendo

```bash
docker compose exec etl-cron supercronic -test /etc/cron/crontab
```

Si la sintaxis es invalida, supercronic lo dice ahi.

### Disco lleno

```bash
docker system prune -af --volumes
```

Limpia imagenes antiguas y volumenes sin usar. **Cuidado**: si tienes
volumenes con datos importantes (no nuestro caso, todo esta en Atlas), revisa
antes.

---

## 10. Notas sobre los algoritmos exigidos por la rubrica

- Todos los algoritmos manuales (similitud, patrones, volatilidad, sorting,
  limpieza) viajan en la imagen `nexvest-api`. El contenedor `etl-cron`
  reutiliza esa misma imagen para garantizar que la version del codigo y la
  de las dependencias son identicas a las de la API.
- El PDF tecnico se genera en el backend (matplotlib + reportlab). Tomar entre
  5 y 30 segundos para portafolio completo no es problema porque NO estamos en
  serverless (no hay timeout).
- El cron solo dispara `python -m etl.scheduled`, que ya garantiza
  idempotencia (upsert por fecha, lookback de 7 dias).
