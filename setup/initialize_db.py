#!/usr/bin/env python3
import sqlite3
import os
import sys
from pathlib import Path


def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    current_file = Path(__file__)
    # El archivo está en setup/, así que subimos un nivel
    return current_file.parent.parent


def read_schema_sql(schema_path):
    """Lee el contenido del archivo schema.sql"""
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {schema_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al leer schema.sql: {e}")
        sys.exit(1)


def initialize_database(db_path, schema_content):
    """Inicializa la base de datos SQLite con el esquema"""
    try:
        # Crear directorio si no existe
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Conectar a la base de datos (se crea si no existe)
        print(f"📦 Conectando a la base de datos: {db_path}")
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Habilitar foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Ejecutar el esquema completo
        print("🔨 Ejecutando schema.sql...")
        cursor.executescript(schema_content)
        
        # Confirmar cambios
        connection.commit()
        
        # Verificar que las tablas se crearon correctamente
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Base de datos inicializada correctamente!")
        print(f"📋 Tablas creadas: {len(tables)}")
        
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verificar vistas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='view'
            ORDER BY name;
        """)
        
        views = cursor.fetchall()
        if views:
            print(f"👁️  Vistas creadas: {len(views)}")
            for view in views:
                print(f"   - {view[0]}")
        
        # Verificar índices
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        
        indexes = cursor.fetchall()
        if indexes:
            print(f"🗂️  Índices creados: {len(indexes)}")
            for index in indexes:
                print(f"   - {index[0]}")
        
        # Cerrar conexión
        connection.close()
        
        # Mostrar información del archivo
        db_file = Path(db_path)
        if db_file.exists():
            size_bytes = db_file.stat().st_size
            size_kb = size_bytes / 1024
            print(f"💾 Tamaño de la base de datos: {size_kb:.1f} KB")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error de SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def verify_database_integrity(db_path):
    """Verifica la integridad de la base de datos creada"""
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        print("🔍 Verificando integridad de la base de datos...")
        
        # Verificar integridad
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            print("✅ Integridad de la base de datos: OK")
        else:
            print(f"⚠️  Problema de integridad: {result[0]}")
        
        # Verificar configuración de foreign keys
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        print(f"🔗 Foreign Keys: {'Habilitadas' if fk_status else 'Deshabilitadas'}")
        
        # Verificar versión de SQLite
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()[0]
        print(f"📊 Versión de SQLite: {version}")
        
        connection.close()
        
    except Exception as e:
        print(f"⚠️  Error al verificar integridad: {e}")


def main():
    """Función principal"""
    print("🚀 INICIALIZADOR DE BASE DE DATOS SQLITE")
    print("=" * 50)
    
    # Obtener rutas
    project_root = get_project_root()
    schema_path = project_root / "db" / "schema.sql"
    db_path = project_root / "db" / "licitar.db"
    
    print(f"📁 Directorio del proyecto: {project_root}")
    print(f"📄 Archivo de esquema: {schema_path}")
    print(f"🗃️  Base de datos: {db_path}")
    print()
    
    # Verificar si ya existe la base de datos
    if db_path.exists():
        response = input("⚠️  La base de datos ya existe. ¿Deseas recrearla? (s/N): ")
        if response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada.")
            sys.exit(0)
        else:
            print("🗑️  Eliminando base de datos existente...")
            os.remove(db_path)
    
    # Leer esquema
    schema_content = read_schema_sql(schema_path)
    
    # Inicializar base de datos
    success = initialize_database(db_path, schema_content)
    
    if success:
        # Verificar integridad
        verify_database_integrity(db_path)
        
        print()
        print("🎉 ¡BASE DE DATOS INICIALIZADA EXITOSAMENTE!")
        print(f"📍 Ubicación: {db_path.absolute()}")
        print()
        print("💡 Próximos pasos:")
        print("   1. Modificar step3.py para usar SQLite en lugar de JSONL")
        print("   2. Crear funciones de consulta y reporting")
        print("   3. Implementar migración de datos existentes")
        
    else:
        print("❌ Error al inicializar la base de datos")
        sys.exit(1)


if __name__ == "__main__":
    main()