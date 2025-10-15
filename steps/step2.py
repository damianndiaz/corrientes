from playwright.sync_api import sync_playwright
import os
from pathlib import Path

def download_html(url, folder_path, file_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Timeout más corto y wait_until menos estricto
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            html = page.content()
            
            Path(folder_path).mkdir(parents=True, exist_ok=True)
            file_path = Path(folder_path) / file_name
            file_path.write_text(html, encoding='utf-8')
            
            browser.close()
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error descargando HTML {url}: {e}")
            browser.close()
            return None

def download_png(url, folder_path, file_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Timeout más corto y wait_until menos estricto
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            Path(folder_path).mkdir(parents=True, exist_ok=True)
            file_path = Path(folder_path) / file_name
            page.screenshot(path=str(file_path), full_page=True)
            
            browser.close()
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error descargando PNG {url}: {e}")
            browser.close()
            return None

def find_pliego_links(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url, wait_until='networkidle', timeout=60000)
        anchors = page.locator('a').all()
        results = []
        
        for a in anchors:
            href = a.get_attribute('href')
            text = a.text_content() or ''
            if href:
                lower = (href + ' ' + text).lower()
                if 'pliego' in lower:
                    if href.startswith('http'):
                        absolute = href
                    else:
                        from urllib.parse import urljoin
                        absolute = urljoin(url, href)
                    results.append(absolute)
        
        browser.close()
        return list(set(results)) 

def download_page_content(urls, docs_path):
    results = []
    html_dir = Path(docs_path) / 'pages_html'
    png_dir = Path(docs_path) / 'pages_png'
    
    # Asegurar que los directorios existen
    html_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    
    for i, url in enumerate(urls, 1):
        try:
            print(f"🔄 Procesando {i}/{len(urls)}: {url}")
            
            # Descargar HTML
            html_path = download_html(url, str(html_dir), f"{i}.html")
            
            # Tomar screenshot
            png_path = download_png(url, str(png_dir), f"{i}.png")
            
            # Solo agregar si ambos se descargaron exitosamente
            if html_path and png_path:
                # Guardar paths relativos desde la raíz del proyecto
                rel_html_path = os.path.join('docs', 'pages_html', f"{i}.html")
                rel_png_path = os.path.join('docs', 'pages_png', f"{i}.png")
                
                results.append((url, rel_html_path, rel_png_path))
                print(f"✅ Completado {i}/{len(urls)}")
            else:
                print(f"⚠️  Falló descarga para {url}")
            
        except Exception as e:
            print(f"❌ Error procesando {url}: {e}")
            continue
    
    return results

if __name__ == "__main__":
    # Prueba del módulo
    test_urls = [
        "https://obraspublicas.corrientes.gob.ar/noticia/licitacion-publica-n-01-2023",
        "https://obraspublicas.corrientes.gob.ar/noticia/licitacion-publica-n-22-2022"
    ]
    docs_path = "./docs"
    results = download_page_content(test_urls, docs_path)
    for url, html, png in results:
        print(f"URL: {url}")
        print(f"HTML: {html}")
        print(f"PNG: {png}")
        print("-" * 50)