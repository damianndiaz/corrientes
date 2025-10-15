import json
import time
import os
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime


def get_database_connection(db_path):
    """Obtiene una conexión a la base de datos SQLite"""
    db_file = Path(db_path) / "licitar.db"
    
    # Verificar que la base de datos existe
    if not db_file.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_file}")
    
    connection = sqlite3.connect(str(db_file))
    # Habilitar foreign keys
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def calculate_file_hash(file_path):
    """Calcula el hash MD5 de un archivo"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None


def get_file_size(file_path):
    """Obtiene el tamaño de un archivo en bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return None


def create_run_record_sqlite(db_path):
    """Crea un nuevo registro de ejecución en SQLite"""
    connection = get_database_connection(db_path)
    cursor = connection.cursor()
    
    try:
        # Insertar nuevo run
        cursor.execute("""
            INSERT INTO runs (started_at, status)
            VALUES (CURRENT_TIMESTAMP, 'running')
        """)
        
        run_id = cursor.lastrowid
        connection.commit()
        
        return run_id
        
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()


def create_run_details_sqlite(db_path, run_id, url_data):
    """Crea el registro de detalles de la ejecución"""
    connection = get_database_connection(db_path)
    cursor = connection.cursor()
    
    try:
        # Convertir URLs a JSON para almacenar
        urls_paginas_json = json.dumps(url_data.get('urlsPaginas', []))
        
        cursor.execute("""
            INSERT INTO run_details (
                run_id, url_principal, numero_paginas, 
                total_licitaciones, urls_paginas
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            run_id,
            url_data.get('urlPrincipal', ''),
            url_data.get('numeroPaginas', 0),
            url_data.get('totalLicitaciones', 0),
            urls_paginas_json
        ))
        
        connection.commit()
        
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()


def store_licitaciones_sqlite(db_path, run_id, processed_pages):
    """Almacena las licitaciones y archivos en SQLite"""
    connection = get_database_connection(db_path)
    cursor = connection.cursor()
    
    try:
        licitacion_ids = []
        
        for url, html_path, png_path in processed_pages:
            # 1. Insertar licitación
            cursor.execute("""
                INSERT INTO licitaciones (run_id, url, scraped_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (run_id, url))
            
            licitacion_id = cursor.lastrowid
            licitacion_ids.append(licitacion_id)
            
            # 2. Insertar archivo HTML
            if html_path and os.path.exists(html_path):
                html_size = get_file_size(html_path)
                html_hash = calculate_file_hash(html_path)
                # Convertir a ruta absoluta y luego calcular relativa
                html_abs_path = os.path.abspath(html_path)
                project_root = Path(db_path).parent
                try:
                    html_relative = str(Path(html_abs_path).relative_to(project_root))
                except ValueError:
                    # Si no puede ser relativa, usar el path original
                    html_relative = html_path
                
                cursor.execute("""
                    INSERT INTO archivos_html (
                        licitacion_id, path_relativo, path_absoluto,
                        tamano_bytes, hash_md5
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    licitacion_id, html_relative, html_abs_path,
                    html_size, html_hash
                ))
            
            # 3. Insertar archivo PNG
            if png_path and os.path.exists(png_path):
                png_size = get_file_size(png_path)
                # Convertir a ruta absoluta y luego calcular relativa
                png_abs_path = os.path.abspath(png_path)
                project_root = Path(db_path).parent
                try:
                    png_relative = str(Path(png_abs_path).relative_to(project_root))
                except ValueError:
                    # Si no puede ser relativa, usar el path original
                    png_relative = png_path
                
                cursor.execute("""
                    INSERT INTO archivos_png (
                        licitacion_id, path_relativo, path_absoluto,
                        tamano_bytes
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    licitacion_id, png_relative, png_abs_path,
                    png_size
                ))
        
        connection.commit()
        return licitacion_ids
        
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()


def finish_run_sqlite(db_path, run_id, total_pages, execution_time):
    """Finaliza el registro de ejecución"""
    connection = get_database_connection(db_path)
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE runs 
            SET finished_at = CURRENT_TIMESTAMP,
                status = 'completed',
                total_pages = ?,
                execution_time_seconds = ?
            WHERE id = ?
        """, (total_pages, execution_time, run_id))
        
        connection.commit()
        
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()


def store_metrics_sqlite(db_path, run_id, metrics):
    """Almacena métricas de la ejecución"""
    connection = get_database_connection(db_path)
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO metricas_ejecucion (
                run_id, paginas_procesadas, paginas_exitosas,
                paginas_con_error, archivos_html_creados,
                archivos_png_creados
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            metrics.get('paginas_procesadas', 0),
            metrics.get('paginas_exitosas', 0),
            metrics.get('paginas_con_error', 0),
            metrics.get('archivos_html_creados', 0),
            metrics.get('archivos_png_creados', 0)
        ))
        
        connection.commit()
        
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()


# ============================================================================
# FUNCIONES LEGACY (JSONL) - Mantenidas para compatibilidad
# ============================================================================

def get_next_id(jsonl_file):
    if not os.path.exists(jsonl_file):
        return 1
    
    max_id = 0
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if 'id' in record and record['id'] > max_id:
                        max_id = record['id']
    except:
        pass
    
    return max_id + 1

def append_to_jsonl(jsonl_file, record):
    Path(jsonl_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(jsonl_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

def create_run_record(db_path):
    runs_file = Path(db_path) / 'runs.jsonl'
    run_details_file = Path(db_path) / 'run_details.jsonl'
    
    # Crear registro en runs.jsonl
    run_id = get_next_id(runs_file)
    run_details_id = get_next_id(run_details_file)
    
    run_record = {
        'id': run_id,
        'started_at': int(time.time()),
        'finished_at': None,
        'details_id': run_details_id
    }
    
    append_to_jsonl(runs_file, run_record)
    return run_id, run_details_id

def create_run_details_record(db_path, run_details_id, url_data):
    run_details_file = Path(db_path) / 'run_details.jsonl'
    
    details_record = {
        'id': run_details_id,
        'details': url_data
    }
    
    append_to_jsonl(run_details_file, details_record)

def create_page_records(db_path, processed_pages):
    pages_file = Path(db_path) / 'pages.jsonl'
    pages_html_file = Path(db_path) / 'pages_html.jsonl'
    pages_png_file = Path(db_path) / 'pages_png.jsonl'
    
    page_ids = []
    
    for url, html_path, png_path in processed_pages:
        # Crear registro en pages_html.jsonl
        html_id = get_next_id(pages_html_file)
        html_record = {
            'id': html_id,
            'path': html_path
        }
        append_to_jsonl(pages_html_file, html_record)
        
        # Crear registro en pages_png.jsonl
        png_id = get_next_id(pages_png_file)
        png_record = {
            'id': png_id,
            'path': png_path
        }
        append_to_jsonl(pages_png_file, png_record)
        
        # Crear registro en pages.jsonl
        page_id = get_next_id(pages_file)
        page_record = {
            'id': page_id,
            'url': url,
            'pages_png_id': png_id,
            'pages_html_id': html_id,
            'timestamp': int(time.time())
        }
        append_to_jsonl(pages_file, page_record)
        
        page_ids.append(page_id)
    
    return page_ids

def finish_run_record(db_path, run_id):
    runs_file = Path(db_path) / 'runs.jsonl'
    
    # Leer todos los registros
    records = []
    if os.path.exists(runs_file):
        with open(runs_file, 'r', encoding='utf-8') as f:
            records = [json.loads(line) for line in f if line.strip()]
    
    # Actualizar el registro correspondiente
    for record in records:
        if record['id'] == run_id:
            record['finished_at'] = int(time.time())
            break
    
    # Reescribir el archivo
    with open(runs_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

def store_pipeline_data(db_path, url_data, processed_pages):
    """
    Almacena datos del pipeline en SQLite
    
    Args:
        db_path: Ruta al directorio que contiene la base de datos
        url_data: Datos de URLs extraídas del step1
        processed_pages: Lista de tuplas (url, html_path, png_path) del step2
    
    Returns:
        Diccionario con información del almacenamiento
    """
    start_time = time.time()
    
    try:
        # 1. Crear registro de ejecución
        print("📝 Creando registro de ejecución...")
        run_id = create_run_record_sqlite(db_path)
        
        # 2. Crear registro de detalles
        print("📋 Almacenando detalles de ejecución...")
        create_run_details_sqlite(db_path, run_id, url_data)
        
        # 3. Almacenar licitaciones y archivos
        print(f"💾 Almacenando {len(processed_pages)} licitaciones...")
        licitacion_ids = store_licitaciones_sqlite(db_path, run_id, processed_pages)
        
        # 4. Calcular métricas
        html_count = sum(1 for _, html_path, _ in processed_pages if html_path and os.path.exists(html_path))
        png_count = sum(1 for _, _, png_path in processed_pages if png_path and os.path.exists(png_path))
        
        metrics = {
            'paginas_procesadas': len(processed_pages),
            'paginas_exitosas': len(licitacion_ids),
            'paginas_con_error': len(processed_pages) - len(licitacion_ids),
            'archivos_html_creados': html_count,
            'archivos_png_creados': png_count
        }
        
        # 5. Almacenar métricas
        print("📊 Guardando métricas...")
        store_metrics_sqlite(db_path, run_id, metrics)
        
        # 6. Finalizar ejecución
        execution_time = int(time.time() - start_time)
        print("✅ Finalizando registro de ejecución...")
        finish_run_sqlite(db_path, run_id, len(processed_pages), execution_time)
        
        print(f"🎉 Datos almacenados exitosamente en SQLite!")
        print(f"   - Run ID: {run_id}")
        print(f"   - Licitaciones: {len(licitacion_ids)}")
        print(f"   - Archivos HTML: {html_count}")
        print(f"   - Archivos PNG: {png_count}")
        print(f"   - Tiempo ejecución: {execution_time}s")
        
        return {
            'run_id': run_id,
            'licitacion_ids': licitacion_ids,
            'total_pages': len(processed_pages),
            'metrics': metrics,
            'execution_time': execution_time,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"❌ Error almacenando en SQLite: {e}")
        
        # En caso de error, intentar con sistema JSONL legacy
        print("🔄 Intentando con sistema JSONL legacy...")
        try:
            return store_pipeline_data_legacy(db_path, url_data, processed_pages)
        except Exception as legacy_error:
            print(f"❌ Error también en sistema legacy: {legacy_error}")
            raise e


def store_pipeline_data_legacy(db_path, url_data, processed_pages):
    """Función legacy usando JSONL como backup"""
    # 1. Crear registro de run
    run_id, run_details_id = create_run_record(db_path)
    
    # 2. Crear registro de detalles
    create_run_details_record(db_path, run_details_id, url_data)
    
    # 3. Crear registros de páginas
    page_ids = create_page_records(db_path, processed_pages)
    
    # 4. Finalizar registro de run
    finish_run_record(db_path, run_id)
    
    return {
        'run_id': run_id,
        'run_details_id': run_details_id,
        'page_ids': page_ids,
        'total_pages': len(processed_pages),
        'status': 'legacy'
    }

if __name__ == "__main__":
    # Prueba del módulo
    test_url_data = {
        "urlPrincipal": "https://obraspublicas.corrientes.gob.ar/home/licitaciones--5/categorias",
        "numeroPaginas": 2,
        "urlsPaginas": ["url1", "url2"],
        "licitaciones": {"pagina1": ["url1", "url2"], "pagina2": ["url3", "url4"]},
        "totalLicitaciones": 4
    }
    
    test_processed_pages = [
        ("url1", "docs/pages_html/1.html", "docs/pages_png/1.png"),
        ("url2", "docs/pages_html/2.html", "docs/pages_png/2.png")
    ]
    
    db_path = "./test_db"
    result = store_pipeline_data(db_path, test_url_data, test_processed_pages)
    print(f"Datos almacenados: {result}")