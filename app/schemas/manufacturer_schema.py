from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schema for creating a new blanket
class BlanketCreate(BaseModel):
    model_name: str
    material: str
    stock: int
    production_capacity: int

# Schema for returning blanket details
class BlanketOut(BaseModel):
    id: int
    model_name: str
    material: str
    stock: int
    production_capacity: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for updating production capacity
class ProductionCapacityUpdate(BaseModel):
    production_capacity: int

# Schema for updating blanket (all fields optional)
class BlanketUpdate(BaseModel):
    model_name: Optional[str] = None
    material: Optional[str] = None
    stock: Optional[int] = None
    production_capacity: Optional[int] = None

# Schema for returning production capacity
class ProductionCapacityOut(BaseModel):
    production_capacity: int

# Schema for stock availability check
class StockAvailabilityCheck(BaseModel):
    blanket_id: int
    required_quantity: int

# Schema for stock availability response
class StockAvailabilityResponse(BaseModel):
    available: bool
    current_stock: int
    message: str

# Schema for stock operation response
class StockOperationResponse(BaseModel):
    success: bool
    message: str
    manufacturer_remaining_stock: int
    distributor_stock: int
    processed_quantity: int

# Schema for available stock view (simplified)
class AvailableStockOut(BaseModel):
    id: int
    model_name: str
    material: str
    stock: int
    production_capacity: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for distributor order response
class DistributorOrderOut(BaseModel):
    id: int
    distributor_id: int
    distributor_name: str | None = None
    blanket_id: int
    blanket_name: str | None = None
    quantity: int
    order_date: datetime

    class Config:
        from_attributes = True