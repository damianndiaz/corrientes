-- Tabla principal de ejecuciones del scraper
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    total_pages INTEGER DEFAULT 0,
    execution_time_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de detalles de cada ejecución (metadatos del scraping)
CREATE TABLE IF NOT EXISTS run_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    url_principal VARCHAR(500) NOT NULL,
    numero_paginas INTEGER NOT NULL,
    total_licitaciones INTEGER NOT NULL,
    urls_paginas TEXT, -- JSON con todas las URLs de paginación
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

-- Tabla principal de licitaciones
CREATE TABLE IF NOT EXISTS licitaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    numero_licitacion VARCHAR(100),
    estado VARCHAR(50),
    fecha_publicacion DATE,
    fecha_apertura DATE,
    monto_estimado DECIMAL(15,2),
    moneda VARCHAR(10) DEFAULT 'ARS',
    organismo VARCHAR(200),
    categoria VARCHAR(100),
    subcategoria VARCHAR(100),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

-- Tabla de archivos HTML descargados
CREATE TABLE IF NOT EXISTS archivos_html (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    licitacion_id INTEGER NOT NULL,
    path_relativo VARCHAR(500) NOT NULL,
    path_absoluto VARCHAR(1000),
    tamano_bytes INTEGER,
    hash_md5 VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (licitacion_id) REFERENCES licitaciones(id) ON DELETE CASCADE
);

-- Tabla de screenshots PNG
CREATE TABLE IF NOT EXISTS archivos_png (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    licitacion_id INTEGER NOT NULL,
    path_relativo VARCHAR(500) NOT NULL,
    path_absoluto VARCHAR(1000),
    tamano_bytes INTEGER,
    ancho_pixeles INTEGER,
    alto_pixeles INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (licitacion_id) REFERENCES archivos_html(id) ON DELETE CASCADE
);

-- Tabla de errores durante el scraping
CREATE TABLE IF NOT EXISTS scraping_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    url VARCHAR(1000),
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

-- Tabla de métricas por ejecución
CREATE TABLE IF NOT EXISTS metricas_ejecucion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    paginas_procesadas INTEGER DEFAULT 0,
    paginas_exitosas INTEGER DEFAULT 0,
    paginas_con_error INTEGER DEFAULT 0,
    archivos_html_creados INTEGER DEFAULT 0,
    archivos_png_creados INTEGER DEFAULT 0,
    tiempo_step1_seconds INTEGER DEFAULT 0,
    tiempo_step2_seconds INTEGER DEFAULT 0,
    tiempo_step3_seconds INTEGER DEFAULT 0,
    memoria_maxima_mb INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);


-- Índices para consultas frecuentes por fechas
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_licitaciones_scraped_at ON licitaciones(scraped_at);
CREATE INDEX IF NOT EXISTS idx_licitaciones_fecha_publicacion ON licitaciones(fecha_publicacion);

-- Índices para búsquedas por URL y estado
CREATE INDEX IF NOT EXISTS idx_licitaciones_url ON licitaciones(url);
CREATE INDEX IF NOT EXISTS idx_licitaciones_estado ON licitaciones(estado);

-- Índice único compuesto para evitar duplicados por run
CREATE UNIQUE INDEX IF NOT EXISTS idx_licitaciones_run_url ON licitaciones(run_id, url);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);

-- Índices para relaciones entre tablas
CREATE INDEX IF NOT EXISTS idx_run_details_run_id ON run_details(run_id);
CREATE INDEX IF NOT EXISTS idx_licitaciones_run_id ON licitaciones(run_id);
CREATE INDEX IF NOT EXISTS idx_archivos_html_licitacion_id ON archivos_html(licitacion_id);
CREATE INDEX IF NOT EXISTS idx_archivos_png_licitacion_id ON archivos_png(licitacion_id);
CREATE INDEX IF NOT EXISTS idx_scraping_errors_run_id ON scraping_errors(run_id);
CREATE INDEX IF NOT EXISTS idx_metricas_run_id ON metricas_ejecucion(run_id);

-- =============================================================================
-- TRIGGERS PARA ACTUALIZACIÓN AUTOMÁTICA DE TIMESTAMPS
-- =============================================================================

-- Trigger para actualizar updated_at en tabla runs
CREATE TRIGGER IF NOT EXISTS update_runs_timestamp 
    AFTER UPDATE ON runs
    FOR EACH ROW
    BEGIN
        UPDATE runs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger para actualizar updated_at en tabla licitaciones
CREATE TRIGGER IF NOT EXISTS update_licitaciones_timestamp 
    AFTER UPDATE ON licitaciones
    FOR EACH ROW
    BEGIN
        UPDATE licitaciones SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Vista con información completa de licitaciones y sus archivos
CREATE VIEW IF NOT EXISTS v_licitaciones_completas AS
SELECT 
    l.id,
    l.url,
    l.title,
    l.numero_licitacion,
    l.estado,
    l.fecha_publicacion,
    l.fecha_apertura,
    l.monto_estimado,
    l.organismo,
    l.categoria,
    r.started_at as run_fecha,
    ah.path_relativo as html_path,
    ap.path_relativo as png_path,
    l.scraped_at
FROM licitaciones l
LEFT JOIN runs r ON l.run_id = r.id
LEFT JOIN archivos_html ah ON l.id = ah.licitacion_id
LEFT JOIN archivos_png ap ON l.id = ap.licitacion_id
ORDER BY l.scraped_at DESC;

-- Vista de estadísticas por ejecución
CREATE VIEW IF NOT EXISTS v_estadisticas_runs AS
SELECT 
    r.id,
    r.started_at,
    r.finished_at,
    r.status,
    r.execution_time_seconds,
    COUNT(l.id) as total_licitaciones,
    COUNT(ah.id) as total_html_files,
    COUNT(ap.id) as total_png_files,
    COUNT(se.id) as total_errors
FROM runs r
LEFT JOIN licitaciones l ON r.id = l.run_id
LEFT JOIN archivos_html ah ON l.id = ah.licitacion_id
LEFT JOIN archivos_png ap ON l.id = ap.licitacion_id
LEFT JOIN scraping_errors se ON r.id = se.run_id
GROUP BY r.id, r.started_at, r.finished_at, r.status, r.execution_time_seconds
ORDER BY r.started_at DESC;