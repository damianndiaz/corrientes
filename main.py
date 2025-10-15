import os
import sys
from pathlib import Path
import importlib.util

# Obtener rutas a los archivos de steps
current_dir = Path(__file__).parent
steps_dir = current_dir / 'steps'

# Cargar step1
spec1 = importlib.util.spec_from_file_location("step1", steps_dir / "step1.py")
step1 = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(step1)
extract_all_licitacion_urls = step1.extract_all_licitacion_urls

# Cargar step2
spec2 = importlib.util.spec_from_file_location("step2", steps_dir / "step2.py")
step2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(step2)
download_page_content = step2.download_page_content

# Cargar step3
spec3 = importlib.util.spec_from_file_location("step3", steps_dir / "step3.py")
step3 = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(step3)
store_pipeline_data = step3.store_pipeline_data

def flatten_licitacion_urls(licitaciones_data):
    all_urls = []
    for page_key, urls in licitaciones_data['licitaciones'].items():
        all_urls.extend(urls)
    return all_urls

def main():
    # Configuración de rutas
    root_url = "https://obraspublicas.corrientes.gob.ar/"
    base_path = Path(__file__).parent
    docs_path = base_path / 'docs'
    db_path = base_path / 'db'
    
    # STEP 1: Extraer URLs de licitaciones
    url_data = extract_all_licitacion_urls(root_url)
    
    # Convertir URLs a lista plana
    all_licitacion_urls = flatten_licitacion_urls(url_data)
    
    # STEP 2: Descargar contenido HTML y PNG
    processed_pages = download_page_content(all_licitacion_urls, str(docs_path))
    
    # STEP 3: Almacenar datos en archivos JSONL
    storage_result = store_pipeline_data(str(db_path), url_data, processed_pages)
    
    return storage_result

if __name__ == "__main__":
    try:
        result = main()
    except Exception as e:
        pass