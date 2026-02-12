from sqlalchemy.orm import Session
from app.models.seller_model import SellerInventory, CustomerOrder, SellerOrder, ProductForSale, AvailabilityStatus
from app.models.user_model import User
from app.schemas.seller_schema import CustomerOrderCreate, StockRequest, ProductForSaleCreate, ProductForSaleUpdate

# View available products (from seller's inventory)
def get_available_products(db: Session):
    return db.query(SellerInventory).all()

# Place a customer order
def place_customer_order(db: Session, data: CustomerOrderCreate, current_user=None):
    # Determine status based on who is placing the order
    if current_user and current_user.role == "seller":
        status = "completed"
    else:
        status = "pending"
    
    order = CustomerOrder(
        customer_name=data.customer_name,
        seller_name=data.seller_name,
        blanket_id=data.blanket_id,
        quantity=data.quantity,
        status=status
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

# Get status of a customer order
def get_order_status(db: Session, order_id: int):
    return db.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()

# Request stock from distributor (simulated by adding to seller inventory)
def request_stock_from_distributor(db: Session, data: StockRequest):
    stock = db.query(SellerInventory).filter(
        SellerInventory.seller_name == data.seller_name,
        SellerInventory.blanket_id == data.blanket_id
    ).first()

    if stock:
        stock.quantity += data.quantity
    else:
        stock = SellerInventory(
            seller_name=data.seller_name,
            blanket_id=data.blanket_id,
            quantity=data.quantity
        )
        db.add(stock)

    db.commit()
    db.refresh(stock)
    
    # Sync product for sale quantity if it exists
    try:
        sync_product_quantity_with_inventory(db, data.seller_name, data.blanket_id)
    except ValueError:
        # Product for sale doesn't exist, which is fine
        pass
    
    return stock

# View seller's own inventory
def get_seller_inventory(db: Session):
    return db.query(SellerInventory).all()

# Get seller inventory by seller name
def get_seller_inventory_by_name(db: Session, seller_name: str):
    from sqlalchemy.orm import joinedload
    inventories = db.query(SellerInventory).options(joinedload(SellerInventory.blanket)).filter(SellerInventory.seller_name == seller_name).all()
    result = []
    for inv in inventories:
        result.append({
            "id": inv.id,
            "seller_name": inv.seller_name,
            "blanket_id": inv.blanket_id,
            "blanket_name": inv.blanket.model_name if inv.blanket else None,
            "blanket_image_url": inv.blanket.image_url if inv.blanket else None,
            "quantity": inv.quantity
        })
    return result

# Update status of a customer order
def update_order_status(db: Session, order_id: int, status: str):
    order = db.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not order:
        return None
    order.status = status
    db.commit()
    db.refresh(order)
    return order

# Process customer order and update seller inventory
def process_customer_order(db: Session, blanket_id: int, quantity: int, seller_name: str, customer_name: str, current_user=None, provided_total_value=None):
    """
    Process customer order by:
    1. Checking seller inventory availability
    2. Decreasing seller inventory
    3. Creating customer order record
    4. Syncing product for sale quantities
    """
    # Check seller inventory
    seller_inventory = db.query(SellerInventory).filter(
        SellerInventory.seller_name == seller_name,
        SellerInventory.blanket_id == blanket_id
    ).first()
    
    if not seller_inventory:
        raise ValueError(f"No inventory found for seller {seller_name} and blanket {blanket_id}")
    
    if seller_inventory.quantity < quantity:
        raise ValueError(f"Insufficient seller inventory. Available: {seller_inventory.quantity}, Requested: {quantity}")
    
    # Decrease seller inventory
    seller_inventory.quantity -= quantity
    
    # Determine order status based on user role
    status = "completed" if current_user and current_user.role == "seller" else "pending"
    
    # Get product price for this blanket and seller
    product = db.query(ProductForSale).filter(
        ProductForSale.seller_id == db.query(User.id).filter(User.username == seller_name).scalar(),
        ProductForSale.blanket_id == blanket_id
    ).first()
    
    # Calculate total value
    calculated_total_value = None
    if product:
        calculated_total_value = product.price * quantity
    
    # Validate provided total value if given
    if provided_total_value is not None and calculated_total_value is not None:
        if abs(provided_total_value - calculated_total_value) > 0.01:  # Allow small floating point differences
            raise ValueError(f"Total value mismatch. Expected: {calculated_total_value}, Provided: {provided_total_value}")
    
    # Use calculated total value
    total_value = calculated_total_value

    # Create customer order
    customer_order = CustomerOrder(
        customer_name=customer_name,
        seller_name=seller_name,
        blanket_id=blanket_id,
        quantity=quantity,
        status=status,
        total_value=total_value
    )
    db.add(customer_order)
    
    db.commit()
    db.refresh(seller_inventory)
    db.refresh(customer_order)
    
    # Sync product for sale quantity if it exists
    try:
        sync_product_quantity_with_inventory(db, seller_name, blanket_id)
    except ValueError:
        # Product for sale doesn't exist, which is fine
        pass
    
    return {
        "seller_remaining_inventory": seller_inventory.quantity,
        "customer_order": customer_order,
        "processed_quantity": quantity
    }

# Check seller inventory availability
def check_seller_inventory_availability(db: Session, seller_name: str, blanket_id: int, required_quantity: int):
    """Check if seller has sufficient inventory for the requested quantity"""
    seller_inventory = db.query(SellerInventory).filter(
        SellerInventory.seller_name == seller_name,
        SellerInventory.blanket_id == blanket_id
    ).first()
    
    if not seller_inventory:
        return {"available": False, "current_stock": 0, "message": "No inventory found for this seller and blanket"}
    
    if seller_inventory.quantity >= required_quantity:
        return {"available": True, "current_stock": seller_inventory.quantity, "message": "Inventory available"}
    else:
        return {
            "available": False, 
            "current_stock": seller_inventory.quantity, 
            "message": f"Insufficient inventory. Available: {seller_inventory.quantity}, Required: {required_quantity}"
        }

# Get seller inventory by seller name and blanket ID
def get_seller_inventory_by_blanket(db: Session, seller_name: str, blanket_id: int):
    """Get specific seller inventory for a blanket"""
    return db.query(SellerInventory).filter(
        SellerInventory.seller_name == seller_name,
        SellerInventory.blanket_id == blanket_id
    ).first()

# Get seller orders by seller ID
def get_seller_orders(db: Session, seller_id: int):
    """Get all orders placed by a seller"""
    return db.query(SellerOrder).filter(SellerOrder.seller_id == seller_id).all()

# Get seller orders by seller name
def get_seller_orders_by_name(db: Session, seller_name: str):
    """Get all orders placed by a seller using seller name"""
    seller = db.query(User).filter(User.username == seller_name).first()
    if not seller:
        return []
    return db.query(SellerOrder).filter(SellerOrder.seller_id == seller.id).all()

# Get all seller orders (admin function)
def get_all_seller_orders(db: Session):
    """Get all seller orders from the database"""
    return db.query(SellerOrder).all()

# Get seller orders by distributor name
def get_seller_orders_by_distributor(db: Session, distributor_name: str):
    """Get all orders that were sold by a distributor to sellers"""
    from sqlalchemy.orm import joinedload
    distributor = db.query(User).filter(User.username == distributor_name).first()
    if not distributor:
        return []
    orders = db.query(SellerOrder).options(
        joinedload(SellerOrder.seller),
        joinedload(SellerOrder.blanket)
    ).filter(SellerOrder.distributor_id == distributor.id).all()
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "seller_id": order.seller_id,
            "seller_name": order.seller.username if order.seller else None,
            "distributor_id": order.distributor_id,
            "blanket_id": order.blanket_id,
            "blanket_name": order.blanket.model_name if order.blanket else None,
            "quantity": order.quantity,
            "purchase_date": order.purchase_date
        })
    return result


