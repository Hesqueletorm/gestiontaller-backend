"""Script to fix admin password with correct hashing"""
import sqlite3
from passlib.context import CryptContext

# Same context as in security.py
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Connect to database
conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables in database: {tables}")

# Find user table
for table in tables:
    table_name = table[0]
    if 'user' in table_name.lower():
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        cols = [desc[0] for desc in cursor.description]
        print(f"\nTable '{table_name}' columns: {cols}")
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Row: {row}")

# Update admin password
# First find the correct table and column names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]

user_table = None
for t in tables:
    if 'user' in t.lower():
        user_table = t
        break

if user_table:
    # Get column names
    cursor.execute(f"PRAGMA table_info({user_table})")
    columns = cursor.fetchall()
    col_names = [c[1] for c in columns]
    print(f"\nUser table: {user_table}, Columns: {col_names}")
    
    # Find username and password columns
    username_col = None
    password_col = None
    for col in col_names:
        if 'usuario' in col.lower() or 'username' in col.lower():
            username_col = col
        if 'password' in col.lower() or 'hashed' in col.lower():
            password_col = col
    
    if username_col and password_col:
        # Get current admin hash
        cursor.execute(f"SELECT {username_col}, {password_col} FROM {user_table} WHERE {username_col} = 'admin'")
        row = cursor.fetchone()
        if row:
            print(f"\nCurrent admin password hash: {row[1][:60]}...")
            
            # Update with correct hash
            new_hash = get_password_hash('qwe123qwe')
            cursor.execute(f"UPDATE {user_table} SET {password_col} = ? WHERE {username_col} = 'admin'", (new_hash,))
            conn.commit()
            print(f"Updated admin password with pbkdf2_sha256 hash")
            print(f"New hash: {new_hash[:60]}...")
        else:
            print("Admin user not found")
    else:
        print(f"Could not identify username/password columns")
else:
    print("User table not found")

conn.close()
