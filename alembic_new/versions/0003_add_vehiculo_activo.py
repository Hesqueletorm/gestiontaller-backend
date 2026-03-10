"""add activo column to vehiculos

Revision ID: 0003
Revises: 98b4c479c80f
Create Date: 2026-01-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_vehiculo_activo'
down_revision: Union[str, None] = '98b4c479c80f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna activo a vehiculos con valor por defecto True
    op.add_column('vehiculos', sa.Column('activo', sa.Boolean(), nullable=True, server_default='1'))
    
    # Actualizar todos los registros existentes a activo=True
    op.execute("UPDATE vehiculos SET activo = 1 WHERE activo IS NULL")


def downgrade() -> None:
    op.drop_column('vehiculos', 'activo')
