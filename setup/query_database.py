#!/usr/bin/env python3
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def get_database_path():
    """Obtiene la ruta a la base de datos"""
    project_root = Path(__file__).parent.parent
    return project_root / "db" / "licitar.db"


def connect_database():
    """Conecta a la base de datos"""
    db_path = get_database_path()
    
    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        sys.exit(1)
    
    return sqlite3.connect(str(db_path))


def show_stats():
    """Muestra estadísticas generales de la base de datos"""
    conn = connect_database()
    cursor = conn.cursor()
    
    print("📊 ESTADÍSTICAS GENERALES")
    print("=" * 50)
    
    # Estadísticas básicas
    stats_queries = [
        ("Total de ejecuciones", "SELECT COUNT(*) FROM runs"),
        ("Ejecuciones completadas", "SELECT COUNT(*) FROM runs WHERE status = 'completed'"),
        ("Total de licitaciones", "SELECT COUNT(*) FROM licitaciones"),
        ("Archivos HTML", "SELECT COUNT(*) FROM archivos_html"),
        ("Archivos PNG", "SELECT COUNT(*) FROM archivos_png"),
        ("Errores registrados", "SELECT COUNT(*) FROM scraping_errors"),
    ]
    
    for label, query in stats_queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"{label:.<30} {count:>6}")
    
    print()
    
    # Estadísticas de tiempo
    cursor.execute("""
        SELECT 
            AVG(execution_time_seconds) as avg_time,
            MIN(execution_time_seconds) as min_time,
            MAX(execution_time_seconds) as max_time
        FROM runs 
        WHERE status = 'completed' AND execution_time_seconds > 0
    """)
    
    time_stats = cursor.fetchone()
    if time_stats and time_stats[0]:
        print("⏱️  TIEMPOS DE EJECUCIÓN")
        print(f"Promedio: {time_stats[0]:.1f}s")
        print(f"Mínimo:   {time_stats[1]}s") 
        print(f"Máximo:   {time_stats[2]}s")
    
    conn.close()


def show_recent_runs(limit=10):
    """Muestra las ejecuciones más recientes"""
    conn = connect_database()
    cursor = conn.cursor()
    
    print(f"🚀 ÚLTIMAS {limit} EJECUCIONES")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            id,
            started_at,
            finished_at,
            status,
            total_pages,
            execution_time_seconds
        FROM runs
        ORDER BY started_at DESC
        LIMIT ?
    """, (limit,))
    
    runs = cursor.fetchall()
    
    if not runs:
        print("No hay ejecuciones registradas.")
        return
    
    print(f"{'ID':<4} {'Inicio':<20} {'Estado':<12} {'Páginas':<8} {'Tiempo':<8}")
    print("-" * 70)
    
    for run in runs:
        run_id, started, finished, status, pages, exec_time = run
        
        # Formatear fecha
        try:
            start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
            start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            start_str = started[:19] if started else "N/A"
        
        pages_str = str(pages) if pages else "0"
        time_str = f"{exec_time}s" if exec_time else "N/A"
        
        print(f"{run_id:<4} {start_str:<20} {status:<12} {pages_str:<8} {time_str:<8}")
    
    conn.close()


def show_recent_licitaciones(limit=20):
    """Muestra las licitaciones más recientes"""
    conn = connect_database()
    cursor = conn.cursor()
    
    print(f"📋 ÚLTIMAS {limit} LICITACIONES")
    print("=" * 100)
    
    cursor.execute("""
        SELECT 
            l.id,
            l.url,
            l.title,
            l.scraped_at,
            r.id as run_id
        FROM licitaciones l
        LEFT JOIN runs r ON l.run_id = r.id
        ORDER BY l.scraped_at DESC
        LIMIT ?
    """, (limit,))
    
    licitaciones = cursor.fetchall()
    
    if not licitaciones:
        print("No hay licitaciones registradas.")
        return
    
    print(f"{'ID':<4} {'Run':<5} {'Fecha':<20} {'URL':<70}")
    print("-" * 100)
    
    for lic in licitaciones:
        lic_id, url, title, scraped, run_id = lic
        
        # Formatear fecha
        try:
            scraped_dt = datetime.fromisoformat(scraped.replace('Z', '+00:00'))
            scraped_str = scraped_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            scraped_str = scraped[:19] if scraped else "N/A"
        
        # Truncar URL si es muy larga
        url_display = url[:65] + "..." if len(url) > 68 else url
        
        print(f"{lic_id:<4} {run_id:<5} {scraped_str:<20} {url_display:<70}")
    
    conn.close()


def show_last_run_details():
    """Muestra detalles de la última ejecución"""
    conn = connect_database()
    cursor = conn.cursor()
    
    print("🔍 DETALLES DE LA ÚLTIMA EJECUCIÓN")
    print("=" * 50)
    
    # Obtener última ejecución
    cursor.execute("""
        SELECT * FROM runs 
        ORDER BY started_at DESC 
        LIMIT 1
    """)
    
    last_run = cursor.fetchone()
    
    if not last_run:
        print("No hay ejecuciones registradas.")
        return
    
    run_id = last_run[0]
    
    print(f"ID de ejecución: {run_id}")
    print(f"Estado: {last_run[3]}")
    print(f"Inicio: {last_run[1]}")
    print(f"Fin: {last_run[2] if last_run[2] else 'En curso'}")
    print(f"Páginas procesadas: {last_run[4]}")
    print(f"Tiempo de ejecución: {last_run[5]}s" if last_run[5] else "N/A")
    
    print()
    
    # Detalles de la ejecución
    cursor.execute("""
        SELECT url_principal, numero_paginas, total_licitaciones
        FROM run_details 
        WHERE run_id = ?
    """, (run_id,))
    
    details = cursor.fetchone()
    if details:
        print("📋 Detalles:")
        print(f"  URL principal: {details[0]}")
        print(f"  Páginas navegadas: {details[1]}")
        print(f"  Licitaciones encontradas: {details[2]}")
    
    # Métricas
    cursor.execute("""
        SELECT * FROM metricas_ejecucion 
        WHERE run_id = ?
    """, (run_id,))
    
    metrics = cursor.fetchone()
    if metrics:
        print()
        print("📊 Métricas:")
        print(f"  Páginas procesadas: {metrics[2]}")
        print(f"  Páginas exitosas: {metrics[3]}")
        print(f"  Páginas con error: {metrics[4]}")
        print(f"  Archivos HTML creados: {metrics[5]}")
        print(f"  Archivos PNG creados: {metrics[6]}")
    
    conn.close()


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        command = "stats"
    else:
        command = sys.argv[1].lower()
    
    try:
        if command == "stats":
            show_stats()
        elif command == "runs":
            show_recent_runs()
        elif command == "licitaciones":
            show_recent_licitaciones()
        elif command == "last":
            show_last_run_details()
        else:
            print("❌ Comando no reconocido.")
            print("Comandos disponibles: stats, runs, licitaciones, last")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()