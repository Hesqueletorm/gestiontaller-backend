"""add_lubricentros_table_multi_tenant

Revision ID: 0002_lubricentros_multi_tenant
Revises: 98b4c479c80f
Create Date: 2026-01-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_lubricentros_multi_tenant'
down_revision: Union[str, Sequence[str], None] = '98b4c479c80f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to multi-tenant with lubricentros table."""
    
    # 1. Crear tabla de lubricentros
    op.create_table('lubricentros',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(), nullable=False, server_default='Mi Lubricentro'),
        sa.Column('codigo', sa.String(), nullable=False),
        sa.Column('color_fondo', sa.String(), nullable=True, server_default='#04060c'),
        sa.Column('color_tematica', sa.String(), nullable=True, server_default='#f2e71a'),
        sa.Column('color_tematica2', sa.String(), nullable=True, server_default='#FFA000'),
        sa.Column('color_letras', sa.String(), nullable=True, server_default='#F5F7FA'),
        sa.Column('tema', sa.String(), nullable=True, server_default='dark'),
        sa.Column('idioma', sa.String(), nullable=True, server_default='Español'),
        sa.Column('configuracion_extra', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('activo', sa.Boolean(), nullable=True, server_default='1'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_lubricentros')),
        sa.UniqueConstraint('codigo', name=op.f('uq_lubricentros_codigo'))
    )
    op.create_index(op.f('ix_lubricentros_codigo'), 'lubricentros', ['codigo'], unique=True)
    
    # 2. Insertar lubricentro por defecto
    op.execute("""
        INSERT INTO lubricentros (nombre, codigo, color_fondo, color_tematica, color_tematica2, color_letras, tema, activo)
        VALUES ('Lubricentro Principal', 'LUBRI001', '#04060c', '#f2e71a', '#FFA000', '#F5F7FA', 'dark', 1)
    """)
    
    # 3. Agregar lubricentro_id a usuarios
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lubricentro_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_usuarios_lubricentro_id'), ['lubricentro_id'], unique=False)
        batch_op.create_foreign_key(
            op.f('fk_usuarios_lubricentro_id_lubricentros'), 
            'lubricentros', ['lubricentro_id'], ['id'], 
            ondelete='CASCADE'
        )
        # Eliminar columna nombre_lubricentro (ahora viene del join)
        try:
            batch_op.drop_column('nombre_lubricentro')
        except:
            pass
    
    # 4. Asignar usuarios existentes al lubricentro por defecto
    op.execute("UPDATE usuarios SET lubricentro_id = 1 WHERE lubricentro_id IS NULL")
    
    # 5. Cambiar user_id a lubricentro_id en clientes
    with op.batch_alter_table('clientes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lubricentro_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_clientes_lubricentro_id'), ['lubricentro_id'], unique=False)
        batch_op.create_foreign_key(
            op.f('fk_clientes_lubricentro_id_lubricentros'),
            'lubricentros', ['lubricentro_id'], ['id'],
            ondelete='CASCADE'
        )
    
    # Migrar datos de user_id a lubricentro_id (obtener lubricentro del usuario)
    op.execute("""
        UPDATE clientes SET lubricentro_id = (
            SELECT COALESCE(u.lubricentro_id, 1) FROM usuarios u WHERE u.id = clientes.user_id
        ) WHERE user_id IS NOT NULL
    """)
    op.execute("UPDATE clientes SET lubricentro_id = 1 WHERE lubricentro_id IS NULL")
    
    # 6. Cambiar user_id a lubricentro_id en turnos
    with op.batch_alter_table('turnos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lubricentro_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_turnos_lubricentro_id'), ['lubricentro_id'], unique=False)
        batch_op.create_foreign_key(
            op.f('fk_turnos_lubricentro_id_lubricentros'),
            'lubricentros', ['lubricentro_id'], ['id'],
            ondelete='CASCADE'
        )
        # Recrear índice único con lubricentro_id
        try:
            batch_op.drop_index('idx_turnos_user_fecha_hora')
        except:
            pass
        batch_op.create_index('idx_turnos_lubri_fecha_hora', ['lubricentro_id', 'fecha', 'hora'], unique=True)
    
    op.execute("""
        UPDATE turnos SET lubricentro_id = (
            SELECT COALESCE(u.lubricentro_id, 1) FROM usuarios u WHERE u.id = turnos.user_id
        ) WHERE user_id IS NOT NULL
    """)
    op.execute("UPDATE turnos SET lubricentro_id = 1 WHERE lubricentro_id IS NULL")
    
    # 7. Cambiar user_id a lubricentro_id en comprobantes
    with op.batch_alter_table('comprobantes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lubricentro_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_comprobantes_lubricentro_id'), ['lubricentro_id'], unique=False)
        batch_op.create_foreign_key(
            op.f('fk_comprobantes_lubricentro_id_lubricentros'),
            'lubricentros', ['lubricentro_id'], ['id'],
            ondelete='CASCADE'
        )
        try:
            batch_op.drop_index('idx_comp_user_pv_num')
        except:
            pass
        batch_op.create_index('idx_comp_lubri_pv_num', ['lubricentro_id', 'punto_venta', 'numero'], unique=True)
    
    op.execute("""
        UPDATE comprobantes SET lubricentro_id = (
            SELECT COALESCE(u.lubricentro_id, 1) FROM usuarios u WHERE u.id = comprobantes.user_id
        ) WHERE user_id IS NOT NULL
    """)
    op.execute("UPDATE comprobantes SET lubricentro_id = 1 WHERE lubricentro_id IS NULL")
    
    # 8. Cambiar user_id a lubricentro_id en stock_productos
    with op.batch_alter_table('stock_productos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lubricentro_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_stock_productos_lubricentro_id'), ['lubricentro_id'], unique=False)
        batch_op.create_foreign_key(
            op.f('fk_stock_productos_lubricentro_id_lubricentros'),
            'lubricentros', ['lubricentro_id'], ['id'],
            ondelete='CASCADE'
        )
    
    op.execute("""
        UPDATE stock_productos SET lubricentro_id = (
            SELECT COALESCE(u.lubricentro_id, 1) FROM usuarios u WHERE u.id = stock_productos.user_id
        ) WHERE user_id IS NOT NULL
    """)
    op.execute("UPDATE stock_productos SET lubricentro_id = 1 WHERE lubricentro_id IS NULL")
    
    # 9. Cambiar user_id a lubricentro_id en stock_categorias
    with op.batch_alter_table('stock_categorias', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lubricentro_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_stock_categorias_lubricentro_id'), ['lubricentro_id'], unique=False)
        batch_op.create_foreign_key(
            op.f('fk_stock_categorias_lubricentro_id_lubricentros'),
            'lubricentros', ['lubricentro_id'], ['id'],
            ondelete='CASCADE'
        )
    
    op.execute("""
        UPDATE stock_categorias SET lubricentro_id = (
            SELECT COALESCE(u.lubricentro_id, 1) FROM usuarios u WHERE u.id = stock_categorias.user_id
        ) WHERE user_id IS NOT NULL
    """)
    op.execute("UPDATE stock_categorias SET lubricentro_id = 1 WHERE lubricentro_id IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    # Remover foreign keys y columnas lubricentro_id
    with op.batch_alter_table('stock_categorias', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('fk_stock_categorias_lubricentro_id_lubricentros'), type_='foreignkey')
        batch_op.drop_index(op.f('ix_stock_categorias_lubricentro_id'))
        batch_op.drop_column('lubricentro_id')
    
    with op.batch_alter_table('stock_productos', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('fk_stock_productos_lubricentro_id_lubricentros'), type_='foreignkey')
        batch_op.drop_index(op.f('ix_stock_productos_lubricentro_id'))
        batch_op.drop_column('lubricentro_id')
    
    with op.batch_alter_table('comprobantes', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('fk_comprobantes_lubricentro_id_lubricentros'), type_='foreignkey')
        batch_op.drop_index('idx_comp_lubri_pv_num')
        batch_op.drop_index(op.f('ix_comprobantes_lubricentro_id'))
        batch_op.drop_column('lubricentro_id')
        batch_op.create_index('idx_comp_user_pv_num', ['user_id', 'punto_venta', 'numero'], unique=True)
    
    with op.batch_alter_table('turnos', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('fk_turnos_lubricentro_id_lubricentros'), type_='foreignkey')
        batch_op.drop_index('idx_turnos_lubri_fecha_hora')
        batch_op.drop_index(op.f('ix_turnos_lubricentro_id'))
        batch_op.drop_column('lubricentro_id')
        batch_op.create_index('idx_turnos_user_fecha_hora', ['user_id', 'fecha', 'hora'], unique=True)
    
    with op.batch_alter_table('clientes', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('fk_clientes_lubricentro_id_lubricentros'), type_='foreignkey')
        batch_op.drop_index(op.f('ix_clientes_lubricentro_id'))
        batch_op.drop_column('lubricentro_id')
    
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('fk_usuarios_lubricentro_id_lubricentros'), type_='foreignkey')
        batch_op.drop_index(op.f('ix_usuarios_lubricentro_id'))
        batch_op.drop_column('lubricentro_id')
        batch_op.add_column(sa.Column('nombre_lubricentro', sa.String(), nullable=True))
    
    op.drop_index(op.f('ix_lubricentros_codigo'), table_name='lubricentros')
    op.drop_table('lubricentros')
