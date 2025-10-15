import json
import time
import os
from pathlib import Path

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
        'total_pages': len(processed_pages)
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