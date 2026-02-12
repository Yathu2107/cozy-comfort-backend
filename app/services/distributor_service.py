from sqlalchemy.orm import Session, joinedload
from app.models.distributor_model import DistributorOrder, DistributorStock
from app.models.seller_model import SellerInventory, SellerOrder
from app.models.user_model import User
from app.schemas.distributor_schema import DistributorOrderCreate, DistributorStockCreate

# Place a new order to the manufacturer
def place_order(db: Session, data: DistributorOrderCreate, user):
    order = DistributorOrder(
        distributor_id=user.id,
        blanket_id=data.blanket_id,
        quantity=data.quantity
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Load the relationships to include names in response
    order = db.query(DistributorOrder).options(
        joinedload(DistributorOrder.blanket),
        joinedload(DistributorOrder.user)
    ).filter(DistributorOrder.id == order.id).first()
    
    return {
        "id": order.id,
        "distributor_id": order.distributor_id,
        "distributor_name": order.user.username if order.user else None,
        "blanket_id": order.blanket_id,
        "quantity": order.quantity,
        "order_date": order.order_date,
        "blanket_model_name": order.blanket.model_name if order.blanket else None
    }

# Get all distributor orders
def get_all_orders(db: Session, distributor_id: int = None):
    query = db.query(DistributorOrder).options(
        joinedload(DistributorOrder.blanket), 
        joinedload(DistributorOrder.user)
    )
    
    if distributor_id is not None:
        query = query.filter(DistributorOrder.distributor_id == distributor_id)
    
    orders = query.all()
    
    # Convert to response format with names from relationships
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "distributor_id": order.distributor_id,
            "distributor_name": order.user.username if order.user else None,
            "blanket_id": order.blanket_id,
            "quantity": order.quantity,
            "order_date": order.order_date,
            "blanket_model_name": order.blanket.model_name if order.blanket else None
        })
    
    return result

# Get distributor stock
def get_distributor_stock(db: Session, blanket_id: int = None, distributor_name: str = None):
    from sqlalchemy.orm import joinedload
    query = db.query(DistributorStock).options(joinedload(DistributorStock.blanket))

    if distributor_name is not None:
        query = query.filter(DistributorStock.distributor_name == distributor_name)

    if blanket_id is not None:
        stock = query.filter(DistributorStock.blanket_id == blanket_id).first()
        if not stock:
            return None
        return {
            "id": stock.id,
            "distributor_name": stock.distributor_name,
            "blanket_id": stock.blanket_id,
            "blanket_name": stock.blanket.model_name if stock.blanket else None,
            "blanket_image_url": stock.blanket.image_url if stock.blanket else None,
            "quantity": stock.quantity
        }
    stocks = query.all()
    result = []
    for stock in stocks:
        result.append({
            "id": stock.id,
            "distributor_name": stock.distributor_name,
            "blanket_id": stock.blanket_id,
            "blanket_name": stock.blanket.model_name if stock.blanket else None,
            "blanket_image_url": stock.blanket.image_url if stock.blanket else None,
            "quantity": stock.quantity
        })
    return result

# Update distributor stock (create or modify)
def update_distributor_stock(db: Session, data: DistributorStockCreate, user):
    stock = db.query(DistributorStock).filter(
        DistributorStock.distributor_name == user.username,
        DistributorStock.blanket_id == data.blanket_id
    ).first()

    if stock:
        stock.quantity = data.quantity
    else:
        stock = DistributorStock(
            distributor_name=user.username,
            blanket_id=data.blanket_id,
            quantity=data.quantity
        )
        db.add(stock)

    db.commit()
    db.refresh(stock)
    return stock

# Process seller order and update distributor stock
def process_seller_order(db: Session, blanket_id: int, quantity: int, distributor_name: str, seller_name: str):
    """
    Process seller order by:
    1. Checking distributor stock availability
    2. Decreasing distributor stock
    3. Adding/updating seller inventory
    4. Creating seller order record
    """
    # Get seller and distributor user IDs
    seller_user = db.query(User).filter(User.username == seller_name).first()
    distributor_user = db.query(User).filter(User.username == distributor_name).first()
    
    if not seller_user:
        raise ValueError(f"Seller '{seller_name}' not found")
    if not distributor_user:
        raise ValueError(f"Distributor '{distributor_name}' not found")
    
    # Check distributor stock
    distributor_stock = db.query(DistributorStock).filter(
        DistributorStock.distributor_name == distributor_name,
        DistributorStock.blanket_id == blanket_id
    ).first()
    
    if not distributor_stock:
        raise ValueError(f"No stock found for distributor {distributor_name} and blanket {blanket_id}")
    
    if distributor_stock.quantity < quantity:
        raise ValueError(f"Insufficient distributor stock. Available: {distributor_stock.quantity}, Requested: {quantity}")
    
    # Decrease distributor stock
    distributor_stock.quantity -= quantity
    
    # Check if seller already has inventory for this blanket
    seller_inventory = db.query(SellerInventory).filter(
        SellerInventory.seller_name == seller_name,
        SellerInventory.blanket_id == blanket_id
    ).first()
    
    if seller_inventory:
        # Add to existing inventory
        seller_inventory.quantity += quantity
    else:
        # Create new seller inventory entry
        seller_inventory = SellerInventory(
            seller_name=seller_name,
            blanket_id=blanket_id,
            quantity=quantity
        )
        db.add(seller_inventory)
    
    # Create seller order record
    seller_order = SellerOrder(
        seller_id=seller_user.id,
        distributor_id=distributor_user.id,
        blanket_id=blanket_id,
        quantity=quantity
    )
    db.add(seller_order)
    
    db.commit()
    db.refresh(distributor_stock)
    db.refresh(seller_inventory)
    db.refresh(seller_order)
    
    # Sync product for sale quantity if it exists
    try:
        from app.services.seller_service import sync_product_quantity_with_inventory
        sync_product_quantity_with_inventory(db, seller_name, blanket_id)
    except (ValueError, ImportError):
        # Product for sale doesn't exist or import fails, which is fine
        pass
    
    return {
        "distributor_remaining_stock": distributor_stock.quantity,
        "seller_inventory": seller_inventory.quantity,
        "processed_quantity": quantity,
        "seller_order_id": seller_order.id
    }

# Check distributor stock availability
def check_distributor_stock_availability(db: Session, distributor_name: str, blanket_id: int, required_quantity: int):
    """Check if distributor has sufficient stock for the requested quantity"""
    distributor_stock = db.query(DistributorStock).filter(
        DistributorStock.distributor_name == distributor_name,
        DistributorStock.blanket_id == blanket_id
    ).first()
    
    if not distributor_stock:
        return {"available": False, "current_stock": 0, "message": "No stock found for this distributor and blanket"}
    
    if distributor_stock.quantity >= required_quantity:
        return {"available": True, "current_stock": distributor_stock.quantity, "message": "Stock available"}
    else:
        return {
            "available": False, 
            "current_stock": distributor_stock.quantity, 
            "message": f"Insufficient stock. Available: {distributor_stock.quantity}, Required: {required_quantity}"
        }