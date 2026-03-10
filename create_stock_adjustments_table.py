"""
Script de migración: Crear tabla stock_ajustes
Ejecutar manualmente con: python create_stock_adjustments_table.py
"""
import sqlite3
import os

# Ruta a la base de datos SQLite
DB_PATH = "sql_app.db"

def run_migration():
    """Crear la tabla stock_ajustes si no existe."""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró la base de datos: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar si la tabla ya existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='stock_ajustes'
    """)
    
    if cursor.fetchone():
        print("✅ La tabla stock_ajustes ya existe.")
        conn.close()
        return True
    
    # Crear la tabla
    create_sql = """
    CREATE TABLE stock_ajustes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lubricentro_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        tipo_ajuste VARCHAR NOT NULL,
        cantidad FLOAT NOT NULL,
        motivo TEXT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        created_by INTEGER,
        
        FOREIGN KEY (lubricentro_id) REFERENCES lubricentros (id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES stock_productos (id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES usuarios (id) ON DELETE SET NULL
    )
    """
    
    try:
        cursor.execute(create_sql)
        
        # Crear índices para mejor rendimiento
        cursor.execute("CREATE INDEX idx_stock_ajustes_lubricentro ON stock_ajustes (lubricentro_id)")
        cursor.execute("CREATE INDEX idx_stock_ajustes_producto ON stock_ajustes (producto_id)")
        cursor.execute("CREATE INDEX idx_stock_ajustes_fecha ON stock_ajustes (lubricentro_id, fecha)")
        
        conn.commit()
        print("✅ Tabla stock_ajustes creada correctamente.")
        print("✅ Índices creados.")
        return True
        
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Migración: Crear tabla stock_ajustes")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        print("\n🎉 Migración completada exitosamente!")
    else:
        print("\n⚠️ Hubo problemas con la migración.")
