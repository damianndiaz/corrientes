from playwright.sync_api import sync_playwright

def get_licitaciones_url():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://obraspublicas.corrientes.gob.ar/', 
                 wait_until='domcontentloaded', timeout=60000)
        page.wait_for_load_state('networkidle', timeout=60000)
        
        licitaciones_link = page.locator('a:has-text("Licitaciones")').first
        href = licitaciones_link.get_attribute('href')
        
        browser.close()
        return 'https://obraspublicas.corrientes.gob.ar' + href

def get_num_paginas(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_load_state('networkidle', timeout=60000)
        
        page_numbers = page.locator('.pagination a:not(:has-text("Siguiente")):not(:has-text("Último"))').all()
        max_page = 1
        
        for element in page_numbers:
            text = element.text_content()
            try:
                number = int(text)
                if number > max_page:
                    max_page = number
            except ValueError:
                continue
        
        browser.close()
        return max_page

def get_licitaciones_links(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_load_state('networkidle', timeout=60000)
        
        links = page.locator('a[href^="/noticia/"]').all()
        urls = []
        
        for link in links:
            href = link.get_attribute('href')
            if href:
                full_url = f'https://obraspublicas.corrientes.gob.ar{href}'
                if full_url not in urls:
                    urls.append(full_url)
        
        browser.close()
        return urls

def extract_all_licitacion_urls(root_url):
    # 1. Obtener URL de licitaciones
    licitaciones_url = get_licitaciones_url()
    
    # 2. Obtener número de páginas
    num_paginas = get_num_paginas(licitaciones_url)
    
    # 3. Generar URLs de todas las páginas
    all_pages_urls = [licitaciones_url]
    for i in range(2, num_paginas + 1):
        all_pages_urls.append(f"{licitaciones_url}?page={i}")
    
    # 4. Extraer enlaces de cada página
    licitaciones_por_pagina = {}
    total_licitaciones = 0
    
    for i, page_url in enumerate(all_pages_urls, 1):
        links = get_licitaciones_links(page_url)
        licitaciones_por_pagina[f"pagina{i}"] = links
        total_licitaciones += len(links)
    
    return {
        "urlPrincipal": licitaciones_url,
        "numeroPaginas": num_paginas,
        "urlsPaginas": all_pages_urls,
        "licitaciones": licitaciones_por_pagina,
        "totalLicitaciones": total_licitaciones
    }

if __name__ == "__main__":
    # Prueba del módulo
    root_url = "https://obraspublicas.corrientes.gob.ar/"
    result = extract_all_licitacion_urls(root_url)
    print(f"Total de páginas encontradas: {result['numeroPaginas']}")
    print(f"Total de licitaciones encontradas: {result['totalLicitaciones']}")