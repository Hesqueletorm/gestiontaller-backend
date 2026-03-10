import sqlite3

conn = sqlite3.connect('sql_app.db')

# Ver tablas
print("=== TABLAS ===")
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print(row[0])

# Ver usuarios
print("\n=== USUARIOS ===")
try:
    cursor = conn.execute("SELECT * FROM usuarios")
    print("Columnas:", [d[0] for d in cursor.description])
    for row in cursor.fetchall():
        print(row)
except Exception as e:
    print(f"Error: {e}")

conn.close()
