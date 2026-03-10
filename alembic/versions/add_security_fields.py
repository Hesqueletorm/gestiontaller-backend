"""Agregar campos de seguridad al modelo User

Campos nuevos:
- failed_login_attempts: Intentos fallidos consecutivos
- locked_until: Fecha hasta la que está bloqueada la cuenta
- last_login_at: Último login exitoso
- last_login_ip: IP del último login
- last_failed_login: Último intento fallido
- password_changed_at: Última vez que cambió contraseña
- totp_secret: Secreto TOTP encriptado
- totp_enabled: Si tiene 2FA activado
- totp_backup_codes: Códigos de backup (JSON)

Revision ID: add_security_fields
Revises: (anterior)
Create Date: 2026-02-03
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_security_fields'
down_revision = None  # Ajustar al ID de la migración anterior
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos de bloqueo de cuenta
    op.add_column('usuarios', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('usuarios', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('usuarios', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    op.add_column('usuarios', sa.Column('last_login_ip', sa.String(), nullable=True))
    op.add_column('usuarios', sa.Column('last_failed_login', sa.DateTime(), nullable=True))
    op.add_column('usuarios', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    
    # Agregar campos de 2FA/TOTP
    op.add_column('usuarios', sa.Column('totp_secret', sa.String(), nullable=True))
    op.add_column('usuarios', sa.Column('totp_enabled', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('usuarios', sa.Column('totp_backup_codes', sa.Text(), nullable=True))


def downgrade():
    # Eliminar campos de 2FA
    op.drop_column('usuarios', 'totp_backup_codes')
    op.drop_column('usuarios', 'totp_enabled')
    op.drop_column('usuarios', 'totp_secret')
    
    # Eliminar campos de bloqueo
    op.drop_column('usuarios', 'password_changed_at')
    op.drop_column('usuarios', 'last_failed_login')
    op.drop_column('usuarios', 'last_login_ip')
    op.drop_column('usuarios', 'last_login_at')
    op.drop_column('usuarios', 'locked_until')
    op.drop_column('usuarios', 'failed_login_attempts')
