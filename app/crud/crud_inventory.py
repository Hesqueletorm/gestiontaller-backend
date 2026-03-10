"""
CRUD operations para Inventory (Productos y Categorías)
"""
from typing import List, Optional, Tuple
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.crud.base import CRUDBase
from app.models.inventory import Product, Category
from app.schemas.product_schema import ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    
    def get_by_code(self, db: Session, *, code: str) -> Optional[Product]:
        """Buscar producto por código"""
        return db.query(Product).filter(Product.codigo == code).first()

    def get_filtered(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        nombre: Optional[str] = None,
        codigo: Optional[str] = None,
        categoria: Optional[str] = None,
        solo_alerta: bool = False,
        skip: int = 0,
        limit: int = 25,
    ) -> Tuple[List[Product], int]:
        """
        Obtener productos con filtros y paginación.
        Devuelve tupla: (lista de productos, total encontrados)
        """
        query = db.query(Product).filter(Product.lubricentro_id == lubricentro_id)

        # Filtro por nombre
        if nombre:
            query = query.filter(Product.nombre.ilike(f"%{nombre}%"))

        # Filtro por código
        if codigo:
            query = query.filter(Product.codigo.ilike(f"%{codigo}%"))

        # Filtro por categoría
        if categoria:
            query = query.filter(Product.categoria.ilike(categoria))

        # Filtro solo con alerta
        if solo_alerta:
            query = query.filter(Product.alerta == 1)

        # Contar total antes de paginar
        total = query.count()

        # Ordenar y paginar
        products = (
            query
            .order_by(func.lower(Product.nombre))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return products, total

    def update(
        self, db: Session, *, db_obj: Product, obj_in: ProductUpdate
    ) -> Product:
        """Actualizar producto"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_expiring(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        dias: int = 30,
    ) -> List[Product]:
        """
        Obtener productos con lotes próximos a vencer o ya vencidos.
        - Lotes que vencen en los próximos X días
        - Lotes ya vencidos
        Filtrado por lubricentro (multi-tenant).
        Solo incluye lotes con cantidad > 0 y fecha_vencimiento definida.
        Retorna productos únicos (sin duplicados).
        """
        from app.models.product_lote import ProductLote
        
        hoy = date.today()
        fecha_limite = hoy + timedelta(days=dias)
        
        # Convertir a string formato YYYY-MM-DD para comparar con el campo String
        fecha_limite_str = fecha_limite.strftime("%Y-%m-%d")
        
        # Buscar lotes con cantidad > 0 que vencen dentro del rango
        lotes_query = db.query(ProductLote.producto_id).filter(
            ProductLote.lubricentro_id == lubricentro_id,
            ProductLote.cantidad > 0,
            ProductLote.fecha_vencimiento.isnot(None),
            ProductLote.fecha_vencimiento != "",
            ProductLote.fecha_vencimiento <= fecha_limite_str
        ).distinct()
        
        producto_ids = [r[0] for r in lotes_query.all()]
        
        if not producto_ids:
            return []
        
        # Obtener los productos correspondientes
        productos = db.query(Product).filter(
            Product.id.in_(producto_ids),
            Product.lubricentro_id == lubricentro_id
        ).order_by(func.lower(Product.nombre)).all()
        
        return productos


class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryCreate]):
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Category]:
        """Buscar categoría por nombre"""
        return db.query(Category).filter(Category.nombre == name).first()

    def get_all_names(self, db: Session) -> List[str]:
        """Obtener lista de nombres de categorías (sin duplicados)"""
        results = db.query(Category.nombre).distinct().order_by(Category.nombre).all()
        return [r[0] for r in results]

    def update(
        self, db: Session, *, db_obj: Category, obj_in: CategoryUpdate
    ) -> Category:
        """Actualizar categoría"""
        update_data = obj_in.model_dump(exclude_unset=True)
        old_name = db_obj.nombre
        new_name = update_data.get("nombre")

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        
        # Si cambió el nombre, actualizar productos que usan esta categoría
        if new_name and new_name != old_name:
            db.query(Product).filter(Product.categoria == old_name).update(
                {"categoria": new_name}, synchronize_session=False
            )
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_and_update_products(self, db: Session, *, db_obj: Category) -> None:
        """Eliminar categoría y limpiar productos asociados"""
        cat_name = db_obj.nombre
        
        # Limpiar categoría de productos
        db.query(Product).filter(Product.categoria == cat_name).update(
            {"categoria": None}, synchronize_session=False
        )
        
        # Eliminar categoría
        db.delete(db_obj)
        db.commit()


product = CRUDProduct(Product)
category = CRUDCategory(Category)
