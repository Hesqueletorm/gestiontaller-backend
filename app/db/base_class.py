from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import MetaData

# Convención de nombres para constraints (necesario para SQLite batch migration)
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)

@as_declarative(metadata=metadata)
class Base:
    id: int
    __name__: str

    # Generar nombre de tabla automaticamente a partir del nombre de la clase
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
