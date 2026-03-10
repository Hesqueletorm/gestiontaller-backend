"""
CRUD operations para Sales (Comprobantes)
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
import re

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.crud.base import CRUDBase
from app.models.sales import Sale, SaleItem, SaleVehicle
from app.models.client import Visit  # Para crear visitas automáticas
from app.models.inventory import Product
from app.schemas.sale_schema import SaleCreate, SaleItemCreate, SaleFilter


def _parse_float(value: Any) -> float:
    """Convierte un valor a float de forma segura"""
    try:
        if isinstance(value, str):
            value = value.replace(',', '.')
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalizar_punto_venta(pv: str) -> str:
    """Normaliza el punto de venta a 4 dígitos"""
    digits = re.sub(r"\D", "", pv or "")
    if not digits:
        return "0001"
    return digits[-4:].zfill(4)


def _calc_item(cantidad: float, precio: float, iva_pct: float) -> tuple:
    """Calcula subtotal, IVA y total de un item"""
    subtotal = cantidad * precio
    iva_monto = subtotal * (iva_pct / 100.0)
    total = subtotal + iva_monto
    return subtotal, iva_monto, total


class CRUDSale(CRUDBase[Sale, SaleCreate, SaleCreate]):
    
    def get_with_details(self, db: Session, *, id: int) -> Optional[Sale]:
        """Obtiene un comprobante con sus items y vehículos"""
        return (
            db.query(Sale)
            .options(joinedload(Sale.items), joinedload(Sale.vehiculos))
            .filter(Sale.id == id)
            .first()
        )

    def get_next_number(self, db: Session, *, punto_venta: str) -> str:
        """Obtiene el siguiente número de comprobante para un punto de venta"""
        pv = _normalizar_punto_venta(punto_venta)
        
        # Buscar el máximo número existente
        result = (
            db.query(func.max(Sale.numero))
            .filter(Sale.punto_venta == pv)
            .scalar()
        )
        
        if result:
            try:
                max_num = int(re.sub(r"\D", "", result))
            except (TypeError, ValueError):
                max_num = 0
        else:
            max_num = 0
        
        siguiente = max_num + 1
        return f"{siguiente:08d}"

    def check_exists(self, db: Session, *, punto_venta: str, numero: str) -> bool:
        """Verifica si ya existe un comprobante con ese punto de venta y número"""
        pv = _normalizar_punto_venta(punto_venta)
        return (
            db.query(Sale)
            .filter(Sale.punto_venta == pv, Sale.numero == numero)
            .first() is not None
        )

    def get_filtered(
        self, 
        db: Session, 
        *, 
        lubricentro_id: int,
        filters: SaleFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[Sale]:
        """Obtiene comprobantes con filtros opcionales, aislados por lubricentro"""
        query = db.query(Sale).filter(Sale.lubricentro_id == lubricentro_id)
        
        if filters.cliente:
            query = query.filter(
                Sale.cliente_nombre.ilike(f"%{filters.cliente}%")
            )
        
        if filters.vehiculo:
            # Subquery para filtrar por vehículo
            query = query.filter(
                Sale.vehiculos.any(
                    SaleVehicle.descripcion.ilike(f"%{filters.vehiculo}%")
                )
            )
        
        if filters.desde:
            query = query.filter(Sale.fecha >= filters.desde)
        
        if filters.hasta:
            query = query.filter(Sale.fecha <= filters.hasta)
        
        return (
            query
            .order_by(Sale.fecha.desc(), Sale.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, db: Session, *, obj_in: SaleCreate, lubricentro_id: int) -> Sale:
        """Crea un nuevo comprobante con items y vehículos, asociado al lubricentro"""
        
        # Normalizar punto de venta
        pv = _normalizar_punto_venta(obj_in.punto_venta)
        
        # Obtener o generar número
        if obj_in.numero:
            numero = obj_in.numero.zfill(8)
            # Verificar si existe y obtener siguiente si es necesario
            if self.check_exists(db, punto_venta=pv, numero=numero):
                numero = self.get_next_number(db, punto_venta=pv)
        else:
            numero = self.get_next_number(db, punto_venta=pv)
        
        # Fecha actual si no se especifica (incluye hora)
        fecha = obj_in.fecha or datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Calcular totales de items
        subtotal_total = 0.0
        iva_total = 0.0
        total_total = 0.0
        items_data = []
        
        for item in obj_in.items:
            sub, iva, tot = _calc_item(
                item.cantidad, 
                item.precio_unitario, 
                item.iva_porcentaje
            )
            subtotal_total += sub
            iva_total += iva
            total_total += tot
            items_data.append({
                "articulo": item.articulo,
                "cantidad": item.cantidad,
                "precio_unitario": item.precio_unitario,
                "iva_porcentaje": item.iva_porcentaje,
                "subtotal": sub,
                "total": tot,
                "es_servicio": getattr(item, 'es_servicio', 0),
            })
        
        # Crear comprobante
        db_sale = Sale(
            lubricentro_id=lubricentro_id,
            fecha=fecha,
            tipo=obj_in.tipo,
            punto_venta=pv,
            numero=numero,
            metodo_pago=obj_in.metodo_pago,
            cliente_nombre=obj_in.cliente_nombre,
            cliente_dni=obj_in.cliente_dni or "",
            cliente_cuit=obj_in.cliente_cuit or "",
            cliente_email=obj_in.cliente_email or "",
            cliente_telefono=obj_in.cliente_telefono or "",
            domicilio=obj_in.domicilio or "",
            condicion_iva=obj_in.condicion_iva or "",
            subtotal=subtotal_total,
            iva=iva_total,
            total=total_total,
            observaciones=obj_in.observaciones or "",
        )
        db.add(db_sale)
        db.flush()  # Para obtener el ID
        
        # Crear items
        for item_data in items_data:
            db_item = SaleItem(comprobante_id=db_sale.id, **item_data)
            db.add(db_item)
        
        # Crear vehículos
        vehiculo_descripcion = None
        vehiculo_km = 0
        for vehiculo in obj_in.vehiculos:
            if vehiculo.descripcion.strip():
                db_vehiculo = SaleVehicle(
                    comprobante_id=db_sale.id,
                    descripcion=vehiculo.descripcion,
                    kilometraje=vehiculo.kilometraje,
                )
                db.add(db_vehiculo)
                # Guardar datos del primer vehículo para la visita
                if vehiculo_descripcion is None:
                    vehiculo_descripcion = vehiculo.descripcion
                    vehiculo_km = vehiculo.kilometraje
        
        # === CREAR VISITA AUTOMÁTICA SI HAY CLIENTE_ID ===
        # Verificar que no exista ya una visita para este comprobante (evitar duplicados)
        if obj_in.cliente_id:
            # Primero hacer commit del comprobante para que tenga ID definitivo
            db.flush()
            
            # Verificar si ya existe visita para este comprobante
            existing_visit = db.query(Visit).filter(
                Visit.comprobante_id == db_sale.id
            ).first()
            
            if not existing_visit:
                # También verificar por cliente + fecha + observación (doble seguridad)
                fecha_visita = fecha.split(" ")[0] if " " in fecha else fecha
                obs = obj_in.observaciones or f"Factura #{numero}"
                
                duplicate_check = db.query(Visit).filter(
                    Visit.cliente_id == obj_in.cliente_id,
                    Visit.fecha == fecha_visita,
                    Visit.observacion == obs
                ).first()
                
                if not duplicate_check:
                    db_visita = Visit(
                        cliente_id=obj_in.cliente_id,
                        comprobante_id=db_sale.id,
                        fecha=fecha_visita,
                        kilometraje=vehiculo_km,
                        vehiculo_descripcion=vehiculo_descripcion,
                        observacion=obs,
                        lubricentro_id=lubricentro_id
                    )
                    db.add(db_visita)
        
        db.commit()
        db.refresh(db_sale)
        return db_sale

    def descontar_stock(self, db: Session, *, items: List[Dict]) -> None:
        """Descuenta stock de los productos utilizados"""
        for item in items:
            stock_id = item.get("stock_id")
            cantidad = _parse_float(item.get("cantidad", 0))
            
            if stock_id and cantidad > 0:
                producto = db.query(Product).filter(Product.id == stock_id).first()
                if producto:
                    nueva_cantidad = max(0, producto.cantidad - cantidad)
                    producto.cantidad = nueva_cantidad
        
        db.commit()


sale = CRUDSale(Sale)
