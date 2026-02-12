from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.distributor_service import process_seller_order, get_distributor_stock
from app.middleware.auth_middleware import get_current_user
from app.schemas.seller_schema import (
    SellerInventoryOut,
    CustomerOrderOut,
    OrderStatusUpdate,
    PurchaseFromDistributor,
    CustomerPurchase,
    StockOperationResponse,
    ProductForSaleCreate,
    ProductForSaleUpdate,
    ProductForSaleOut,
    SellerOrderOut
)
from app.schemas.distributor_schema import DistributorStockOut
from app.services.seller_service import (
    get_order_status,
    get_seller_inventory_by_name,
    update_order_status,
    process_customer_order,
    create_product_for_sale,
    update_product_for_sale,
    get_products_for_sale_by_seller,
    get_product_for_sale_by_seller_and_blanket,
    get_customer_orders_by_seller,
    get_seller_orders_by_name
)

router = APIRouter(prefix="/seller", tags=["Seller"])

# Get all purchase history (seller_orders) for the logged-in seller
@router.get("/purchase-history", response_model=list[SellerOrderOut])
def get_purchase_history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Get all purchase history (seller_orders) for the logged-in seller.
    Populates seller_name and blanket_name fields.
    """
    orders = get_seller_orders_by_name(db, user.username)
    result = []
    for order in orders:
        # Get distributor name by querying User table
        from app.models.user_model import User
        distributor = db.query(User).filter(User.id == order.distributor_id).first()
        distributor_name = distributor.username if distributor else None
        
        result.append({
            "id": order.id,
            "seller_id": order.seller_id,
            "seller_name": order.seller.username if hasattr(order, 'seller') and order.seller else user.username,
            "distributor_id": order.distributor_id,
            "distributor_name": distributor_name,
            "blanket_id": order.blanket_id,
            "blanket_name": order.blanket.model_name if hasattr(order, 'blanket') and order.blanket else None,
            "quantity": order.quantity,
            "purchase_date": order.purchase_date
        })
    return result


# Get status of a customer order
@router.get("/order-status/{order_id}", response_model=CustomerOrderOut)
def check_order_status(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = get_order_status(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# Get all customer orders for the logged-in seller
@router.get("/customer-orders", response_model=list[CustomerOrderOut])
def get_my_customer_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Get all customer orders where the logged-in user is the seller.
    This shows all sales made by the current seller to customers.
    """
    return get_customer_orders_by_seller(db, user.username)


# View seller's own inventory
@router.get("/inventory", response_model=list[SellerInventoryOut])
def view_inventory(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_seller_inventory_by_name(db, user.username)


# Get available stock from distributors
@router.get("/distributor-stock", response_model=list[DistributorStockOut])
def get_available_distributor_stock(
    distributor_name: str = None,
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Get available stock from distributors. 
    Optionally filter by distributor name.
    """
    return get_distributor_stock(db, distributor_name=distributor_name)


# Update status of a customer order
@router.put("/order-status/{order_id}", response_model=CustomerOrderOut)
def update_customer_order_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = update_order_status(db, order_id, data.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or update failed")
    return order


# Purchase stock from distributor (dynamic stock transfer)
@router.post("/request-stock", response_model=StockOperationResponse)
def purchase_from_distributor(
    data: PurchaseFromDistributor, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    try:
        result = process_seller_order(db, data.blanket_id, data.quantity, data.distributor_name, data.seller_name)
        return StockOperationResponse(
            success=True,
            message=f"Successfully purchased {data.quantity} units from {data.distributor_name}",
            remaining_stock=result["seller_inventory"],
            processed_quantity=result["processed_quantity"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Process customer purchase (dynamic stock transfer) - Only for products added to sale
@router.post("/customer-purchase", response_model=StockOperationResponse)
def customer_purchase(
    data: CustomerPurchase, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    try:
        # First check if the product is available for sale
        product_for_sale = get_product_for_sale_by_seller_and_blanket(db, data.seller_name, data.blanket_id)
        
        if not product_for_sale:
            raise HTTPException(
                status_code=400, 
                detail=f"Product with blanket ID {data.blanket_id} is not available for sale by {data.seller_name}. Seller must add it to products for sale first."
            )
        
        # Check if product is in stock
        if product_for_sale.availability.value == "Out of stock":
            raise HTTPException(
                status_code=400,
                detail=f"Product is currently out of stock"
            )
        
        # Check if requested quantity is available
        if product_for_sale.quantity < data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity available. Available: {product_for_sale.quantity}, Requested: {data.quantity}"
            )
        
        result = process_customer_order(db, data.blanket_id, data.quantity, data.seller_name, data.customer_name, current_user=user, provided_total_value=data.total_value)
        return StockOperationResponse(
            success=True,
            message=f"Successfully processed purchase for {data.customer_name}",
            remaining_stock=result["seller_remaining_inventory"],
            processed_quantity=result["processed_quantity"],
            total_value=result["customer_order"].total_value
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Create a new product for sale
@router.post("/products-for-sale", response_model=ProductForSaleOut, status_code=status.HTTP_201_CREATED)
def create_product_for_sale_endpoint(
    data: ProductForSaleCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        product = create_product_for_sale(db, user.username, data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Get all products for sale by current seller
@router.get("/products-for-sale", response_model=list[ProductForSaleOut])
def get_my_products_for_sale(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return get_products_for_sale_by_seller(db, user.username)


# Update a product for sale
@router.put("/products-for-sale/{product_id}", response_model=ProductForSaleOut)
def update_product_for_sale_endpoint(
    product_id: int,
    data: ProductForSaleUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        product = update_product_for_sale(db, user.username, product_id, data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")