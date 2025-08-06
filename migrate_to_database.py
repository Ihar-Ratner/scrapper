#!/usr/bin/env python3
"""
Migration script to move from file storage to database
"""

import asyncio
import json
import logging
from pathlib import Path
from src.storage.database_manager import DatabaseManager
from src.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_data():
    """Migrate data from files to database"""
    db_manager = DatabaseManager()
    
    # Load existing data from files
    data_dir = Path("data")
    if not data_dir.exists():
        logger.info("No data directory found, skipping migration")
        return
    
    # Migrate users and articles
    for user_file in data_dir.glob("*.txt"):
        if user_file.name == "subscribers.txt":
            continue
            
        user_id = int(user_file.stem)
        logger.info(f"Migrating user {user_id}")
        
        # Create user
        user = db_manager.get_or_create_user(user_id)
        
        # Load articles
        with open(user_file, 'r', encoding='utf-8') as f:
            articles = [line.strip() for line in f if line.strip()]
        
        if articles:
            db_manager.add_articles(user.id, articles)
            logger.info(f"Migrated {len(articles)} articles for user {user_id}")
    
    # Migrate results
    for results_file in data_dir.glob("*.json"):
        user_id = int(results_file.stem)
        logger.info(f"Migrating results for user {user_id}")
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            for result in results:
                db_manager.save_product_price(
                    articule=result["articule"],
                    product_name=result["product_name"],
                    final_price=result["final_price"],
                    user_id=user_id
                )
            
            logger.info(f"Migrated {len(results)} price records for user {user_id}")
        except Exception as e:
            logger.error(f"Error migrating results for user {user_id}: {e}")
    
    # Migrate subscriptions
    subscribers_file = data_dir / "subscribers.txt"
    if subscribers_file.exists():
        with open(subscribers_file, 'r', encoding='utf-8') as f:
            subscribers = [int(line.strip()) for line in f if line.strip().isdigit()]
        
        for user_id in subscribers:
            try:
                user = db_manager.get_or_create_user(user_id)
                db_manager.save_subscription(user.id)
                logger.info(f"Migrated subscription for user {user_id}")
            except Exception as e:
                logger.error(f"Error migrating subscription for user {user_id}: {e}")
    
    # Migrate intervals
    intervals_file = Path("intervals.json")
    if intervals_file.exists():
        try:
            with open(intervals_file, 'r', encoding='utf-8') as f:
                intervals = json.load(f)
            
            for user_id_str, interval_seconds in intervals.items():
                user_id = int(user_id_str)
                try:
                    user = db_manager.get_or_create_user(user_id)
                    db_manager.save_subscription(user.id, interval_seconds)
                    logger.info(f"Migrated interval for user {user_id}: {interval_seconds}s")
                except Exception as e:
                    logger.error(f"Error migrating interval for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error migrating intervals: {e}")
    
    logger.info("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_data())
