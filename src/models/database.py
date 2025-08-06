from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    """User table for storing user information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Article(Base):
    """Articles tracked by users"""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    articule = Column(String(20), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Add unique constraint for user_id + articule combination
    __table_args__ = (
        UniqueConstraint('user_id', 'articule', name='uq_user_article'),
    )

class ProductPrice(Base):
    """Product price history"""
    __tablename__ = 'product_prices'
    
    id = Column(Integer, primary_key=True)
    articule = Column(String(20), nullable=False, index=True)
    product_name = Column(Text, nullable=False)
    final_price = Column(String(50), nullable=False)
    price_float = Column(Float, nullable=True)
    is_sold_out = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)

class CacheEntry(Base):
    """Cache entries for products"""
    __tablename__ = 'cache_entries'
    
    id = Column(Integer, primary_key=True)
    articule = Column(String(20), unique=True, nullable=False, index=True)
    product_name = Column(Text, nullable=False)
    final_price = Column(String(50), nullable=False)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)

class Subscription(Base):
    """User subscriptions for periodic updates"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    interval_seconds = Column(Integer, default=300)  # 5 minutes default
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ErrorLog(Base):
    """Error logging for debugging"""
    __tablename__ = 'error_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    articule = Column(String(20), nullable=True)
    error_type = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    