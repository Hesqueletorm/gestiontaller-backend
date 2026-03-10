import sqlite3

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

# Crear lubricentro
cursor.execute("""
    INSERT INTO lubricentros (nombre, codigo, color_fondo, color_tematica, color_tematica2, color_letras, tema, idioma, activo) 
    VALUES ('Lubricentro Maldonado', 'LM001', '#1a1a2e', '#e94560', '#533483', '#eaeaea', 'dark', 'es', 1)
""")

# Obtener el ID del lubricentro creado
lubricentro_id = cursor.lastrowid
print(f"Lubricentro creado con ID: {lubricentro_id}")

# Asignar al usuario
cursor.execute(f"UPDATE usuarios SET lubricentro_id = {lubricentro_id} WHERE id = 1")
print("Usuario admin actualizado con lubricentro_id")

conn.commit()
conn.close()

print("¡Listo!")
