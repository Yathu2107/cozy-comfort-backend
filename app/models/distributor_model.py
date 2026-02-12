from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DistributorOrder(Base):
    __tablename__ = "distributor_orders"

    id = Column(Integer, primary_key=True, index=True)
    distributor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blanket_id = Column(Integer, ForeignKey("blankets.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_date = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    blanket = relationship("Blanket", back_populates="distributor_orders")
    user = relationship("User", back_populates="distributor_orders")

class DistributorStock(Base):
    __tablename__ = "distributor_stock"

    id = Column(Integer, primary_key=True, index=True)
    distributor_name = Column(String(100), nullable=False)
    blanket_id = Column(Integer, ForeignKey("blankets.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Relationship to Blanket
    blanket = relationship("Blanket", back_populates=None)

    # Ensure unique combination of distributor and blanket
    __table_args__ = (UniqueConstraint('distributor_name', 'blanket_id', name='unique_distributor_blanket'),)