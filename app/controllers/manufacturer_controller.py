from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.manufacturer_schema import (
    BlanketCreate, 
    BlanketOut, 
    BlanketUpdate,
    StockAvailabilityCheck,
    StockAvailabilityResponse,
    StockOperationResponse,
    DistributorOrderOut
)
from app.services.manufacturer_service import (
    create_blanket,
    get_all_blankets,
    get_blanket_by_id,
    update_blanket,
    process_distributor_order,
    check_stock_availability,
    get_all_distributor_orders
)
from app.services.auth_service import get_current_user
from app.utils.file_handler import save_image, validate_image_file
from typing import Optional

router = APIRouter(prefix="/manufacturer", tags=["Manufacturer"])

# Create a new blanket model
@router.post("/blankets", response_model=BlanketOut, status_code=status.HTTP_201_CREATED)
async def add_blanket(
    model_name: str = Form(...),
    material: str = Form(...),
    stock: int = Form(...),
    production_capacity: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    # Validate image if provided
    if image and not validate_image_file(image):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file. Allowed formats: jpg, jpeg, png, gif, bmp, webp"
        )
    
    # Save image if provided
    image_url = None
    if image:
        try:
            image_url = await save_image(image)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
    
    # Create blanket data
    blanket_data = BlanketCreate(
        model_name=model_name,
        material=material,
        stock=stock,
        production_capacity=production_capacity
    )
    
    return create_blanket(db, blanket_data, image_url)

# Get all blanket models
@router.get("/blankets", response_model=list[BlanketOut])
def list_blankets(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_all_blankets(db)

# Get a specific blanket by ID
@router.get("/blankets/{blanket_id}", response_model=BlanketOut)
def get_blanket(blanket_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    blanket = get_blanket_by_id(db, blanket_id)
    if not blanket:
        raise HTTPException(status_code=404, detail="Blanket not found")
    return blanket

# Update blanket (comprehensive update for all fields including image)
@router.put("/blankets/{blanket_id}", response_model=BlanketOut)
async def update_blanket_comprehensive(
    blanket_id: int,
    model_name: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    production_capacity: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # Check if blanket exists
    existing_blanket = get_blanket_by_id(db, blanket_id)
    if not existing_blanket:
        raise HTTPException(status_code=404, detail="Blanket not found")
    
    # Validate image if provided
    if image and not validate_image_file(image):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file. Allowed formats: jpg, jpeg, png, gif, bmp, webp"
        )
    
    # Prepare update data
    update_data = None
    if any([model_name is not None, material is not None, stock is not None, production_capacity is not None]):
        update_data = BlanketUpdate(
            model_name=model_name,
            material=material,
            stock=stock,
            production_capacity=production_capacity
        )
    
    # Handle image upload if provided
    new_image_url = None
    if image:
        try:
            new_image_url = await save_image(image)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
    
    # Update blanket
    result = update_blanket(db, blanket_id, update_data, new_image_url)
    if not result:
        raise HTTPException(status_code=404, detail="Blanket not found")
    
    # Delete old image if a new one was uploaded
    if new_image_url and result["old_image_url"]:
        from app.utils.file_handler import delete_image
        delete_image(result["old_image_url"])
    
    return result["blanket"]

# Check stock availability
@router.post("/check-stock", response_model=StockAvailabilityResponse)
def check_stock(data: StockAvailabilityCheck, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return check_stock_availability(db, data.blanket_id, data.required_quantity)

# Process distributor order (dynamic stock transfer)
@router.post("/sell-to-distributor", response_model=StockOperationResponse)
def sell_to_distributor(
    blanket_id: int, 
    quantity: int, 
    distributor_name: str, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    try:
        result = process_distributor_order(db, blanket_id, quantity, distributor_name, user)
        return StockOperationResponse(
            success=True,
            message=f"Successfully sold {quantity} units to {distributor_name}",
            manufacturer_remaining_stock=result["manufacturer_remaining_stock"],
            distributor_stock=result["distributor_stock"],
            processed_quantity=result["processed_quantity"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get all distributor orders
@router.get("/distributor-orders", response_model=list[DistributorOrderOut])
def get_distributor_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_all_distributor_orders(db)