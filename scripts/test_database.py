#!/usr/bin/env python3
"""
Simple database test without full settings
"""

import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test basic database connection"""
    try:
        # Test with SQLite first (no PostgreSQL required)
        engine = create_engine("sqlite:///test.db", echo=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Test session creation
        session = SessionLocal()
        session.close()
        logger.info("✅ Database session works")
        
        logger.info("✅ Basic database test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
