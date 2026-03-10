"""Agregar campo nombre_lubricentro a usuarios

Revision ID: 0001
Revises: 
Create Date: 2026-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_nombre_lubricentro'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna nombre_lubricentro a la tabla usuarios
    op.add_column('usuarios', sa.Column('nombre_lubricentro', sa.String(), nullable=True))


def downgrade() -> None:
    # Eliminar columna nombre_lubricentro de la tabla usuarios
    op.drop_column('usuarios', 'nombre_lubricentro')
