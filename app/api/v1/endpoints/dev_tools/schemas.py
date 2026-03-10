"""
Schemas para el módulo de Herramientas de Desarrollador
"""
from pydantic import BaseModel


class DevToolResponse(BaseModel):
    success: bool
    message: str
    count: int = 0


class CacheLimpiezaResponse(BaseModel):
    success: bool
    message: str
    dirs_deleted: int = 0
    files_deleted: int = 0
