from pydantic import BaseModel, EmailStr

# Schema for registering a new user
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# Schema for returning user details
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

# Schema for returning JWT token
class Token(BaseModel):
    access_token: str
    token_type: str