import asyncio
import json
import re
from datetime import datetime
from base_scraper import BaseScraper

class ExtractorDataCompleta(BaseScraper):
    def __init__(self, headless=True):
        super().__init__(headless)
        self.contador_procesados = 0
        self.contador_exitosos = 0
        self.contador_errores = 0
    
    async def extraer_data_completa(self, archivo_links=None):
        print("\n📊 FUNCIÓN 2: EXTRAYENDO DATA COMPLETA DE LICITACIONES")
        print("=" * 80)
        
    async def extraer_data_completa(self, archivo_links=None, start_from=0, load_progress=None):
        links_data = self._cargar_links(archivo_links)
        
        if not links_data:
            print("❌ No se pudieron cargar los links. Ejecuta primero la Función 1.")
            return None
        
        # Cargar progreso previo si existe
        if load_progress:
            try:
                with open(load_progress, 'r', encoding='utf-8') as f:
                    resultado_completo = json.load(f)
                print(f"✅ Cargado progreso previo desde: {load_progress}")
                print(f"   📊 Licitaciones ya procesadas: {len(resultado_completo['licitaciones_completas'])}")
            except Exception as e:
                print(f"⚠️  Error cargando progreso: {e}")
                resultado_completo = {
                    'licitaciones_completas': [],
                    'estadisticas': {
                        'total_links_procesados': 0,
                        'total_extracciones_exitosas': 0,
                        'total_errores': 0,
                        'fecha_procesamiento': datetime.now().isoformat()
                    },
                    'errores_detallados': []
                }
        else:
            resultado_completo = {
                'licitaciones_completas': [],
                'estadisticas': {
                    'total_links_procesados': 0,
                    'total_extracciones_exitosas': 0,
                    'total_errores': 0,
                    'fecha_procesamiento': datetime.now().isoformat()
                },
                'errores_detallados': []
            }
        
        try:
            # Combinar todos los links
            todos_los_links = links_data.get('links_proxima_apertura', []) + links_data.get('links_ultimos_30_dias', [])
            
            print(f"📋 Total de links a procesar: {len(todos_los_links)}")
            
            # Procesar cada link individualmente
            await self._procesar_todos_los_links(todos_los_links, resultado_completo, start_from)
            
            # Generar estadísticas finales
            self._generar_estadisticas_finales(resultado_completo)
            
            # Guardar resultado
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_json(resultado_completo, f'funcion2_data_completa_{timestamp}.json')
            
            # Exportar a CSV para análisis
            self._exportar_a_csv(resultado_completo, f'licitaciones_completas_{timestamp}.csv')
            
            self._mostrar_resumen_final(resultado_completo)
            
            return resultado_completo
            
        except Exception as e:
            print(f"❌ Error en procesamiento completo: {e}")
            return resultado_completo
    
    def _cargar_links(self, archivo_links=None):
        try:
            archivo = archivo_links or 'funcion1_todos_los_links.json'
            
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ Cargados links desde: {archivo}")
            return data
            
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {archivo}")
            print("💡 Ejecuta primero la Función 1 para generar los links")
            return None
        except Exception as e:
            print(f"❌ Error cargando links: {e}")
            return None
    
    async def _procesar_todos_los_links(self, links, resultado_completo, start_from=0):
        total_links = len(links)
        
        if start_from > 0:
            print(f"🔄 REANUDANDO desde licitación {start_from + 1} de {total_links}")
            links = links[start_from:]
            print(f"📋 Links restantes a procesar: {len(links)}")
        
        print(f"🚀 Iniciando procesamiento de {len(links)} links...")
        print(f"⏱️  Tiempo estimado: {(len(links) * 3) // 60} minutos")
        
        for i, link_info in enumerate(links, start_from + 1):
            self.contador_procesados += 1
            
            # Mostrar progreso cada 50 links para no saturar la consola
            if i % 50 == 0 or i <= 10 or i == total_links:
                print(f"\n� PROGRESO: [{i:4d}/{total_links}] ({(i/total_links)*100:.1f}%)")
                print(f"   ✅ Exitosos: {self.contador_exitosos} | ❌ Errores: {self.contador_errores}")
            
            # Mostrar detalles solo para los primeros 5
            if i <= 5:
                print(f"\n🔍 [{i:4d}] Procesando: {link_info.get('numero_proceso', 'N/A')}")
                print(f"   📄 Texto: {link_info.get('texto', '')[:60]}...")
            
            try:
                # Extraer data con reintentos
                data_licitacion = await self._extraer_con_reintentos(link_info)
                
                if data_licitacion:
                    resultado_completo['licitaciones_completas'].append(data_licitacion)
                    self.contador_exitosos += 1
                    if i <= 10:  # Solo mostrar detalles para los primeros
                        print(f"   ✅ Exitoso")
                else:
                    self.contador_errores += 1
                    if i <= 10:
                        print(f"   ⚠️  Sin data extraída")
                
                # Pausa cada 25 requests para no sobrecargar
                if i % 25 == 0:
                    await asyncio.sleep(1)
                
                # Guardar progreso cada 100 links
                if i % 100 == 0:
                    await self._guardar_progreso_parcial(resultado_completo, i)
                
            except Exception as e:
                self.contador_errores += 1
                error_info = {
                    'link': link_info['url'],
                    'numero_proceso': link_info.get('numero_proceso', ''),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                resultado_completo['errores_detallados'].append(error_info)
                print(f"   ❌ Error: {str(e)[:50]}...")
        
        # Actualizar estadísticas
        resultado_completo['estadisticas']['total_links_procesados'] = self.contador_procesados
        resultado_completo['estadisticas']['total_extracciones_exitosas'] = self.contador_exitosos
        resultado_completo['estadisticas']['total_errores'] = self.contador_errores
        
        print(f"\n🏁 PROCESAMIENTO COMPLETADO!")
        print(f"📊 Resumen: {self.contador_exitosos} exitosos, {self.contador_errores} errores")
    
    async def _extraer_con_reintentos(self, link_info, max_reintentos=2):
        for intento in range(max_reintentos + 1):
            try:
                return await self._extraer_data_licitacion_individual(link_info)
            except Exception as e:
                if intento < max_reintentos:
                    await asyncio.sleep(1)  # Pausa antes del reintento
                    continue
                else:
                    raise e
    
    async def _guardar_progreso_parcial(self, resultado, procesados):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_temp = f'funcion2_progreso_{procesados}_{timestamp}.json'
        self.save_json(resultado, archivo_temp)
        print(f"   💾 Progreso guardado: {archivo_temp}")
    
    async def _extraer_data_licitacion_individual(self, link_info):
        try:
            # Los links son JavaScript postbacks, necesitamos ejecutarlos desde la página correcta
            success = await self._navegar_a_licitacion_postback(link_info)
            
            if not success:
                print(f"   ❌ No se pudo navegar a la licitación")
                return None
            
            # Estructura base de la licitación
            licitacion = {
                'metadata': {
                    'url_origen': link_info['url'],
                    'numero_proceso_original': link_info.get('numero_proceso', ''),
                    'texto_original': link_info.get('texto', ''),
                    'tipo_origen': link_info.get('tipo_origen', ''),
                    'pagina_origen': link_info.get('pagina', 0),
                    'timestamp_extraccion': datetime.now().isoformat()
                },
                'datos_basicos': {},
                'informacion_detallada': {},
                'documentos': [],
                'fechas_importantes': {},
                'informacion_contacto': {},
                'observaciones': []
            }
            
            # Extraer diferentes secciones de información
            await self._extraer_datos_basicos(licitacion)
            await self._extraer_informacion_detallada(licitacion)
            await self._extraer_documentos(licitacion)
            await self._extraer_fechas_importantes(licitacion)
            await self._extraer_informacion_contacto(licitacion)
            
            return licitacion
            
        except Exception as e:
            print(f"      ❌ Error extrayendo licitación: {e}")
            return None
    
    async def _extraer_datos_basicos(self, licitacion):
        """Extraer datos usando método robusto del debug - SIN consultar elementos del DOM"""
        try:
            # Esperar estabilización como en debug exitoso
            await self.page.wait_for_timeout(3000)
            
            # Obtener TODO el HTML de una vez (evita errores de DOM)
            html_completo = await self.page.content()
            
            # Verificar que tenemos la sección correcta
            if 'Información básica del proceso' not in html_completo:
                print(f"      ❌ No se encontró 'Información básica del proceso' en el HTML")
                return
            
            print(f"      ✅ Encontrado: 'Información básica del proceso'")
            
            # Extraer texto limpio del HTML (sin parsear DOM)
            # Remover tags HTML manualmente
            texto_limpio = re.sub(r'<[^>]+>', '\n', html_completo)
            texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
            texto_completo = texto_limpio
            
            # Campos a extraer
            campos_a_extraer = {
                'numero_proceso': ['Número de proceso', 'N° de proceso'],
                'numero_expediente': ['Número de expediente'],
                'nombre_descriptivo': ['Nombre descriptivo del proceso'],
                'unidad_operativa': ['Unidad Operativa de Contrataciones'],
                'estado': ['Estado'],
                'modalidad': ['Modalidad'],
                'tipo_contratacion': ['Tipo de contratación'],
                'tipo_adjudicacion': ['Tipo de adjudicación'],
                'encuadre_legal': ['Encuadre legal'],
                'objeto_contratacion': ['Objeto de la contratación'],
                'lugar_recepcion': ['Lugar de recepción de documentación física'],
                'requiere_pago': ['Requiere pago'],
                'genera_recursos': ['Genera Recursos'],
                'financiamiento_externo': ['Financiamiento Externo'],
                'acepta_prorroga': ['Acepta prórroga']
            }
                
            # Buscar cada campo con patrón que se detiene en próximo campo
            for campo_clave, posibles_etiquetas in campos_a_extraer.items():
                for etiqueta in posibles_etiquetas:
                    try:
                        # Patrón: "Etiqueta" + valor hasta encontrar otra etiqueta conocida
                        patron = re.escape(etiqueta) + r'\s*([^\n]+?)(?=(?:Número de|Nombre descriptivo|Unidad Operativa|Estado|Modalidad|Tipo de|Encuadre legal|Objeto de|Lugar de|Requiere|Genera|Financiamiento|Acepta|$))'
                        match = re.search(patron, texto_completo, re.IGNORECASE)
                        
                        if match:
                            valor = match.group(1).strip()
                            # Limpiar HTML, espacios y separadores
                            valor = re.sub(r'&nbsp;', ' ', valor)
                            valor = re.sub(r'\s+', ' ', valor).strip()
                            valor = valor.strip(':').strip()
                            
                            if valor and len(valor) > 1 and not valor.isspace():
                                licitacion['datos_basicos'][campo_clave] = valor
                                preview = valor[:60] + '...' if len(valor) > 60 else valor
                                print(f"      📋 {campo_clave}: {preview}")
                                break
                                
                    except Exception as ex:
                        continue
            
            print(f"      ✅ Extraídos {len(licitacion['datos_basicos'])} campos básicos")
            
        except Exception as e:
            print(f"      ⚠️  Error extrayendo datos básicos: {e}")
    
    async def _navegar_a_licitacion_postback(self, link_info):
        """Método simplificado: ir al listado y ejecutar postback directamente"""
        try:
            tipo_origen = link_info.get('tipo_origen', '')
            url = link_info['url']
            
            print(f"      🌐 Navegando al listado: {tipo_origen}")
            
            # Ir al listado correcto
            if tipo_origen == 'proxima_apertura':
                success = await self._ir_a_listado_proxima_apertura()
            else:
                success = await self._ir_a_listado_30_dias()
            
            if not success:
                print(f"      ❌ No se pudo llegar al listado")
                return False
            
            # Extraer y ejecutar postback desde URL
            if 'javascript:__doPostBack' in url:
                match = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", url)
                if match:
                    target = match.group(1)
                    argument = match.group(2)
                    
                    print(f"      🔧 Ejecutando postback: {target}")
                    script = f"__doPostBack('{target}', '{argument}');"
                    await self.page.evaluate(script)
                    await self.page.wait_for_timeout(5000)  # Esperar navegación
                    
                    # Verificar navegación exitosa
                    url_final = self.page.url
                    if 'VistaPreviaPliegoCiudadano' in url_final or 'PliegoCiudadano' in url_final:
                        print(f"      ✅ Navegación exitosa a: {url_final[:80]}...")
                        return True
                    else:
                        print(f"      ⚠️  URL inesperada: {url_final[:80]}...")
                        return False
            else:
                print(f"      ❌ URL no contiene postback válido")
                return False
            
        except Exception as e:
            print(f"      ❌ Error navegando: {str(e)[:100]}")
            return False
    
    async def _ir_a_listado_proxima_apertura(self):
        """Ir al listado de próxima apertura con manejo robusto de elementos dinámicos"""
        try:
            await self.navigate_to_main_page()
            await self.page.wait_for_timeout(2000)  # Esperar más tiempo
            
            # Buscar botón de próxima apertura
            boton_proxima = await self.page.query_selector('text=/Procesos con apertura próxima/i')
            
            if boton_proxima:
                await boton_proxima.click()
                await self.page.wait_for_timeout(3000)  # Esperar como en debug exitoso
                
                # Re-buscar "Ver todos" después del primer clic
                ver_todos_fresh = await self.page.query_selector('text=/ver todos/i')
                if ver_todos_fresh:
                    await ver_todos_fresh.click()
                    await self.page.wait_for_timeout(3000)  # Esperar estabilización
                    return True
                    
        except Exception as e:
            print(f"      ⚠️  Error navegando a próxima apertura: {e}")
            return False
        
        return False
    
    async def _ir_a_listado_30_dias(self):
        """Ir al listado de últimos 30 días con manejo robusto"""  
        try:
            await self.navigate_to_main_page()
            await self.page.wait_for_timeout(2000)
            
            # Re-buscar botón fresco para evitar DOM issues
            boton_30_dias = await self.page.query_selector('text=/últimos 30 días/i')
            
            if boton_30_dias:
                await boton_30_dias.click()
                await self.page.wait_for_timeout(3000)  # Esperar como en próxima apertura
                
                # Re-buscar "Ver todos" después del primer clic
                ver_todos_fresh = await self.page.query_selector('text=/ver todos/i')
                if ver_todos_fresh:
                    await ver_todos_fresh.click()
                    await self.page.wait_for_timeout(3000)
                    return True
                    
        except Exception as e:
            print(f"      ⚠️  Error navegando a 30 días: {e}")
            return False
        
        return False
    
    async def _extraer_informacion_detallada(self, licitacion):
        try:
            contenido = await self.page.content()
            
            # Extraer objeto de la contratación
            objetos = re.findall(r'(?:Objeto|Descripción)[:\s]*([^<\n]{20,})', contenido, re.IGNORECASE)
            if objetos:
                licitacion['informacion_detallada']['objeto'] = objetos[0].strip()
            
            # Extraer presupuesto oficial
            presupuestos = re.findall(r'(?:Presupuesto|Monto)[:\s]*\$?([0-9.,]+)', contenido, re.IGNORECASE)
            if presupuestos:
                licitacion['informacion_detallada']['presupuesto'] = presupuestos[0]
            
            # Extraer moneda
            monedas = re.findall(r'(?:Moneda)[:\s]*([A-Z]{3}|Pesos|Dólares)', contenido, re.IGNORECASE)
            if monedas:
                licitacion['informacion_detallada']['moneda'] = monedas[0]
            
            # Extraer lugar de ejecución
            lugares = re.findall(r'(?:Lugar|Localización)[:\s]*([^<\n]+)', contenido, re.IGNORECASE)
            if lugares:
                licitacion['informacion_detallada']['lugar_ejecucion'] = lugares[0].strip()
            
        except Exception as e:
            print(f"      ⚠️  Error extrayendo información detallada: {e}")
    
    async def _extraer_documentos(self, licitacion):
        """Extraer links de documentos asociados"""
        try:
            # Buscar enlaces a documentos
            enlaces_docs = await self.page.query_selector_all('a[href*=".pdf"], a[href*=".doc"], a[href*=".xls"]')
            
            for enlace in enlaces_docs:
                href = await enlace.get_attribute('href')
                texto = await enlace.text_content()
                
                if href:
                    documento = {
                        'nombre': texto.strip() if texto else 'Documento',
                        'url': self.build_full_url(href),
                        'tipo': self._determinar_tipo_documento(href)
                    }
                    licitacion['documentos'].append(documento)
            
        except Exception as e:
            print(f"      ⚠️  Error extrayendo documentos: {e}")
    
    async def _extraer_fechas_importantes(self, licitacion):
        try:
            contenido = await self.page.content()
            
            # Patrones de fechas
            patrones_fechas = {
                'fecha_apertura': r'(?:Apertura)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                'fecha_publicacion': r'(?:Publicación)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                'fecha_cierre': r'(?:Cierre|Vencimiento)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                'fecha_adjudicacion': r'(?:Adjudicación)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            }
            
            for tipo_fecha, patron in patrones_fechas.items():
                fechas = re.findall(patron, contenido, re.IGNORECASE)
                if fechas:
                    licitacion['fechas_importantes'][tipo_fecha] = fechas[0]
            
        except Exception as e:
            print(f"      ⚠️  Error extrayendo fechas: {e}")
    
    async def _extraer_informacion_contacto(self, licitacion):
        """Extraer información de contacto"""
        try:
            contenido = await self.page.content()
            
            # Extraer emails
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', contenido)
            if emails:
                licitacion['informacion_contacto']['emails'] = emails[:3]  # Máximo 3
            
            # Extraer teléfonos
            telefonos = re.findall(r'(?:Tel|Teléfono)[:\s]*([0-9\-\s\(\)]{8,})', contenido, re.IGNORECASE)
            if telefonos:
                licitacion['informacion_contacto']['telefonos'] = telefonos[:2]  # Máximo 2
            
            # Extraer direcciones
            direcciones = re.findall(r'(?:Dirección|Domicilio)[:\s]*([^<\n]{10,})', contenido, re.IGNORECASE)
            if direcciones:
                licitacion['informacion_contacto']['direcciones'] = direcciones[0].strip()
            
        except Exception as e:
            print(f"      ⚠️  Error extrayendo contacto: {e}")
    
    def _determinar_tipo_documento(self, url):
        """Determinar el tipo de documento por su extensión"""
        if '.pdf' in url.lower():
            return 'PDF'
        elif '.doc' in url.lower():
            return 'Word'
        elif '.xls' in url.lower():
            return 'Excel'
        else:
            return 'Otro'
    
    def _generar_estadisticas_finales(self, resultado_completo):
        """Generar estadísticas básicas del procesamiento"""
        # Solo mantener estadísticas básicas sin conteos detallados
        pass
    
    def _exportar_a_csv(self, resultado_completo, filename):
        """Exportar resultados a CSV para análisis"""
        try:
            import pandas as pd
            
            # Preparar datos para CSV
            datos_csv = []
            
            for lic in resultado_completo['licitaciones_completas']:
                fila = {
                    'numero_proceso': lic['datos_basicos'].get('numero_proceso', ''),
                    'titulo': lic['datos_basicos'].get('titulo', ''),
                    'tipo_proceso': lic['datos_basicos'].get('tipo_proceso', ''),
                    'organismo': lic['datos_basicos'].get('organismo', ''),
                    'estado': lic['datos_basicos'].get('estado', ''),
                    'objeto': lic['informacion_detallada'].get('objeto', ''),
                    'presupuesto': lic['informacion_detallada'].get('presupuesto', ''),
                    'fecha_apertura': lic['fechas_importantes'].get('fecha_apertura', ''),
                    'url_origen': lic['metadata']['url_origen'],
                    'cantidad_documentos': len(lic['documentos'])
                }
                datos_csv.append(fila)
            
            df = pd.DataFrame(datos_csv)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"📊 Exportado a CSV: {filename}")
            
        except Exception as e:
            print(f"⚠️  Error exportando CSV: {e}")
    
    def _mostrar_resumen_final(self, resultado_completo):
        """Mostrar resumen final del procesamiento"""
        print(f"\n📊 RESUMEN FINAL FUNCIÓN 2")
        print("=" * 70)
        
        stats = resultado_completo['estadisticas']
        
        print(f"📋 Links procesados: {stats['total_links_procesados']}")
        print(f"✅ Extracciones exitosas: {stats['total_extracciones_exitosas']}")
        print(f"❌ Errores: {stats['total_errores']}")
        
        if stats['total_links_procesados'] > 0:
            tasa_exito = (stats['total_extracciones_exitosas'] / stats['total_links_procesados']) * 100
            print(f"📈 Tasa de éxito: {tasa_exito:.1f}%")
        
        print(f"📅 Fecha procesamiento: {stats['fecha_procesamiento']}")
        
        tasa_exito = (stats['total_extracciones_exitosas'] / stats['total_links_procesados']) * 100 if stats['total_links_procesados'] > 0 else 0
        print(f"📈 Tasa de éxito: {tasa_exito:.1f}%")
        
        print(f"\n🏛️  TOP TIPOS DE PROCESO:")
        for tipo, cantidad in list(stats['tipos_de_proceso'].items())[:5]:
            print(f"   • {tipo}: {cantidad}")
        
        print(f"\n🏢 TOP ORGANISMOS:")
        for org, cantidad in list(stats['servicios_administrativos'].items())[:5]:
            print(f"   • {org[:50]}...: {cantidad}")

async def main():
    print("🚀 FUNCIÓN 2: EXTRACCIÓN DE DATA COMPLETA")
    print("=" * 50)
    
    extractor = ExtractorDataCompleta(headless=False)
    
    try:
        await extractor.start_browser()
        
        # Reanudar desde licitación 1200
        resultado = await extractor.extraer_data_completa(
            start_from=1200,
            load_progress='funcion2_progreso_1200_20251119_181218.json'
        )
        
        if resultado:
            print(f"\n🎉 ¡EXTRACCIÓN DE DATA COMPLETADA!")
            print(f"Total licitaciones procesadas: {resultado['estadisticas']['total_extracciones_exitosas']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await extractor.close_browser()

if __name__ == "__main__":
    asyncio.run(main())