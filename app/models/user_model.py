from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="seller")
    
    # Relationships
    distributor_orders = relationship("DistributorOrder", back_populates="user")
    seller_orders = relationship("SellerOrder", foreign_keys="SellerOrder.seller_id", back_populates="seller")
    distributor_seller_orders = relationship("SellerOrder", foreign_keys="SellerOrder.distributor_id", back_populates="distributor")
    products_for_sale = relationship("ProductForSale", back_populates="seller")  