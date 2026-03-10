"""
Migración para agregar columnas de colores de identidad al modelo User.
Estas columnas almacenan los 3 colores del gradiente de la barra de identidad.
"""

import sqlite3
import os

def migrar():
    """Agregar columnas de colores de identidad si no existen."""
    
    # Ruta a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), "lubricentro.db")
    
    if not os.path.exists(db_path):
        print(f"❌ No se encontró la base de datos en: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar columnas existentes en la tabla usuarios
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas_existentes = [col[1] for col in cursor.fetchall()]
        
        columnas_nuevas = [
            ("color_identidad1", "TEXT"),
            ("color_identidad2", "TEXT"),
            ("color_identidad3", "TEXT"),
        ]
        
        for nombre_columna, tipo in columnas_nuevas:
            if nombre_columna not in columnas_existentes:
                print(f"➕ Agregando columna '{nombre_columna}' a tabla usuarios...")
                cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {nombre_columna} {tipo}")
                print(f"✅ Columna '{nombre_columna}' agregada exitosamente")
            else:
                print(f"ℹ️ La columna '{nombre_columna}' ya existe")
        
        conn.commit()
        print("\n✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    migrar()
