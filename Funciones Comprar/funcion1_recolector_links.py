import asyncio
import re
from datetime import datetime
from base_scraper import BaseScraper

class RecolectorLinks(BaseScraper):
    def __init__(self, headless=True):
        super().__init__(headless)
    
    async def recolectar_todos_los_links(self):
        """
        Función principal: Recolectar TODOS los links de licitaciones
        """
        print("\n🔗 FUNCIÓN 1: RECOLECTANDO TODOS LOS LINKS DE LICITACIONES")
        print("=" * 80)
        
        resultado = {
            'links_proxima_apertura': [],
            'links_ultimos_30_dias': [],
            'metadata': {
                'total_paginas_proxima': 0,
                'total_paginas_30_dias': 0,
                'fecha_extraccion': datetime.now().isoformat(),
                'total_links': 0
            }
        }
        
        try:
            await self.navigate_to_main_page()
            
            # PASO 1: Recolectar links de "Procesos con apertura próxima"
            print(f"\n🎯 PASO 1: PRÓXIMA APERTURA")
            print("=" * 50)
            
            await self._recolectar_links_proxima_apertura(resultado)
            
            # PASO 2: Recolectar links de "Procesos con apertura en los últimos 30 días"
            print(f"\n🎯 PASO 2: ÚLTIMOS 30 DÍAS")
            print("=" * 50)
            
            await self._recolectar_links_ultimos_30_dias(resultado)
            
            # PASO 3: Guardar resultados
            resultado['metadata']['total_links'] = len(resultado['links_proxima_apertura']) + len(resultado['links_ultimos_30_dias'])
            
            self.save_json(resultado, 'funcion1_todos_los_links.json')
            self._mostrar_resumen_recoleccion(resultado)
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error en recolección completa: {e}")
            return resultado
    
    async def _recolectar_links_proxima_apertura(self, resultado):
        """Recolectar todos los links de próxima apertura"""
        try:
            # Ir a página principal
            await self.navigate_to_main_page()
            
            # Hacer clic en "Procesos con apertura próxima"
            print("🔍 Buscando 'Procesos con apertura próxima'...")
            
            # Buscar el botón principal de próxima apertura
            boton_principal = await self._encontrar_boton_principal_proxima()
            
            if boton_principal:
                print("✅ Encontrado botón principal, haciendo clic...")
                await self._ejecutar_click_seguro(boton_principal)
                
                await self.page.wait_for_timeout(3000)
                
                # Buscar botón "Ver todos"
                await self._ir_a_ver_todos()
                
                # Recolectar links de todas las páginas
                total_paginas = await self._recolectar_links_todas_las_paginas(
                    resultado['links_proxima_apertura'], 
                    "proxima_apertura"
                )
                
                resultado['metadata']['total_paginas_proxima'] = total_paginas
                print(f"✅ Próxima apertura: {len(resultado['links_proxima_apertura'])} links de {total_paginas} páginas")
            
            else:
                print("❌ No se encontró el botón de próxima apertura")
                
        except Exception as e:
            print(f"❌ Error recolectando próxima apertura: {e}")
    
    async def _recolectar_links_ultimos_30_dias(self, resultado):
        """Recolectar todos los links de últimos 30 días"""
        try:
            # Volver a página principal
            await self.navigate_to_main_page()
            
            print("🔍 Buscando 'Procesos con apertura en los últimos 30 días'...")
            
            # Buscar el botón principal de últimos 30 días
            boton_principal = await self._encontrar_boton_principal_30_dias()
            
            if boton_principal:
                print("✅ Encontrado botón principal, haciendo clic...")
                await self._ejecutar_click_seguro(boton_principal)
                
                await self.page.wait_for_timeout(3000)
                
                # Buscar botón "Ver todos"
                await self._ir_a_ver_todos()
                
                # Recolectar links de todas las páginas
                total_paginas = await self._recolectar_links_todas_las_paginas(
                    resultado['links_ultimos_30_dias'], 
                    "ultimos_30_dias"
                )
                
                resultado['metadata']['total_paginas_30_dias'] = total_paginas
                print(f"✅ Últimos 30 días: {len(resultado['links_ultimos_30_dias'])} links de {total_paginas} páginas")
            
            else:
                print("❌ No se encontró el botón de últimos 30 días")
                
        except Exception as e:
            print(f"❌ Error recolectando últimos 30 días: {e}")
    
    async def _encontrar_boton_principal_proxima(self):
        """Encontrar el botón principal de próxima apertura (el que tiene más cantidad)"""
        try:
            # Buscar elementos que contengan "próxima apertura" y un número alto
            elementos = await self.page.query_selector_all('a')
            
            mejor_candidato = None
            mayor_numero = 0
            
            for elemento in elementos:
                texto = await elemento.text_content()
                if texto and 'próxima' in texto.lower():
                    # Extraer números del texto
                    numeros = re.findall(r'\d+', texto)
                    if numeros:
                        numero = int(numeros[-1])  # Tomar el último número
                        if numero > mayor_numero:
                            mayor_numero = numero
                            mejor_candidato = elemento
                            print(f"   📊 Candidato: {texto.strip()[:60]} ({numero})")
            
            if mejor_candidato:
                print(f"   ✅ Seleccionado: {mayor_numero} procesos")
            
            return mejor_candidato
            
        except Exception as e:
            print(f"⚠️  Error encontrando botón próxima: {e}")
            return None
    
    async def _encontrar_boton_principal_30_dias(self):
        """Encontrar el botón principal de últimos 30 días (el que tiene más cantidad)"""
        try:
            elementos = await self.page.query_selector_all('a')
            
            mejor_candidato = None
            mayor_numero = 0
            
            for elemento in elementos:
                texto = await elemento.text_content()
                if texto and ('últimos' in texto.lower() or '30' in texto):
                    numeros = re.findall(r'\d+', texto)
                    if numeros:
                        numero = int(numeros[-1])
                        if numero > mayor_numero:
                            mayor_numero = numero
                            mejor_candidato = elemento
                            print(f"   📊 Candidato: {texto.strip()[:60]} ({numero})")
            
            if mejor_candidato:
                print(f"   ✅ Seleccionado: {mayor_numero} procesos")
            
            return mejor_candidato
            
        except Exception as e:
            print(f"⚠️  Error encontrando botón 30 días: {e}")
            return None
    
    async def _ejecutar_click_seguro(self, elemento):
        try:
            href = await elemento.get_attribute('href')
            
            if href and 'javascript:__doPostBack' in href:
                match = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", href)
                if match:
                    target = match.group(1)
                    argument = match.group(2)
                    script = f"__doPostBack('{target}', '{argument}');"
                    await self.page.evaluate(script)
                    print(f"   🖱️  Ejecutado postback: {target}")
            else:
                await elemento.click()
                print(f"   🖱️  Click ejecutado")
                
        except Exception as e:
            print(f"⚠️  Error en click: {e}")
    
    async def _ir_a_ver_todos(self):
        """Buscar y hacer clic en 'Ver todos'"""
        try:
            print("🔍 Buscando botón 'Ver todos'...")
            
            # Diferentes variaciones del botón "Ver todos"
            selectores_ver_todos = [
                'text="Ver todos"',
                'text="ver todos"',
                'text="VER TODOS"',
                'text=/ver todos/i',
                'a:has-text("Ver todos")',
                'a:has-text("ver todos")',
                '[title*="Ver todos"]',
                '[alt*="Ver todos"]'
            ]
            
            for selector in selectores_ver_todos:
                try:
                    elemento = await self.page.query_selector(selector)
                    if elemento:
                        print(f"   ✅ Encontrado 'Ver todos' con selector: {selector}")
                        await elemento.click()
                        await self.page.wait_for_timeout(2000)
                        return True
                except:
                    continue
            
            print("   ⚠️  No se encontró botón 'Ver todos', continuando desde página actual...")
            return False
            
        except Exception as e:
            print(f"⚠️  Error buscando 'Ver todos': {e}")
            return False
    
    async def _recolectar_links_todas_las_paginas(self, lista_links, prefijo_tipo):
        """Recolectar links de todas las páginas del paginador"""
        pagina_actual = 1
        total_links_pagina = 0
        
        try:
            while True:
                print(f"   📄 Página {pagina_actual}: ", end="")
                
                # Extraer links de la página actual
                links_pagina = await self._extraer_links_pagina_actual()
                
                if links_pagina:
                    # Agregar metadata a cada link
                    for i, link in enumerate(links_pagina):
                        link_completo = {
                            'url': link['url'],
                            'texto': link['texto'],
                            'numero_proceso': link.get('numero_proceso', ''),
                            'pagina': pagina_actual,
                            'posicion_en_pagina': i + 1,
                            'tipo_origen': prefijo_tipo,
                            'timestamp': datetime.now().isoformat()
                        }
                        lista_links.append(link_completo)
                    
                    print(f"✅ {len(links_pagina)} links extraídos")
                    total_links_pagina += len(links_pagina)
                    
                    # Progreso ocasional
                    if pagina_actual % 10 == 0:
                        print(f"   📊 Progreso: {pagina_actual} páginas completadas")
                else:
                    print("⚠️  No se encontraron links")
                
                # Verificar si hay más páginas antes de intentar navegar
                if not await self._hay_siguiente_pagina():
                    print(f"   🏁 No hay más páginas - fin en página {pagina_actual}")
                    break
                
                # Buscar siguiente página
                if not await self._ir_a_siguiente_pagina():
                    print(f"   🏁 Error navegando - fin en página {pagina_actual}")
                    break
                
                pagina_actual += 1
                
                # Limite de seguridad
                if pagina_actual > 200:
                    print(f"   ⚠️  Límite de seguridad alcanzado (200 páginas)")
                    break
                    
            print(f"   📊 Total: {total_links_pagina} links de {pagina_actual} páginas")
            return pagina_actual
            
        except Exception as e:
            print(f"❌ Error navegando páginas: {e}")
            return pagina_actual
    
    async def _extraer_links_pagina_actual(self):
        links = []
        
        try:
            # Buscar tabla de licitaciones
            tablas = await self.page.query_selector_all('table')
            
            for tabla in tablas:
                filas = await tabla.query_selector_all('tr')
                
                if len(filas) > 3:  # Tabla con contenido
                    for fila in filas[1:]:  # Saltar header
                        enlaces_fila = await fila.query_selector_all('a')
                        
                        for enlace in enlaces_fila:
                            href = await enlace.get_attribute('href')
                            texto = await enlace.text_content()
                            
                            if href and texto:
                                # FILTRAR: Solo enlaces que NO sean de paginación
                                if self._es_link_licitacion_valido(href, texto):
                                    # Buscar número de proceso en la fila
                                    texto_fila = await fila.text_content()
                                    numeros_proceso = re.findall(r'\b\d{2,}/\d{2,}-\d+\b|\b\d+[-/]\d+\b|\b\w+\d+-\w+\d+\b', texto_fila)
                                    
                                    link_info = {
                                        'url': self.build_full_url(href),
                                        'texto': texto.strip(),
                                        'numero_proceso': numeros_proceso[0] if numeros_proceso else ''
                                    }
                                    
                                    # Evitar duplicados en la misma página
                                    if not any(l['url'] == link_info['url'] for l in links):
                                        links.append(link_info)
                    
                    break  # Usar solo la primera tabla significativa
            
            return links
            
        except Exception as e:
            print(f"⚠️  Error extrayendo links: {e}")
            return links
    
    def _es_link_licitacion_valido(self, href, texto):
        """Determinar si un link es una licitación válida (no paginación)"""
        # Excluir links de paginación
        if 'Page$' in href:
            return False
        
        # Excluir números simples (1, 2, 3, etc.) que son paginación
        if texto.strip().isdigit() and len(texto.strip()) <= 3:
            return False
        
        # Excluir "..." que es paginación
        if texto.strip() in ['...', '......', '>>>', '<<<']:
            return False
        
        # Incluir solo links que contengan referencias a procesos
        if 'lnkNumeroProceso' in href:
            return True
        
        # Incluir links que tengan formato de número de proceso
        if re.search(r'\d+[-/]\d+', texto):
            return True
        
        return False
    
    async def _ir_a_siguiente_pagina(self):
        """Navegar a la siguiente página del paginador"""
        try:
            # Obtener información de página actual
            pagina_actual = await self._obtener_pagina_actual()
            
            # MÉTODO 1: Buscar botón ">" o "»" 
            selectores_siguiente = [
                'a:has-text(">")',
                'a:has-text("»")',
                'text=">"',
                'text="»"'
            ]
            
            for selector in selectores_siguiente:
                try:
                    elemento = await self.page.query_selector(selector)
                    if elemento:
                        href = await elemento.get_attribute('href') or ""
                        clase = await elemento.get_attribute('class') or ""
                        
                        # Verificar que no esté deshabilitado y tenga href válido
                        if href and 'disabled' not in clase.lower():
                            print(f"      🔄 Navegando con botón >")
                            await elemento.click()
                            await self.page.wait_for_timeout(3000)
                            return True
                except:
                    continue
            
            # MÉTODO 2: Buscar siguiente número de página específico
            siguiente_pagina = pagina_actual + 1
            
            # Buscar enlace con el número exacto de la siguiente página
            enlace_siguiente_numero = await self.page.query_selector(f'a:has-text("{siguiente_pagina}")')
            
            if enlace_siguiente_numero:
                href = await enlace_siguiente_numero.get_attribute('href') or ""
                if 'Page$' in href:
                    print(f"      🔄 Navegando con número de página {siguiente_pagina}")
                    await enlace_siguiente_numero.click()
                    await self.page.wait_for_timeout(3000)
                    return True
            
            # MÉTODO 3: Buscar enlaces de paginación por postback más sistemático
            enlaces_paginacion = await self.page.query_selector_all('a[href*="Page$"]')
            print(f"      📊 DEBUG: Encontrados {len(enlaces_paginacion)} enlaces con Page$")
            
            for i, enlace in enumerate(enlaces_paginacion):
                href = await enlace.get_attribute('href') or ""
                texto = await enlace.text_content() or ""
                
                if 'Page$' in href:
                    # Extraer número de página
                    match = re.search(r'Page\$(\d+)', href)
                    if match:
                        num_pagina = int(match.group(1))
                        print(f"      📄 DEBUG: Enlace {i+1}: '{texto}' -> página {num_pagina}")
                        
                        # Si es la siguiente página
                        if num_pagina == siguiente_pagina:
                            print(f"      🔄 Navegando a página {num_pagina} con postback")
                            await enlace.click()
                            await self.page.wait_for_timeout(3000)
                            return True
            
            # MÉTODO 4: JavaScript directo con nombres de control detectados automáticamente
            try:
                # Buscar controles de GridView en la página
                contenido = await self.page.content()
                controles_grid = re.findall(r'(ctl00\$CPH1\$[^"\']*Grid[^"\']*)', contenido)
                controles_unicos = list(set(controles_grid))
                
                print(f"      🔍 DEBUG: Controles Grid detectados: {controles_unicos}")
                
                for control in controles_unicos:
                    try:
                        script = f"__doPostBack('{control}', 'Page${siguiente_pagina}');"
                        print(f"      🔄 Probando JS: {script}")
                        
                        await self.page.evaluate(script)
                        await self.page.wait_for_timeout(3000)
                        
                        # Verificar si cambió la página
                        nueva_pagina = await self._obtener_pagina_actual()
                        print(f"      📄 DEBUG: Después de JS, página: {nueva_pagina}")
                        
                        if nueva_pagina > pagina_actual:
                            print(f"      ✅ Navegado con JS a página {nueva_pagina}")
                            return True
                    except Exception as e:
                        print(f"      ❌ Error con control {control}: {e}")
                        continue
                        
            except Exception as e:
                print(f"      ❌ Error en método JS: {e}")
            
            print("      ❌ DEBUG: Todos los métodos fallaron")
            return False
            
        except Exception as e:
            print(f"⚠️  Error navegando a siguiente: {e}")
            return False
    
    async def _obtener_pagina_actual(self):
        """Obtener el número de página actual"""
        try:
            # MÉTODO 1: Buscar elementos con estilos que indiquen página actual
            selectores_pagina_actual = [
                'span[style*="font-weight:bold"]',
                'span[style*="font-weight: bold"]', 
                '.current',
                '.active',
                '.selected',
                'span[style*="color:"]'  # En ASP.NET a veces colorea la página actual
            ]
            
            for selector in selectores_pagina_actual:
                elementos = await self.page.query_selector_all(selector)
                for elemento in elementos:
                    texto = await elemento.text_content() or ""
                    # Verificar si es un número y está en contexto de paginación
                    if texto.strip().isdigit():
                        # Verificar que el elemento esté cerca de otros elementos de paginación
                        parent = await elemento.query_selector('..')
                        if parent:
                            hermanos = await parent.query_selector_all('a, span')
                            textos_hermanos = []
                            for hermano in hermanos:
                                texto_hermano = await hermano.text_content() or ""
                                textos_hermanos.append(texto_hermano.strip())
                            
                            # Si hay otros números cerca, es probablemente paginación
                            otros_numeros = [t for t in textos_hermanos if t.isdigit()]
                            if len(otros_numeros) >= 2:  # Al menos 2 números = paginación
                                pagina = int(texto.strip())
                                print(f"      📄 DEBUG: Página actual detectada por estilo: {pagina}")
                                return pagina
            
            # MÉTODO 2: Analizar el URL actual o viewstate para información de página
            try:
                url_actual = self.page.url
                if 'Page$' in url_actual:
                    match = re.search(r'Page\$(\d+)', url_actual)
                    if match:
                        pagina = int(match.group(1))
                        print(f"      📄 DEBUG: Página actual detectada por URL: {pagina}")
                        return pagina
            except:
                pass
            
            # MÉTODO 3: Buscar en el viewstate o controles hidden
            try:
                contenido = await self.page.content()
                
                # Buscar viewstate que contiene información de página
                viewstate_match = re.search(r'__VIEWSTATE[^>]*value="([^"]*)"', contenido)
                if viewstate_match:
                    # En ASP.NET el viewstate a veces contiene info de paginación
                    # pero es complejo decodificar, intentemos otro método
                    pass
                
                # Buscar patrones de JavaScript que indiquen página actual
                js_patterns = [
                    r"Page\$(\d+)['\"]?\s*,\s*['\"]?\s*true",  # Página actual marcada como true
                    r"currentPage['\"]?\s*:\s*['\"]?(\d+)"     # Variable currentPage
                ]
                
                for pattern in js_patterns:
                    matches = re.findall(pattern, contenido)
                    if matches:
                        pagina = int(matches[0])
                        print(f"      📄 DEBUG: Página actual detectada por JS: {pagina}")
                        return pagina
                        
            except:
                pass
            
            # MÉTODO 4: Buscar span sin link (página actual no es link)
            try:
                # En muchos paginadores ASP.NET, la página actual es un span, las otras son links
                todos_elementos_pag = await self.page.query_selector_all('table td span, table td a')
                
                numeros_encontrados = []
                for elem in todos_elementos_pag:
                    texto = await elem.text_content() or ""
                    tag_name = await elem.evaluate('el => el.tagName.toLowerCase()')
                    href = await elem.get_attribute('href') or ""
                    
                    if texto.strip().isdigit():
                        numeros_encontrados.append({
                            'numero': int(texto.strip()),
                            'es_link': tag_name == 'a' and href,
                            'texto': texto.strip()
                        })
                
                # Si hay varios números, el que NO es link probablemente es la página actual
                if len(numeros_encontrados) > 1:
                    nums_no_link = [n for n in numeros_encontrados if not n['es_link']]
                    if nums_no_link:
                        pagina = nums_no_link[0]['numero']
                        print(f"      📄 DEBUG: Página actual detectada por span sin link: {pagina}")
                        return pagina
                        
            except:
                pass
            
            # Si no se encuentra nada, asumir página 1
            print(f"      📄 DEBUG: No se pudo detectar página actual, asumiendo 1")
            return 1
            
        except Exception as e:
            print(f"      ❌ Error detectando página actual: {e}")
            return 1
    
    async def _hay_siguiente_pagina(self):
        """Verificar si hay una siguiente página disponible"""
        try:
            # MÉTODO 1: Verificar botón ">" o "»" habilitado
            selectores_siguiente = [
                'a:has-text(">")',
                'a:has-text("»")'
            ]
            
            for selector in selectores_siguiente:
                try:
                    elemento = await self.page.query_selector(selector)
                    if elemento:
                        # Verificar si no está deshabilitado
                        clase = await elemento.get_attribute('class') or ""
                        href = await elemento.get_attribute('href') or ""
                        
                        # Si tiene href y no está disabled, hay siguiente página
                        if href and 'disabled' not in clase.lower():
                            return True
                except:
                    continue
            
            # MÉTODO 2: Verificar números de página disponibles
            pagina_actual = await self._obtener_pagina_actual()
            
            # Buscar enlaces de páginas con números mayores
            enlaces_paginacion = await self.page.query_selector_all('a[href*="Page$"]')
            
            for enlace in enlaces_paginacion:
                try:
                    href = await enlace.get_attribute('href')
                    if href and 'Page$' in href:
                        match = re.search(r'Page\$(\d+)', href)
                        if match:
                            num_pagina = int(match.group(1))
                            if num_pagina > pagina_actual:
                                return True
                except:
                    continue
            
            # MÉTODO 3: Buscar texto que indique páginas (ej: "Página 1 de 57")
            try:
                contenido_pagina = await self.page.content()
                
                # Patrones comunes de paginación
                patrones = [
                    r'Página\s+(\d+)\s+de\s+(\d+)',
                    r'Page\s+(\d+)\s+of\s+(\d+)',
                    r'(\d+)\s+de\s+(\d+)',
                    r'(\d+)\s+/\s+(\d+)'
                ]
                
                for patron in patrones:
                    matches = re.findall(patron, contenido_pagina)
                    for match in matches:
                        pagina_actual_texto = int(match[0])
                        total_paginas = int(match[1])
                        
                        if pagina_actual_texto < total_paginas:
                            print(f"      📄 Encontrado: página {pagina_actual_texto} de {total_paginas}")
                            return True
                            
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"⚠️  Error verificando siguiente página: {e}")
            return False
    
    def _mostrar_resumen_recoleccion(self, resultado):
        """Mostrar resumen de la recolección"""
        print(f"\n📊 RESUMEN DE RECOLECCIÓN DE LINKS")
        print("=" * 60)
        
        metadata = resultado['metadata']
        
        print(f"✅ Links próxima apertura: {len(resultado['links_proxima_apertura'])}")
        print(f"   📄 Páginas navegadas: {metadata['total_paginas_proxima']}")
        
        print(f"✅ Links últimos 30 días: {len(resultado['links_ultimos_30_dias'])}")
        print(f"   📄 Páginas navegadas: {metadata['total_paginas_30_dias']}")
        
        print(f"🎯 TOTAL LINKS RECOLECTADOS: {metadata['total_links']}")
        print(f"📅 Fecha extracción: {metadata['fecha_extraccion']}")
        
        # Mostrar algunos ejemplos
        if resultado['links_proxima_apertura']:
            print(f"\n🔗 EJEMPLOS PRÓXIMA APERTURA:")
            for i, link in enumerate(resultado['links_proxima_apertura'][:3], 1):
                print(f"   {i}. {link['numero_proceso']} - {link['texto'][:50]}...")
        
        if resultado['links_ultimos_30_dias']:
            print(f"\n🔗 EJEMPLOS ÚLTIMOS 30 DÍAS:")
            for i, link in enumerate(resultado['links_ultimos_30_dias'][:3], 1):
                print(f"   {i}. {link['numero_proceso']} - {link['texto'][:50]}...")

async def main():
    print("🚀 FUNCIÓN 1: RECOLECCIÓN MASIVA DE LINKS")
    print("=" * 50)
    
    recolector = RecolectorLinks(headless=False)
    
    try:
        await recolector.start_browser()
        resultado = await recolector.recolectar_todos_los_links()
        
        print(f"\n🎉 ¡RECOLECCIÓN COMPLETADA!")
        print(f"Total de links recolectados: {resultado['metadata']['total_links']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await recolector.close_browser()

if __name__ == "__main__":
    asyncio.run(main())