from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.distributor_schema import (
    DistributorOrderOut,
    DistributorStockOut,
    PurchaseFromManufacturer,
    SaleToSeller,
    StockOperationResponse
)
from app.schemas.seller_schema import SellerOrderOut
from app.schemas.manufacturer_schema import AvailableStockOut
from app.services.distributor_service import (
    get_all_orders,
    get_distributor_stock,
    process_seller_order,
    check_distributor_stock_availability
)
from app.services.seller_service import get_seller_orders_by_distributor
from app.services.manufacturer_service import process_distributor_order, get_all_blankets
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/distributor", tags=["Distributor"])

# Get all distributor orders for the logged-in user
@router.get("/orders", response_model=list[DistributorOrderOut])
def list_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_all_orders(db, distributor_id=user.id)

# Get distributor stock for the logged-in user
@router.get("/stock", response_model=list[DistributorStockOut])
def view_stock(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_distributor_stock(db, distributor_name=user.username)

# Get sales to sellers for the logged-in distributor
@router.get("/sales-to-sellers", response_model=list[SellerOrderOut])
def view_sales_to_sellers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_seller_orders_by_distributor(db, distributor_name=user.username)

# Get all available stock from manufacturer
@router.get("/available-stock", response_model=list[AvailableStockOut])
def view_available_stock(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_all_blankets(db)

# Purchase stock from manufacturer (dynamic stock transfer)
@router.post("/purchase-from-manufacturer", response_model=StockOperationResponse)
def purchase_from_manufacturer(
    data: PurchaseFromManufacturer, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    try:
        # Use authenticated user instead of asking for distributor_name
        result = process_distributor_order(db, data.blanket_id, data.quantity, user.username, user)
        return StockOperationResponse(
            success=True,
            message=f"Successfully purchased {data.quantity} units from manufacturer",
            remaining_stock=result["distributor_stock"],
            processed_quantity=result["processed_quantity"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Sell stock to seller (dynamic stock transfer)
@router.post("/sell-to-seller", response_model=StockOperationResponse)
def sell_to_seller(
    data: SaleToSeller, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    try:
        # Use authenticated user's username as distributor_name
        result = process_seller_order(db, data.blanket_id, data.quantity, user.username, data.seller_name)
        return StockOperationResponse(
            success=True,
            message=f"Successfully sold {data.quantity} units to {data.seller_name}",
            remaining_stock=result["distributor_remaining_stock"],
            processed_quantity=result["processed_quantity"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Check stock availability
@router.get("/check-stock/{blanket_id}/{required_quantity}")
def check_stock_availability(
    blanket_id: int, 
    required_quantity: int, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    # Use authenticated user's username as distributor_name
    return check_distributor_stock_availability(db, user.username, blanket_id, required_quantity)