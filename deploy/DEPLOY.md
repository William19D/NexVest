# Deploy de NexVest en Hetzner Cloud

Guia paso a paso para correr NexVest en un VPS Hetzner. Cubre R5 del PDF
("el proyecto debera estar desplegado como una aplicacion web funcional").

**Costo aproximado:** Hetzner CX22 (2 vCPU, 4 GB RAM, 40 GB SSD) cuesta
~5 EUR/mes. Se puede destruir cuando termine el semestre.

---

## 0. Resumen de lo que se va a desplegar

```
+-------------------------+
|  Hetzner VPS Ubuntu     |
|  ----------------------- |
|  systemd:                |
|    nexvest-api.service  |  --- Uvicorn en 127.0.0.1:8000
|    nexvest-etl.service  |  --- ETL incremental (oneshot)
|    nexvest-etl.timer    |  --- Lun-Vie 22:00 UTC
|  ----------------------- |
|  Caddy v2 (puerto 80/443)|
|    - HTTPS automatico    |
|    - / -> /var/www/...   |
|    - /api -> :8000       |
+-------------------------+
            |
            v
  MongoDB Atlas (free tier) -- la misma base que usas en local.
```

---

## 1. Crear el VPS en Hetzner

1. Entra a <https://console.hetzner.cloud>, crea un proyecto.
2. Click en **Add server**:
   - **Location**: cualquiera (Helsinki es la mas barata).
   - **Image**: **Ubuntu 24.04**.
   - **Type**: **CX22** (suficiente).
   - **Networking**: IPv4 + IPv6.
   - **SSH Key**: sube tu clave publica (`~/.ssh/id_ed25519.pub`).
   - **Name**: `nexvest`.
3. Espera ~30 segundos a que arranque. Anota la IP publica.

---

## 2. (Recomendado) Apuntar un dominio o subdominio

Caddy solo emite certificado HTTPS si el dominio resuelve al VPS. Opciones:

### 2.a Si tienes un dominio propio

En tu proveedor DNS, crea un registro **A**:

```
nexvest.tudominio.com  ->  <IP del VPS>
```

### 2.b Si no tienes dominio: usar uno gratuito

Puedes usar <https://www.duckdns.org> o <https://www.nip.io>.

Con nip.io no hace falta configurar nada: si tu IP es `5.75.123.45`, el dominio
`5.75.123.45.nip.io` ya apunta a tu IP automaticamente. Caddy emitira un
certificado valido para ese hostname.

> Sin dominio que resuelva por DNS, Caddy fallara la negociacion de Let's
> Encrypt. Como alternativa de prueba, puedes usar el bloque `:80` del
> Caddyfile (sin HTTPS) editandolo manualmente.

---

## 3. Conectarse al VPS

```bash
ssh root@<IP-DEL-VPS>
```

---

## 4. Bootstrap automatico

```bash
# Clonar el repo
git clone https://github.com/<owner>/NexVest.git /opt/nexvest

# Ejecutar el script
sudo bash /opt/nexvest/deploy/setup.sh
```

`setup.sh` hace todo:

- Instala Python, Node, Caddy, git, ufw, fail2ban.
- Crea usuario de sistema `nexvest` sin shell.
- Clona el repo en `/opt/nexvest`.
- Crea virtualenv en `/opt/nexvest/.venv` y instala `requirements.txt`.
- Crea `.env` placeholder en `Nexvest-Back-FASTAPI/.env`.
- Hace build del frontend (`npm run build`) con `VITE_API_URL=/api`.
- Copia el resultado a `/var/www/nexvest`.
- Instala las units systemd y arranca el API + timer ETL.
- Copia el `Caddyfile` plantilla a `/etc/caddy/Caddyfile.nexvest`.
- Habilita firewall (`ufw`) en puertos 22, 80, 443.

Tiempo total: 3-5 minutos.

---

## 5. Configurar credenciales

### 5.a `.env` del backend

```bash
sudo nano /opt/nexvest/Nexvest-Back-FASTAPI/.env
```

Pegar el MONGO_URI real (el mismo que usas en local):

```env
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/?appName=NexVest
MONGO_DB_NAME=nexvest
```

Guardar (Ctrl+O, Enter, Ctrl+X) y reiniciar el servicio:

```bash
sudo systemctl restart nexvest-api.service
```

### 5.b Permitir la IP del VPS en MongoDB Atlas

En <https://cloud.mongodb.com> -> Security -> Network Access -> Add IP Address.
Pega la IP del VPS (o `0.0.0.0/0` si te da pereza, pero esto abre tu cluster a
toda la internet — recomendado: solo la IP).

### 5.c Editar el Caddyfile con tu dominio

```bash
sudo nano /etc/caddy/Caddyfile.nexvest
```

Reemplazar `TU_DOMINIO` por el dominio real (o `5.75.123.45.nip.io`).

Activar:

