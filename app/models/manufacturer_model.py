from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Blanket(Base):
    __tablename__ = "blankets"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    material = Column(String(100), nullable=False)
    stock = Column(Integer, default=0)
    production_capacity = Column(Integer, default=0)
    image_url = Column(String(255), nullable=True)  # Added image URL field
    
    # Relationships
    distributor_orders = relationship("DistributorOrder", back_populates="blanket")
    seller_orders = relationship("SellerOrder", back_populates="blanket")
    products_for_sale = relationship("ProductForSale", back_populates="blanket")