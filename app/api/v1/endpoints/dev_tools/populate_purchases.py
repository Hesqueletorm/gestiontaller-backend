"""
Endpoints para poblar compras y proveedores
"""
from typing import Any
import random
from datetime import timedelta, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.inventory import Producto
from app.models.purchase import Purchase, PurchaseItem
from app.models.product_lote import ProductLote

from .schemas import DevToolResponse
from .catalogs import PROVEEDORES

router = APIRouter()


@router.post("/populate/purchases", response_model=DevToolResponse)
def populate_purchases(
    n: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar compras de stock con productos existentes."""
    try:
        productos = db.query(Producto).filter(
            Producto.lubricentro_id == current_user.lubricentro_id
        ).all()
        
        if not productos:
            return DevToolResponse(
                success=False, 
                message="⚠️ No hay productos en stock. Genere productos primero.",
                count=0
            )
        
        hoy = date.today()
        metodos_pago = ["Efectivo", "Transferencia", "Cheque", "Cuenta Corriente"]
        
        count = 0
        for _ in range(n):
            proveedor = random.choice(PROVEEDORES)
            fecha = hoy - timedelta(days=random.randint(0, 90))
            
            compra = Purchase(
                lubricentro_id=current_user.lubricentro_id,
                fecha=fecha,
                numero_factura=f"FC-{random.randint(1000, 9999)}-{random.randint(10000000, 99999999)}",
                proveedor_nombre=proveedor["nombre"],
                proveedor_cuit=proveedor["cuit"],
                metodo_pago=random.choice(metodos_pago),
                subtotal=0,
                iva=0,
                total=0,
                observaciones=random.choice(["", "Pedido mensual", "Reposición urgente", "Promoción proveedor"]),
                created_by=current_user.id
            )
            db.add(compra)
            db.flush()
            
            num_items = random.randint(2, 6)
            productos_seleccionados = random.sample(productos, min(num_items, len(productos)))
            
            subtotal_compra = 0
            for producto in productos_seleccionados:
                cantidad = random.randint(5, 50)
                precio_compra = random.uniform(300, 3500)
                
                subtotal_item = cantidad * precio_compra
                iva_item = subtotal_item * 0.21
                total_item = subtotal_item + iva_item
                
                item = PurchaseItem(
                    compra_id=compra.id,
                    producto_id=producto.id,
                    articulo=producto.nombre,
                    codigo=producto.codigo,
                    cantidad=cantidad,
                    precio_unitario=round(precio_compra, 2),
                    iva_porcentaje=21.0,
                    subtotal=round(subtotal_item, 2),
                    total=round(total_item, 2)
                )
                db.add(item)
                
                producto.cantidad = (producto.cantidad or 0) + cantidad
                
                tiene_vto = random.random() < 0.7
                if tiene_vto:
                    dias_delta = random.randint(30, 365)
                    fecha_vto = (hoy + timedelta(days=dias_delta)).isoformat()
                else:
                    fecha_vto = None
                
                lote = ProductLote(
                    lubricentro_id=current_user.lubricentro_id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    fecha_vencimiento=fecha_vto,
                    compra_id=compra.id
                )
                db.add(lote)
                
                subtotal_compra += subtotal_item
            
            compra.subtotal = round(subtotal_compra, 2)
            compra.iva = round(subtotal_compra * 0.21, 2)
            compra.total = round(subtotal_compra * 1.21, 2)
            
            count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} compras generadas con lotes y stock actualizado", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar compras: {str(e)}")


@router.post("/populate/suppliers", response_model=DevToolResponse)
def populate_suppliers(
    n: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar proveedores de prueba."""
    from app.models.supplier import Supplier
    
    try:
        # Catálogos para generar datos realistas
        nombres_base = [
            "Distribuidora", "Mayorista", "Comercial", "Importadora", "Lubricantes",
            "Repuestos", "Auto Parts", "Motores", "Filtros", "Aceites", "Premium",
            "Industrial", "Automotriz", "Centro", "Norte", "Sur", "Express"
        ]
        sufijos = ["SA", "SRL", "SAS", "y Cía", "Hnos", "& Asociados", "Argentina", "del Centro"]
        rubros = ["Aceites", "Filtros", "Repuestos", "Electricidad", "Limpieza", "Herramientas", "Accesorios", "General"]
        
        count = 0
        for _ in range(n):
            # Generar nombre único
            nombre = f"{random.choice(nombres_base)} {random.choice(nombres_base)} {random.choice(sufijos)}"
            
            # Verificar que no exista
            existing = db.query(Supplier).filter(
                Supplier.lubricentro_id == current_user.lubricentro_id,
                Supplier.nombre == nombre
            ).first()
            
            if existing:
                continue
            
            # Generar CUIT
            prefijo = random.choice(["20", "23", "27", "30", "33"])
            dni = str(random.randint(10000000, 99999999))
            verificador = random.randint(0, 9)
            cuit = f"{prefijo}-{dni}-{verificador}"
            
            # Generar teléfono
            telefono = f"011-{random.randint(4000, 4999)}-{random.randint(1000, 9999)}"
            
            # Generar email
            email_base = nombre.lower().replace(" ", "").replace(".", "")[:15]
            email = f"ventas@{email_base}.com.ar"
            
            # Generar dirección
            calles = ["Av. Corrientes", "Av. Rivadavia", "Av. Santa Fe", "Av. Independencia", "Calle San Martín", "Av. Belgrano"]
            direccion = f"{random.choice(calles)} {random.randint(100, 9999)}, CABA"
            
            # Generar contacto
            nombres_contacto = ["Juan", "María", "Carlos", "Laura", "Diego", "Ana", "Pablo", "Lucía"]
            contacto = f"{random.choice(nombres_contacto)} (Ventas)"
            
            supplier = Supplier(
                lubricentro_id=current_user.lubricentro_id,
                nombre=nombre,
                cuit=cuit,
                telefono=telefono,
                email=email,
                direccion=direccion,
                contacto=contacto,
                rubro=random.choice(rubros),
                notas="Proveedor generado por bot de desarrollo",
                activo=True
            )
            db.add(supplier)
            count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} proveedores generados con éxito", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar proveedores: {str(e)}")