```bash
sudo mv /etc/caddy/Caddyfile.nexvest /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Caddy emite el certificado Let's Encrypt en ~10 segundos.

---

## 6. Verificacion

### 6.a El sitio responde por HTTPS

```bash
curl -I https://<tu-dominio>
# 200 OK, content-type: text/html
```

Abrir en el navegador: deberias ver el Dashboard de NexVest.

### 6.b La API responde por /api/

```bash
curl https://<tu-dominio>/api/
# {"status":"ok","message":"NexVest API corriendo"}
```

### 6.c El ETL incremental funciona

```bash
# Forzar una corrida ahora
sudo systemctl start nexvest-etl.service

# Ver los logs en vivo
journalctl -u nexvest-etl.service -f
```

Esperar a que termine; deberia salir con `OK en XX.XXs`. Si la base ya esta al
dia, no descarga nada.

### 6.d El timer esta agendado

```bash
systemctl list-timers nexvest-etl.timer
# NEXT                        LEFT      UNIT
# Mon 2026-05-18 22:00:00 UTC  3h 24min  nexvest-etl.timer
```

---

## 7. Cold start (primera carga de datos)

Si tu base Mongo esta vacia, la primera ejecucion del timer descargara los 5
anios para todos los activos. Para forzar eso manualmente:

```bash
sudo -u nexvest /opt/nexvest/.venv/bin/python -m etl.finalInfoScript \
    --user-dir /opt/nexvest/Nexvest-Back-FASTAPI

# Luego subir los JSON a Mongo:
cd /opt/nexvest/Nexvest-Back-FASTAPI
sudo -u nexvest /opt/nexvest/.venv/bin/python -m etl.storage
```

Despues de eso, el timer diario solo descarga lo nuevo (~30 segundos).

---

## 8. Operacion diaria

### Comandos utiles

```bash
# Estado de los servicios
systemctl status nexvest-api.service
systemctl status nexvest-etl.timer
systemctl list-timers --all

# Logs
journalctl -u nexvest-api.service -f       # API en vivo
journalctl -u nexvest-etl.service -n 200   # ultimo run del ETL
journalctl -u caddy --since "1 hour ago"   # Caddy

# Forzar un run inmediato del ETL
sudo systemctl start nexvest-etl.service

# Pausar el ETL temporalmente
sudo systemctl stop nexvest-etl.timer
sudo systemctl disable nexvest-etl.timer
```

### Actualizar el codigo

```bash
cd /opt/nexvest
sudo -u nexvest git pull --ff-only

# Recompilar frontend si cambio:
sudo -u nexvest bash -c "cd Nexvest-Front && npm install && VITE_API_URL=/api npm run build"
sudo cp -r Nexvest-Front/dist/* /var/www/nexvest/

# Reinstalar dependencias backend si cambiaron:
sudo -u nexvest /opt/nexvest/.venv/bin/pip install -r Nexvest-Back-FASTAPI/requirements.txt

# Reiniciar el API
sudo systemctl restart nexvest-api.service
```

---

## 9. Eliminar el VPS al final del semestre

1. Backup opcional: el dataset vive en MongoDB Atlas, **no se pierde** cuando
   borras el VPS.
2. En la consola de Hetzner -> Servers -> nexvest -> **Delete server**.
3. Si usaste un dominio propio, opcionalmente borra el registro DNS.

Costo total de un semestre (~5 meses): ~25 EUR.

---

## 10. Resolucion de problemas

### El servicio no arranca

```bash
journalctl -u nexvest-api.service -n 100
```

Causas tipicas:

- **`MONGO_URI is not set`**: el `.env` no se cargo. Verificar que
  `EnvironmentFile=/opt/nexvest/Nexvest-Back-FASTAPI/.env` exista y tenga
  permisos legibles por el usuario `nexvest`.
- **Connection timed out a MongoDB**: la IP del VPS no esta whitelisted en
  Atlas (paso 5.b).

### Caddy no emite certificado

```bash
journalctl -u caddy --since "10 minutes ago" | grep -i error
```

Causas tipicas:

- El dominio no resuelve al VPS. Verifica con `dig <dominio>`.
- Puerto 80 cerrado: `ufw status` debe mostrar 80/tcp ALLOW.

### El ETL falla con `ImportError`

Verificar el virtualenv:

```bash
sudo -u nexvest /opt/nexvest/.venv/bin/pip list | grep -iE "fastapi|requests|pymongo|matplotlib|reportlab"
```

Si falta algo, reinstalar:

```bash
sudo -u nexvest /opt/nexvest/.venv/bin/pip install -r /opt/nexvest/Nexvest-Back-FASTAPI/requirements.txt
```

### Vercel hobby vs Hetzner

> El PDF de la asignatura no exige Vercel. Se eligio Hetzner porque:
>
> 1. El endpoint `/analisis/reporte/pdf` puede tomar 20-30 segundos para el
>    portafolio completo; Vercel Hobby corta a los 10 segundos.
> 2. El ETL diario requiere un sistema persistente (no serverless).
> 3. Hetzner es ~5 EUR/mes con root completo.
