"""
Script para agregar columnas es_servicio y categoria a la tabla comprobante_items
"""
import sqlite3
import os

# Ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "sql_app.db")

def add_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar si las columnas ya existen
    cursor.execute("PRAGMA table_info(comprobante_items)")
    columns = [col[1] for col in cursor.fetchall()]
    
    changes_made = False
    
    if 'es_servicio' not in columns:
        print("Agregando columna 'es_servicio'...")
        cursor.execute("ALTER TABLE comprobante_items ADD COLUMN es_servicio INTEGER DEFAULT 0")
        changes_made = True
    else:
        print("Columna 'es_servicio' ya existe")
    
    if 'categoria' not in columns:
        print("Agregando columna 'categoria'...")
        cursor.execute("ALTER TABLE comprobante_items ADD COLUMN categoria TEXT DEFAULT ''")
        changes_made = True
    else:
        print("Columna 'categoria' ya existe")
    
    if changes_made:
        conn.commit()
        print("✅ Columnas agregadas exitosamente")
    else:
        print("✅ No se requirieron cambios")
    
    # Mostrar estructura actual
    cursor.execute("PRAGMA table_info(comprobante_items)")
    print("\nEstructura actual de comprobante_items:")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    add_columns()
