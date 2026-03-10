"""
Migración para agregar columna 'aprobado' a la tabla usuarios.
Esta columna indica si el usuario fue aprobado por el administrador del lubricentro.
"""
import sqlite3
import os

# Ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "sql_app.db")

def migrate():
    print("Iniciando migración para agregar columna 'aprobado'...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar si la columna ya existe
    cursor.execute("PRAGMA table_info(usuarios)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'aprobado' in columns:
        print("La columna 'aprobado' ya existe. No se requiere migración.")
        conn.close()
        return
    
    # Agregar la columna con valor default TRUE (1)
    # Los usuarios existentes quedarán aprobados automáticamente
    cursor.execute("ALTER TABLE usuarios ADD COLUMN aprobado BOOLEAN DEFAULT 1")
    
    # Asegurar que todos los usuarios existentes estén aprobados
    cursor.execute("UPDATE usuarios SET aprobado = 1")
    
    conn.commit()
    conn.close()
    
    print("✅ Migración completada. Columna 'aprobado' agregada exitosamente.")
    print("   - Todos los usuarios existentes fueron marcados como aprobados.")

if __name__ == "__main__":
    migrate()
