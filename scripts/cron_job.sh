# Configuración de logging
LOG_FILE="/app/logs/cron_$(date +%Y%m%d).log"
LOCK_FILE="/tmp/scraping_corrientes.lock"
ERROR_EMAIL="damian.diaz@vaovaodata.com"  

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función para limpiar al salir
cleanup() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
        log "🧹 Lock file eliminado"
    fi
}

# Configurar trap para limpiar al salir
trap cleanup EXIT

# =============================================================================
# VERIFICAR QUE NO HAY OTRA INSTANCIA CORRIENDO
# =============================================================================
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE")
    if ps -p "$LOCK_PID" > /dev/null 2>&1; then
        log "❌ ERROR: Otra instancia ya está corriendo (PID: $LOCK_PID)"
        exit 1
    else
        log "⚠️  Lock file obsoleto encontrado, eliminando..."
        rm -f "$LOCK_FILE"
    fi
fi

# Crear lock file
echo $$ > "$LOCK_FILE"
log "🔒 Lock file creado (PID: $$)"

# =============================================================================
# PREPARAR ENTORNO
# =============================================================================
log "🚀 Iniciando scraping diario de licitaciones de Corrientes"

# Cambiar al directorio del proyecto (ahora es la raíz)
cd /app

# Verificar que el directorio existe
if [ ! -d "/app" ]; then
    log "❌ ERROR: Directorio /app no encontrado"
    exit 1
fi

# Verificar que main.py existe
if [ ! -f "main.py" ]; then
    log "❌ ERROR: main.py no encontrado en /app/corrientes"
    exit 1
fi

# =============================================================================
# CREAR BACKUP DE DATOS ANTERIORES 
# =============================================================================
BACKUP_DIR="/app/backups/$(date +%Y%m%d_%H%M%S)"
if [ -d "db" ] && [ "$(ls -A db)" ]; then
    log "💾 Creando backup de datos anteriores en $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp -r db/* "$BACKUP_DIR/" 2>/dev/null || true
    cp -r docs/* "$BACKUP_DIR/" 2>/dev/null || true
    log "✅ Backup completado"
fi

# =============================================================================
# EJECUTAR EL PIPELINE PRINCIPAL
# =============================================================================
log "⚙️  Ejecutando Main.py..."

# Ejecutar main.py y capturar el código de salida
if python3 main.py; then
    EXIT_CODE=$?
    log "✅ Pipeline ejecutado exitosamente (código: $EXIT_CODE)"
    
    # Verificar que se crearon los archivos esperados
    if [ -f "db/runs.jsonl" ] && [ -f "db/pages.jsonl" ]; then
        TOTAL_PAGES=$(wc -l < db/pages.jsonl)
        TOTAL_HTML=$(find docs/pages_html -name "*.html" | wc -l)
        TOTAL_PNG=$(find docs/pages_png -name "*.png" | wc -l)
        
        log "📊 Resultados del scraping:"
        log "   - Páginas procesadas: $TOTAL_PAGES"
        log "   - Archivos HTML: $TOTAL_HTML"
        log "   - Archivos PNG: $TOTAL_PNG"
        
        # Verificar consistencia
        if [ "$TOTAL_PAGES" -eq "$TOTAL_HTML" ] && [ "$TOTAL_PAGES" -eq "$TOTAL_PNG" ]; then
            log "✅ Datos consistentes - scraping completado correctamente"
        else
            log "⚠️  ADVERTENCIA: Inconsistencia en los datos (páginas: $TOTAL_PAGES, HTML: $TOTAL_HTML, PNG: $TOTAL_PNG)"
        fi
    else
        log "❌ ERROR: Archivos de salida no encontrados"
        exit 1
    fi
else
    EXIT_CODE=$?
    log "❌ ERROR: Pipeline falló con código $EXIT_CODE"
    
    
    exit $EXIT_CODE
fi

# =============================================================================
# LIMPIAR ARCHIVOS ANTIGUOS 
# =============================================================================
log "🧹 Limpiando backups antiguos (>7 días)..."
find /app/backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true

# =============================================================================
# FINALIZAR
# =============================================================================
DURATION=$SECONDS
log "🏁 Scraping completado en ${DURATION} segundos"
log "=================================================="

exit 0