            FROM python:3.11-slim

# Configurar zona horaria (cambiar según necesidad)
ENV TZ=America/Argentina/Buenos_Aires
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    cron \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libxss1 \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorios de trabajo
WORKDIR /app

# Copiar archivos del proyecto (nueva estructura)
COPY . /app/
RUN mkdir -p /app/logs /app/backups

# Instalar dependencias de Python
RUN pip install --no-cache-dir playwright

# Instalar navegadores de Playwright
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Hacer ejecutable el script de cron
RUN chmod +x /app/scripts/cron_job.sh

# Configurar cron job para ejecutar diariamente a las 11:00 AM
RUN echo "0 11 * * * root /app/scripts/cron_job.sh >> /app/logs/cron.log 2>&1" > /etc/cron.d/scraping-corrientes

# Dar permisos correctos al archivo de cron
RUN chmod 0644 /etc/cron.d/scraping-corrientes

# Aplicar el cron job
RUN crontab /etc/cron.d/scraping-corrientes

# Crear un script de entrada para iniciar cron
RUN echo '#!/bin/bash\n\
echo "Iniciando servicio cron para scraping de Corrientes..."\n\
echo "Cron job configurado para ejecutar diariamente a las 9:00 AM"\n\
echo "Logs disponibles en /app/logs/"\n\
echo "Para ejecutar manualmente: /app/scripts/cron_job.sh"\n\
echo "================================================"\n\
service cron start\n\
echo "Servicio cron iniciado"\n\
\n\
# Mantener el contenedor corriendo\n\
tail -f /dev/null' > /app/start.sh

RUN chmod +x /app/start.sh

# Exponer directorio de logs como volumen
VOLUME ["/app/logs", "/app/corrientes/db", "/app/corrientes/docs", "/app/backups"]

# Comando por defecto
CMD ["/app/start.sh"]