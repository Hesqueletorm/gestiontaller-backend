#!/usr/bin/env python3
# Script para verificar el estado de usuarios y lubricentros

from app.db.session import SessionLocal
from app.models.user import User
from app.models.lubricentro import Lubricentro

db = SessionLocal()

print("=" * 60)
print("LUBRICENTROS:")
print("=" * 60)
lubricentros = db.query(Lubricentro).all()
print(f"Total lubricentros: {len(lubricentros)}")
for l in lubricentros:
    print(f"  ID:{l.id} Nombre:{l.nombre} Codigo:{l.codigo} Activo:{l.activo}")

print()
print("=" * 60)
print("USUARIOS:")
print("=" * 60)
users = db.query(User).all()
print(f"Total usuarios: {len(users)}")
for u in users:
    aprobado = getattr(u, 'aprobado', 'N/A')
    print(f"  ID:{u.id} Usuario:{u.usuario} Rol:{u.rol} Activo:{u.activo} Aprobado:{aprobado} LubricentroID:{u.lubricentro_id}")

db.close()
