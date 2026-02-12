from sqlalchemy.orm import Session
from app.models.manufacturer_model import Blanket
from app.models.distributor_model import DistributorStock, DistributorOrder
from app.schemas.manufacturer_schema import BlanketCreate, ProductionCapacityUpdate, BlanketUpdate
from typing import Optional

# Create a new blanket
def create_blanket(db: Session, data: BlanketCreate, image_url: Optional[str] = None):
    blanket = Blanket(
        model_name=data.model_name,
        material=data.material,
        stock=data.stock,
        production_capacity=data.production_capacity,
        image_url=image_url
    )
    db.add(blanket)
    db.commit()
    db.refresh(blanket)
    return blanket

# Get all blankets
def get_all_blankets(db: Session):
    blankets = db.query(Blanket).all()
    result = []
    for blanket in blankets:
        result.append({
            "id": blanket.id,
            "model_name": blanket.model_name,
            "material": blanket.material,
            "stock": blanket.stock,
            "production_capacity": blanket.production_capacity,
            "image_url": blanket.image_url
        })
    return result

# Get a specific blanket by ID
def get_blanket_by_id(db: Session, blanket_id: int):
    return db.query(Blanket).filter(Blanket.id == blanket_id).first()

# Update stock for a blanket
def update_blanket_stock(db: Session, blanket_id: int, quantity: int):
    blanket = db.query(Blanket).filter(Blanket.id == blanket_id).first()
    if not blanket:
        return None
    blanket.stock = quantity
    db.commit()
    db.refresh(blanket)
    return blanket

# Get production capacity by blanket ID
def get_production_capacity(db: Session, blanket_id: int):
    blanket = db.query(Blanket).filter(Blanket.id == blanket_id).first()
    if not blanket:
        return {"production_capacity": 0}
    return {"production_capacity": blanket.production_capacity}

# Update production capacity by blanket ID
def update_production_capacity(db: Session, blanket_id: int, data: ProductionCapacityUpdate):
    blanket = db.query(Blanket).filter(Blanket.id == blanket_id).first()
    if not blanket:
        return {"production_capacity": 0}
    blanket.production_capacity = data.production_capacity
    db.commit()
    db.refresh(blanket)
    return {"production_capacity": blanket.production_capacity}

# Process distributor order and update manufacturer stock
def process_distributor_order(db: Session, blanket_id: int, quantity: int, distributor_name: str, user):
    """
    Process distributor order by:
    1. Checking manufacturer stock availability
    2. Decreasing manufacturer stock
    3. Adding/updating distributor stock
    4. Creating distributor order record
    """
    # Check manufacturer stock
    blanket = db.query(Blanket).filter(Blanket.id == blanket_id).first()
    if not blanket:
        raise ValueError("Blanket not found")
    
    if blanket.stock < quantity:
        raise ValueError(f"Insufficient manufacturer stock. Available: {blanket.stock}, Requested: {quantity}")
    
    # Decrease manufacturer stock
    blanket.stock -= quantity
    
    # Check if distributor already has stock for this blanket
    distributor_stock = db.query(DistributorStock).filter(
        DistributorStock.distributor_name == distributor_name,
        DistributorStock.blanket_id == blanket_id
    ).first()
    
    if distributor_stock:
        # Add to existing stock
        distributor_stock.quantity += quantity
    else:
        # Create new distributor stock entry
        distributor_stock = DistributorStock(
            distributor_name=distributor_name,
            blanket_id=blanket_id,
            quantity=quantity
        )
        db.add(distributor_stock)
    
    # Create distributor order record
    distributor_order = DistributorOrder(
        distributor_id=user.id,
        blanket_id=blanket_id,
        quantity=quantity
    )
    db.add(distributor_order)
    
    db.commit()
    db.refresh(blanket)
    db.refresh(distributor_stock)
    db.refresh(distributor_order)
    
    return {
        "manufacturer_remaining_stock": blanket.stock,
        "distributor_stock": distributor_stock.quantity,
        "processed_quantity": quantity,
        "order_id": distributor_order.id
    }

# Check stock availability for a blanket
def check_stock_availability(db: Session, blanket_id: int, required_quantity: int):
    """Check if manufacturer has sufficient stock for the requested quantity"""
    blanket = db.query(Blanket).filter(Blanket.id == blanket_id).first()
    if not blanket:
        return {"available": False, "current_stock": 0, "message": "Blanket not found"}
    
    if blanket.stock >= required_quantity:
        return {"available": True, "current_stock": blanket.stock, "message": "Stock available"}
    else:
        return {
            "available": False, 
            "current_stock": blanket.stock, 
            "message": f"Insufficient stock. Available: {blanket.stock}, Required: {required_quantity}"
        }

# Get all distributor orders
def get_all_distributor_orders(db: Session):
    """Get all distributor orders with related blanket and user information"""
    from sqlalchemy.orm import joinedload
    orders = db.query(DistributorOrder).options(
        joinedload(DistributorOrder.blanket),
        joinedload(DistributorOrder.user)
    ).all()
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "distributor_id": order.distributor_id,
            "distributor_name": order.user.username if order.user else None,
            "blanket_id": order.blanket_id,
            "blanket_name": order.blanket.model_name if order.blanket else None,
            "quantity": order.quantity,
            "order_date": order.order_date
        })
    return result

# Update blanket image
def update_blanket_image(db: Session, blanket_id: int, image_url: str):
    """Update the image URL for a specific blanket"""
    blanket = db.query(Blanket).filter(Blanket.id == blanket_id).first()
    if not blanket:
        return None
    
    old_image_url = blanket.image_url
    blanket.image_url = image_url
    db.commit()
    db.refresh(blanket)
    
    return {"blanket": blanket, "old_image_url": old_image_url}

# Comprehensive update function for blankets
def update_blanket(db: Session, blanket_id: int, update_data: Optional[BlanketUpdate] = None, image_url: Optional[str] = None):
    """Update blanket with any combination of fields including image"""
    blanket = db.query(Blanket).filter(Blanket.id == blanket_id).first()
    if not blanket:
        return None
    
    old_image_url = blanket.image_url
    
    # Update fields if provided
    if update_data:
        if update_data.model_name is not None:
            blanket.model_name = update_data.model_name
        if update_data.material is not None:
            blanket.material = update_data.material
        if update_data.stock is not None:
            blanket.stock = update_data.stock
        if update_data.production_capacity is not None:
            blanket.production_capacity = update_data.production_capacity
    
    # Update image if provided
    if image_url is not None:
        blanket.image_url = image_url
    
    db.commit()
    db.refresh(blanket)
    
    return {"blanket": blanket, "old_image_url": old_image_url}