# Customer order related functions

def get_customer_orders_by_seller(db: Session, seller_name: str):
    """Get all customer orders for a specific seller with blanket names"""
    from sqlalchemy.orm import joinedload
    orders = db.query(CustomerOrder).options(joinedload(CustomerOrder.blanket)).filter(CustomerOrder.seller_name == seller_name).all()
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "customer_name": order.customer_name,
            "seller_name": order.seller_name,
            "blanket_id": order.blanket_id,
            "blanket_name": order.blanket.model_name if order.blanket else None,
            "quantity": order.quantity,
            "status": order.status,
            "total_value": order.total_value
        })
    return result


def get_all_customer_orders(db: Session):
    """Get all customer orders from all sellers"""
    return db.query(CustomerOrder).all()


def get_customer_orders_by_customer(db: Session, customer_name: str):
    """Get all orders placed by a specific customer"""
    return db.query(CustomerOrder).filter(CustomerOrder.customer_name == customer_name).all()


# ProductForSale related functions

def create_product_for_sale(db: Session, seller_username: str, data: ProductForSaleCreate):
    """Create a new product for sale by automatically getting quantity from seller inventory"""
    # Get seller ID
    seller = db.query(User).filter(User.username == seller_username).first()
    if not seller:
        raise ValueError(f"Seller {seller_username} not found")
    
    # Check if seller has inventory for this blanket
    seller_inventory = db.query(SellerInventory).filter(
        SellerInventory.seller_name == seller_username,
        SellerInventory.blanket_id == data.blanket_id
    ).first()
    
    if not seller_inventory:
        raise ValueError(f"No inventory found for blanket {data.blanket_id}")
    
    # Check if product already exists
    existing_product = db.query(ProductForSale).filter(
        ProductForSale.seller_id == seller.id,
        ProductForSale.blanket_id == data.blanket_id
    ).first()
    
    if existing_product:
        raise ValueError(f"Product for blanket {data.blanket_id} already exists")
    
    # Determine availability based on quantity
    availability = AvailabilityStatus.IN_STOCK if seller_inventory.quantity > 0 else AvailabilityStatus.OUT_OF_STOCK
    
    # Create product for sale
    product = ProductForSale(
        seller_id=seller.id,
        blanket_id=data.blanket_id,
        price=data.price,
        quantity=seller_inventory.quantity,
        availability=availability
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product_for_sale(db: Session, seller_username: str, product_id: int, data: ProductForSaleUpdate):
    """Update a product for sale"""
    # Get seller ID
    seller = db.query(User).filter(User.username == seller_username).first()
    if not seller:
        raise ValueError(f"Seller {seller_username} not found")
    
    # Get product
    product = db.query(ProductForSale).filter(
        ProductForSale.id == product_id,
        ProductForSale.seller_id == seller.id
    ).first()
    
    if not product:
        raise ValueError("Product not found")
    
    # Update fields
    if data.price is not None:
        product.price = data.price
    
    if data.availability is not None:
        product.availability = data.availability
    
    db.commit()
    db.refresh(product)
    return product


def get_products_for_sale_by_seller(db: Session, seller_username: str):
    """Get all products for sale by a seller"""
    from sqlalchemy.orm import joinedload
    seller = db.query(User).filter(User.username == seller_username).first()
    if not seller:
        return []
    products = db.query(ProductForSale).options(joinedload(ProductForSale.blanket)).filter(ProductForSale.seller_id == seller.id).all()
    result = []
    for product in products:
        result.append({
            "id": product.id,
            "seller_id": product.seller_id,
            "blanket_id": product.blanket_id,
            "blanket_name": product.blanket.model_name if product.blanket else None,
            "blanket_image_url": product.blanket.image_url if product.blanket else None,
            "price": product.price,
            "quantity": product.quantity,
            "availability": product.availability,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        })
    return result


def get_all_products_for_sale(db: Session):
    """Get all products for sale"""
    return db.query(ProductForSale).all()


def get_product_for_sale_by_id(db: Session, product_id: int):
    """Get a specific product for sale by ID"""
    return db.query(ProductForSale).filter(ProductForSale.id == product_id).first()


def get_product_for_sale_by_seller_and_blanket(db: Session, seller_name: str, blanket_id: int):
    """Get a specific product for sale by seller name and blanket ID"""
    # Get seller ID first
    seller = db.query(User).filter(User.username == seller_name).first()
    if not seller:
        return None
    
    return db.query(ProductForSale).filter(
        ProductForSale.seller_id == seller.id,
        ProductForSale.blanket_id == blanket_id
    ).first()


def sync_product_quantity_with_inventory(db: Session, seller_username: str, blanket_id: int):
    """Sync product quantity and availability with seller inventory"""
    # Get seller ID
    seller = db.query(User).filter(User.username == seller_username).first()
    if not seller:
        raise ValueError(f"Seller {seller_username} not found")
    
    # Get seller inventory
    seller_inventory = db.query(SellerInventory).filter(
        SellerInventory.seller_name == seller_username,
        SellerInventory.blanket_id == blanket_id
    ).first()
    
    if not seller_inventory:
        raise ValueError(f"No inventory found for blanket {blanket_id}")
    
    # Get product for sale
    product = db.query(ProductForSale).filter(
        ProductForSale.seller_id == seller.id,
        ProductForSale.blanket_id == blanket_id
    ).first()
    
    if not product:
        raise ValueError(f"No product for sale found for blanket {blanket_id}")
    
    # Update quantity
    product.quantity = seller_inventory.quantity
    
    # Update availability based on quantity
    if seller_inventory.quantity == 0:
        product.availability = AvailabilityStatus.OUT_OF_STOCK
    elif product.availability == AvailabilityStatus.OUT_OF_STOCK and seller_inventory.quantity > 0:
        product.availability = AvailabilityStatus.IN_STOCK
    
    db.commit()
    db.refresh(product)
    return product


def delete_product_for_sale(db: Session, seller_username: str, product_id: int):
    """Delete a product for sale"""
    # Get seller ID
    seller = db.query(User).filter(User.username == seller_username).first()
    if not seller:
        raise ValueError(f"Seller {seller_username} not found")
    
    # Get product
    product = db.query(ProductForSale).filter(
        ProductForSale.id == product_id,
        ProductForSale.seller_id == seller.id
    ).first()
    
    if not product:
        raise ValueError("Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}