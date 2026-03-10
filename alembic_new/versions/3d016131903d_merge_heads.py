"""merge_heads

Revision ID: 3d016131903d
Revises: 0002_lubricentros_multi_tenant, 0003_add_vehiculo_activo
Create Date: 2026-01-25 12:49:48.885325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d016131903d'
down_revision: Union[str, Sequence[str], None] = ('0002_lubricentros_multi_tenant', '0003_add_vehiculo_activo')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
