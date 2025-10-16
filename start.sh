#!/bin/bash

echo "Iniciando servicio cron para scraping de Corrientes..."
echo "Cron job configurado para ejecutar diariamente a las 13:00 (1:00 PM)"
echo "Logs disponibles en /app/logs/"
echo "Para ejecutar manualmente: /app/scripts/cron_job.sh"
echo "================================================"

# Inicializar la base de datos si no existe
if [ ! -f "/app/db/licitar.db" ]; then
    echo "Inicializando base de datos SQLite..."
    python /app/setup/initialize_db.py
    echo "Base de datos inicializada"
fi

# Iniciar el servicio cron
service cron start
echo "Servicio cron iniciado"

# Mantener el contenedor corriendo
tail -f /dev/null