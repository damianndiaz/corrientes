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
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Crear directorios de trabajo
WORKDIR /app

# Copiar y instalar dependencias de Python primero (para mejor cache)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos del proyecto
COPY . /app/
RUN mkdir -p /app/logs /app/backups

# Convertir terminaciones de línea de Windows a Unix para scripts DESPUÉS de copiar
RUN dos2unix /app/start.sh /app/scripts/cron_job.sh && \
    sed -i 's/\r$//' /app/start.sh && \
    sed -i 's/\r$//' /app/scripts/cron_job.sh

# Instalar navegadores de Playwright
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Hacer ejecutables los scripts
RUN chmod +x /app/scripts/cron_job.sh
RUN chmod +x /app/start.sh

# Configurar cron job para ejecutar diariamente a las 13:00 (1:00 PM)
RUN echo "0 13 * * * root cd /app && /app/scripts/cron_job.sh >> /app/logs/cron.log 2>&1" > /etc/cron.d/scraping-corrientes

# Dar permisos correctos al archivo de cron
RUN chmod 0644 /etc/cron.d/scraping-corrientes

# Aplicar el cron job
RUN crontab /etc/cron.d/scraping-corrientes

# Exponer directorio de logs como volumen
VOLUME ["/app/logs", "/app/db", "/app/docs", "/app/backups"]

# Comando por defecto
CMD ["/bin/bash", "-c", "echo 'Iniciando servicio cron para scraping de Corrientes...' && echo 'Cron job configurado para ejecutar diariamente a las 13:00 (1:00 PM)' && service cron start && echo 'Servicio cron iniciado' && tail -f /dev/null"]