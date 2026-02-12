from pydantic import BaseModel
from datetime import datetime

# Schema for creating a distributor order
class DistributorOrderCreate(BaseModel):
    blanket_id: int
    quantity: int

# Schema for returning distributor order details
class DistributorOrderOut(BaseModel):
    id: int
    distributor_id: int
    distributor_name: str = None  # Will be populated from relationship
    blanket_id: int
    quantity: int
    order_date: datetime
    blanket_model_name: str = None  # Will be populated from relationship

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_relationships(cls, db_obj):
        """Create schema with data from relationships"""
        return cls(
            id=db_obj.id,
            distributor_id=db_obj.distributor_id,
            distributor_name=db_obj.user.username if db_obj.user else None,
            blanket_id=db_obj.blanket_id,
            quantity=db_obj.quantity,
            order_date=db_obj.order_date,
            blanket_model_name=db_obj.blanket.model_name if db_obj.blanket else None
        )

# Schema for creating or updating distributor stock
class DistributorStockCreate(BaseModel):
    blanket_id: int
    quantity: int

# Schema for returning distributor stock details
class DistributorStockOut(BaseModel):
    id: int
    distributor_name: str
    blanket_id: int
    blanket_name: str | None = None
    blanket_image_url: str | None = None
    quantity: int

    class Config:
        from_attributes = True

# Schema for dynamic stock purchase from manufacturer
class PurchaseFromManufacturer(BaseModel):
    blanket_id: int
    quantity: int

# Schema for dynamic stock sale to seller
class SaleToSeller(BaseModel):
    seller_name: str
    blanket_id: int
    quantity: int

# Schema for stock operation response
class StockOperationResponse(BaseModel):
    success: bool
    message: str
    remaining_stock: int
    processed_quantity: int