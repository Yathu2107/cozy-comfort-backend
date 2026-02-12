from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class AvailabilityStatus(str, Enum):
    IN_STOCK = "In stock"
    OUT_OF_STOCK = "Out of stock"

# Schema for creating or updating seller inventory
class SellerInventoryCreate(BaseModel):
    seller_name: str
    blanket_id: int
    quantity: int

# Schema for returning seller inventory details
class SellerInventoryOut(BaseModel):
    id: int
    seller_name: str
    blanket_id: int
    blanket_name: str | None = None
    blanket_image_url: str | None = None
    quantity: int

    class Config:
        from_attributes = True

# Schema for placing a customer order
class CustomerOrderCreate(BaseModel):
    customer_name: str
    seller_name: str
    blanket_id: int
    quantity: int

# Schema for returning customer order details
class CustomerOrderOut(BaseModel):
    id: int
    customer_name: str
    seller_name: str
    blanket_id: int
    blanket_name: str | None = None
    quantity: int
    status: str
    total_value: float | None = None

    class Config:
        from_attributes = True

# Schema for requesting stock from distributor
class StockRequest(BaseModel):
    seller_name: str
    blanket_id: int
    quantity: int

# Schema for updating customer order status
class OrderStatusUpdate(BaseModel):
    status: str

# Schema for dynamic stock purchase from distributor
class PurchaseFromDistributor(BaseModel):
    seller_name: str
    distributor_name: str
    blanket_id: int
    quantity: int

# Schema for dynamic customer purchase
class CustomerPurchase(BaseModel):
    customer_name: str
    seller_name: str
    blanket_id: int
    quantity: int
    total_value: Optional[float] = None  # Optional total value for validation

# Schema for stock operation response
class StockOperationResponse(BaseModel):
    success: bool
    message: str
    remaining_stock: int
    processed_quantity: int
    total_value: Optional[float] = None  # Total value of the transaction

# Schema for creating a seller order
class SellerOrderCreate(BaseModel):
    seller_id: int
    distributor_id: int
    blanket_id: int
    quantity: int

# Schema for returning seller order details
class SellerOrderOut(BaseModel):
    id: int
    seller_id: int
    seller_name: str | None = None
    distributor_id: int
    distributor_name: str | None = None
    blanket_id: int
    blanket_name: str | None = None
    quantity: int
    purchase_date: datetime

    class Config:
        from_attributes = True


# Schema for creating a product for sale
class ProductForSaleCreate(BaseModel):
    blanket_id: int
    price: float
    availability: Optional[AvailabilityStatus] = AvailabilityStatus.IN_STOCK

# Schema for updating a product for sale
class ProductForSaleUpdate(BaseModel):
    price: Optional[float] = None
    availability: Optional[AvailabilityStatus] = None

# Schema for returning product for sale details
class ProductForSaleOut(BaseModel):
    id: int
    seller_id: int
    blanket_id: int
    blanket_name: str | None = None
    blanket_image_url: str | None = None
    price: float
    quantity: int
    availability: AvailabilityStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True