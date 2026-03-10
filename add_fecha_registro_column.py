"""
Script para agregar columna fecha_registro a la tabla clientes
"""
import sqlite3
from datetime import date

DB_PATH = "sql_app.db"

def add_fecha_registro_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar si la columna ya existe
    cursor.execute("PRAGMA table_info(clientes)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'fecha_registro' not in columns:
        print("Agregando columna fecha_registro a tabla clientes...")
        cursor.execute("ALTER TABLE clientes ADD COLUMN fecha_registro TEXT")
        
        # Establecer fecha de hoy para clientes existentes
        today = date.today().isoformat()
        cursor.execute("UPDATE clientes SET fecha_registro = ? WHERE fecha_registro IS NULL", (today,))
        
        conn.commit()
        print(f"Columna agregada. Clientes existentes actualizados con fecha: {today}")
    else:
        print("La columna fecha_registro ya existe.")
    
    conn.close()

if __name__ == "__main__":
    add_fecha_registro_column()
