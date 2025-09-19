"""SQLModel database models."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Item(SQLModel, table=True):
    """Main item model for tracking products."""
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    domain: str = Field(index=True)
    title: Optional[str] = None
    image_url: Optional[str] = None
    site_name: Optional[str] = None
    currency: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_paused: bool = Field(default=False)
    notes: Optional[str] = None
    
    # Relationships
    prices: List["Price"] = Relationship(back_populates="item")
    targets: List["Target"] = Relationship(back_populates="item")
    flags: List["Flag"] = Relationship(back_populates="item")

class Price(SQLModel, table=True):
    """Price history for items."""
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    price_cents: int
    currency: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    source_confidence: float = Field(default=1.0)
    
    # Relationships
    item: Item = Relationship(back_populates="prices")

class Target(SQLModel, table=True):
    """Price targets for items."""
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    target_cents: Optional[int] = None
    rule_name: Optional[str] = None
    
    # Relationships
    item: Item = Relationship(back_populates="targets")

class Flag(SQLModel, table=True):
    """Special flags for items (free shipping, offers, etc.)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    free_shipping: Optional[bool] = None
    accepts_offers: Optional[bool] = None
    ending_ts: Optional[datetime] = None
    
    # Relationships
    item: Item = Relationship(back_populates="flags")
