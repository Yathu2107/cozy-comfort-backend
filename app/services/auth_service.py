from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.models.user_model import User
from app.schemas.auth_schema import UserCreate
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt_handler import create_access_token, decode_access_token
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Register a new user
def register_user(db: Session, data: UserCreate):
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        return None

    hashed_pw = hash_password(data.password)
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hashed_pw,
        role="seller"  # default role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Authenticate user and return JWT token
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None

    token_data = {
        "sub": user.username,
        "role": user.role
    }
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user from token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user