from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class AvailabilityStatus(enum.Enum):
    IN_STOCK = "In stock"
    OUT_OF_STOCK = "Out of stock"

class SellerInventory(Base):
    __tablename__ = "seller_inventory"

    id = Column(Integer, primary_key=True, index=True)
    seller_name = Column(String(100), nullable=False)
    blanket_id = Column(Integer, ForeignKey("blankets.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    # Relationship to Blanket
    blanket = relationship("Blanket", back_populates=None)

    # Ensure unique combination of seller and blanket
    __table_args__ = (UniqueConstraint('seller_name', 'blanket_id', name='unique_seller_blanket'),)

class CustomerOrder(Base):
    __tablename__ = "customer_orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    seller_name = Column(String(100), nullable=False)
    blanket_id = Column(Integer, ForeignKey("blankets.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String(50), default="confirmed")  # e.g., confirmed, fulfilled, cancelled
    total_value = Column(Float, nullable=True)
    
    # Relationship to Blanket
    blanket = relationship("Blanket", back_populates=None)

class SellerOrder(Base):
    __tablename__ = "seller_orders"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    distributor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blanket_id = Column(Integer, ForeignKey("blankets.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_date = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_orders")
    distributor = relationship("User", foreign_keys=[distributor_id], back_populates="distributor_seller_orders")
    blanket = relationship("Blanket", back_populates="seller_orders")


class ProductForSale(Base):
    __tablename__ = "products_for_sale"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blanket_id = Column(Integer, ForeignKey("blankets.id"), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    availability = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.IN_STOCK, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Ensure unique combination of seller and blanket
    __table_args__ = (UniqueConstraint('seller_id', 'blanket_id', name='unique_seller_product'),)
    
    # Relationships
    seller = relationship("User", back_populates="products_for_sale")
    blanket = relationship("Blanket", back_populates="products_for_sale")