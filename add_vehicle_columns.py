"""
Migración para agregar columnas marca, version, modelo, patente, kilometraje a la tabla vehiculos
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lubricentro.db")

ALTERS = [
    "ALTER TABLE vehiculos ADD COLUMN marca TEXT",
    "ALTER TABLE vehiculos ADD COLUMN version TEXT",
    "ALTER TABLE vehiculos ADD COLUMN modelo TEXT",
    "ALTER TABLE vehiculos ADD COLUMN patente TEXT",
    "ALTER TABLE vehiculos ADD COLUMN kilometraje REAL DEFAULT 0",
]

def run():
    print(f"Conectando a {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for stmt in ALTERS:
        try:
            cur.execute(stmt)
            print(f"OK: {stmt}")
        except Exception as e:
            if 'duplicate column name' in str(e).lower():
                print(f"SKIP (ya existe): {stmt}")
            else:
                print(f"ERROR: {stmt} -> {e}")
    
    # Crear índice en patente si no existe
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_vehiculos_patente ON vehiculos(patente)")
        print("OK: Índice en patente creado")
    except Exception as e:
        print(f"ERROR creando índice: {e}")
    
    conn.commit()
    conn.close()
    print("Migración completada")

if __name__ == "__main__":
    run()
