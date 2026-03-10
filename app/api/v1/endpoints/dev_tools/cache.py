"""
Endpoints de limpieza de caché
"""
from typing import Any
import os
import shutil
import stat
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.models.user import User
from .schemas import CacheLimpiezaResponse

router = APIRouter()


@router.post("/cache/clear", response_model=CacheLimpiezaResponse)
def clear_cache(
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Limpiar caché del sistema (__pycache__, .pyc, etc).
    Solo disponible para administradores.
    """
    try:
        proyecto_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
        
        carpetas_cache = ["__pycache__", ".pyc", "cache", ".cache", "temp", ".temp"]
        
        count_dirs = 0
        count_files = 0
        errores = []
        
        def remove_readonly(func, path, _):
            """Clear the readonly bit and reattempt the removal"""
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass
        
        # Eliminar carpetas de caché
        for root, dirs, files in os.walk(proyecto_root, topdown=False):
            for dir_name in dirs:
                if dir_name in carpetas_cache:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(dir_path, onerror=remove_readonly)
                        count_dirs += 1
                    except Exception as e:
                        errores.append(f"Error eliminando {dir_path}: {e}")
        
        # Eliminar archivos .pyc .pyo
        for root, dirs, files in os.walk(proyecto_root):
            for file_name in files:
                if file_name.endswith(".pyc") or file_name.endswith(".pyo"):
                    file_path = os.path.join(root, file_name)
                    try:
                        os.remove(file_path)
                        count_files += 1
                    except Exception as e:
                        errores.append(f"Error eliminando {file_path}: {e}")
        
        msg = f"Limpieza completada: {count_dirs} carpetas y {count_files} archivos eliminados."
        if errores:
            msg += f" ({len(errores)} errores)"
        
        return CacheLimpiezaResponse(
            success=True,
            message=msg,
            dirs_deleted=count_dirs,
            files_deleted=count_files
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar caché: {str(e)}")
