from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.client import Client, Vehicle
from app.schemas.client_schema import ClientCreate, ClientUpdate, VehicleCreate, VehicleUpdate

class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):
    pass

class CRUDVehicle(CRUDBase[Vehicle, VehicleCreate, VehicleUpdate]):
    def get_multi_by_client(self, db: Session, *, client_id: int, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        return (
            db.query(self.model)
            .filter(Vehicle.cliente_id == client_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

client = CRUDClient(Client)
vehicle = CRUDVehicle(Vehicle)
