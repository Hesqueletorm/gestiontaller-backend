from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Configuración compatible con SQLite y Postgres
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL: connection pooling para producción
    connect_args = {"options": "-c client_encoding=utf8"}
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 30,
        "pool_recycle": 1800,
        "pool_timeout": 30,
    })

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
