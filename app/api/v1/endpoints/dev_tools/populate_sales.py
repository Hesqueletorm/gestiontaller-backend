"""
Endpoints para poblar ventas/comprobantes
"""
from typing import Any
import random
from datetime import timedelta, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.client import Client
from app.models.sales import Sale, SaleItem, SaleVehicle

from .schemas import DevToolResponse
from .catalogs import (
    ARTICULOS_FACTURA,
    generar_dni, generar_cuit, generar_direccion, generar_vehiculo
)

router = APIRouter()


@router.post("/populate/sales", response_model=DevToolResponse)
def populate_sales(
    n: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar comprobantes/facturas de prueba."""
    try:
        clientes = db.query(Client).filter(
            Client.lubricentro_id == current_user.lubricentro_id
        ).all()
        
        if not clientes:
            return DevToolResponse(
                success=False, 
                message="⚠️ No hay clientes. Genere clientes primero.",
                count=0
            )
        
        tipos = ["Factura A", "Factura B", "Factura C", "Nota de Crédito"]
        metodos = ["Efectivo", "Tarjeta", "Transferencia", "Cuenta Corriente"]
        hoy = date.today()
        
        ultimo = db.query(Sale).filter(
            Sale.lubricentro_id == current_user.lubricentro_id
        ).order_by(Sale.id.desc()).first()
        
        last_num = int(ultimo.numero) if ultimo else 0
        
        count = 0
        for i in range(n):
            cliente = random.choice(clientes)
            tipo = random.choice(tipos)
            metodo = random.choice(metodos)
            punto_venta = "0001"
            numero = f"{last_num + 1 + i:08d}"
            fecha = (hoy - timedelta(days=random.randint(0, 120))).isoformat()
            domicilio = generar_direccion()
            
            cant_items = random.randint(1, 5)
            subtotal = 0.0
            iva_total = 0.0
            items_data = []
            
            for _ in range(cant_items):
                art = random.choice(ARTICULOS_FACTURA)
                cantidad = round(random.uniform(1, 3), 2)
                precio = round(random.uniform(2500, 25000), 2)
                iva_pct = random.choice([0.0, 10.5, 21.0])
                sub = round(cantidad * precio, 2)
                iva_monto = round(sub * (iva_pct / 100.0), 2)
                tot = round(sub + iva_monto, 2)
                subtotal += sub
                iva_total += iva_monto
                items_data.append((art, cantidad, precio, iva_pct, sub, tot))
            
            total = round(subtotal + iva_total, 2)
            
            venta = Sale(
                lubricentro_id=current_user.lubricentro_id,
                fecha=fecha,
                tipo=tipo,
                punto_venta=punto_venta,
                numero=numero,
                metodo_pago=metodo,
                cliente_nombre=cliente.nombre,
                cliente_dni=generar_dni(),
                cliente_cuit=generar_cuit(generar_dni()),
                cliente_email=cliente.email or "",
                cliente_telefono=cliente.telefono or "",
                domicilio=domicilio,
                condicion_iva=random.choice(["Consumidor Final", "Responsable Inscripto", "Monotributo"]),
                subtotal=subtotal,
                iva=iva_total,
                total=total,
                observaciones="Comprobante generado por bot de desarrollo"
            )
            db.add(venta)
            db.flush()
            
            for art, cantidad, precio, iva_pct, sub, tot in items_data:
                item = SaleItem(
                    comprobante_id=venta.id,
                    articulo=art,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    iva_porcentaje=iva_pct,
                    subtotal=sub,
                    total=tot
                )
                db.add(item)
            
            if random.random() < 0.8:
                vehiculo_data = generar_vehiculo()
                veh = SaleVehicle(
                    comprobante_id=venta.id,
                    descripcion=vehiculo_data["descripcion"],
                    kilometraje=vehiculo_data["kilometraje"]
                )
                db.add(veh)
            
            count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} comprobantes generados con éxito", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar comprobantes: {str(e)}")
