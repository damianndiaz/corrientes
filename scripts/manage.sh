set -e

CONTAINER_NAME="corrientes-scraper"
IMAGE_NAME="scraping-corrientes"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes coloreados
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}=== SCRAPING CORRIENTES - GESTOR DE CONTENEDOR ===${NC}"
    echo ""
    echo "Comandos disponibles:"
    echo ""
    echo -e "  ${GREEN}build${NC}     - Construir la imagen Docker"
    echo -e "  ${GREEN}start${NC}     - Iniciar el contenedor con cron job"
    echo -e "  ${GREEN}stop${NC}      - Detener el contenedor"
    echo -e "  ${GREEN}restart${NC}   - Reiniciar el contenedor"
    echo -e "  ${GREEN}logs${NC}      - Ver logs del cron job"
    echo -e "  ${GREEN}shell${NC}     - Entrar al contenedor (bash)"
    echo -e "  ${GREEN}run${NC}       - Ejecutar scraping manualmente"
    echo -e "  ${GREEN}status${NC}    - Ver estado del contenedor"
    echo -e "  ${GREEN}clean${NC}     - Limpiar contenedores e imágenes"
    echo ""
    echo "Ejemplo: ./manage.sh start"
}

# Función para construir la imagen
build_image() {
    log "Construyendo imagen Docker..."
    docker-compose build
    log "✅ Imagen construida exitosamente"
}

# Función para iniciar el contenedor
start_container() {
    log "Iniciando contenedor con cron job..."
    
    # Crear directorios necesarios
    mkdir -p logs corrientes/db corrientes/docs backups
    
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        log "✅ Contenedor iniciado exitosamente"
        log "📅 Cron job configurado para ejecutar diariamente a las 9:00 AM"
        log "📋 Ver logs: ./manage.sh logs"
        log "🔧 Ejecutar manualmente: ./manage.sh run"
    else
        error "❌ Error al iniciar el contenedor"
        exit 1
    fi
}

# Función para detener el contenedor
stop_container() {
    log "Deteniendo contenedor..."
    docker-compose down
    log "✅ Contenedor detenido"
}

# Función para reiniciar el contenedor
restart_container() {
    log "Reiniciando contenedor..."
    docker-compose restart
    log "✅ Contenedor reiniciado"
}

# Función para ver logs
show_logs() {
    log "Mostrando logs del cron job..."
    echo ""
    
    # Mostrar logs del contenedor
    echo -e "${BLUE}=== LOGS DEL CONTENEDOR ===${NC}"
    docker-compose logs --tail=50 -f
}

# Función para entrar al contenedor
enter_shell() {
    log "Entrando al contenedor..."
    docker-compose exec scraping-corrientes bash
}

# Función para ejecutar scraping manualmente
run_manual() {
    log "Ejecutando scraping manualmente..."
    docker-compose exec scraping-corrientes /app/scripts/cron_job.sh
}

# Función para ver estado
show_status() {
    log "Estado del sistema:"
    echo ""
    
    # Estado del contenedor
    echo -e "${BLUE}=== ESTADO DEL CONTENEDOR ===${NC}"
    docker-compose ps
    echo ""
    
    # Última ejecución
    if [ -f "logs/cron_$(date +%Y%m%d).log" ]; then
        echo -e "${BLUE}=== ÚLTIMA EJECUCIÓN ===${NC}"
        tail -10 "logs/cron_$(date +%Y%m%d).log"
    else
        warn "No se encontraron logs de hoy"
    fi
    
    # Estadísticas de datos
    if [ -d "corrientes/db" ]; then
        echo ""
        echo -e "${BLUE}=== ESTADÍSTICAS DE DATOS ===${NC}"
        if [ -f "corrientes/db/pages.jsonl" ]; then
            TOTAL_PAGES=$(wc -l < corrientes/db/pages.jsonl 2>/dev/null || echo "0")
            echo "📄 Total de páginas: $TOTAL_PAGES"
        fi
        
        if [ -d "corrientes/docs/pages_html" ]; then
            TOTAL_HTML=$(find corrientes/docs/pages_html -name "*.html" | wc -l)
            echo "📝 Archivos HTML: $TOTAL_HTML"
        fi
        
        if [ -d "corrientes/docs/pages_png" ]; then
            TOTAL_PNG=$(find corrientes/docs/pages_png -name "*.png" | wc -l)
            echo "🖼️  Archivos PNG: $TOTAL_PNG"
        fi
    fi
}

# Función para limpiar
clean_all() {
    warn "Esta acción eliminará todos los contenedores e imágenes relacionados"
    read -p "¿Estás seguro? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Limpiando contenedores e imágenes..."
        docker-compose down --rmi all --volumes
        docker system prune -f
        log "✅ Limpieza completada"
    else
        log "Operación cancelada"
    fi
}

# Procesar comando
case "$1" in
    build)
        build_image
        ;;
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    logs)
        show_logs
        ;;
    shell)
        enter_shell
        ;;
    run)
        run_manual
        ;;
    status)
        show_status
        ;;
    clean)
        clean_all
        ;;
    *)
        show_help
        exit 1
        ;;
esac