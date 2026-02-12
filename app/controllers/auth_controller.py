from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.schemas.auth_schema import UserCreate, UserOut, Token
from app.services.auth_service import register_user, authenticate_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Register a new user
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, data)
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    return user

# Login and receive JWT token
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    token = authenticate_user(db, form_data.username, form_data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return token

# Get current authenticated user
@router.get("/me", response_model=UserOut)
def get_me(user: UserOut = Depends(get_current_user)):
    return user