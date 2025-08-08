import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from ..models.database import Base, User, Article, ProductPrice, CacheEntry, Subscription, ErrorLog
from ..config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for PostgreSQL operations"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, echo=settings.debug)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Close database session"""
        session.close()
    
    # User operations
    def get_or_create_user(self, telegram_id: int, username: str = None) -> User:
        """Get or create user"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(telegram_id=telegram_id, username=username)
                session.add(user)
                session.commit()
                session.refresh(user)
            return user
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error getting/creating user: {e}")
            raise
        finally:
            self.close_session(session)
    
    # Article operations
    def add_articles(self, user_id: int, articules: List[str]) -> List[str]:
        """Add articles for user"""
        session = self.get_session()
        added_articles = []
        try:
            for articule in articules:
                # Check if already exists
                existing = session.query(Article).filter(
                    Article.user_id == user_id,
                    Article.articule == articule
                ).first()
                
                if not existing:
                    article = Article(user_id=user_id, articule=articule)
                    session.add(article)
                    added_articles.append(articule)
            
            session.commit()
            return added_articles
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding articles: {e}")
            raise
        finally:
            self.close_session(session)
    
    def remove_articles(self, user_id: int, articules: List[str]) -> List[str]:
        """Remove articles for user"""
        session = self.get_session()
        removed_articles = []
        try:
            for articule in articules:
                article = session.query(Article).filter(
                    Article.user_id == user_id,
                    Article.articule == articule
                ).first()
                
                if article:
                    session.delete(article)
                    removed_articles.append(articule)
            
            session.commit()
            return removed_articles
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error removing articles: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_user_articles(self, user_id: int) -> List[str]:
        """Get all articles for user"""
        session = self.get_session()
        try:
            articles = session.query(Article).filter(Article.user_id == user_id).all()
            return [article.articule for article in articles]
        except SQLAlchemyError as e:
            logger.error(f"Error getting user articles: {e}")
            raise
        finally:
            self.close_session(session)
    
    # Product price operations
    def save_product_price(self, articule: str, product_name: str, final_price: str, 
                          user_id: int, is_sold_out: bool = False) -> ProductPrice:
        """Save product price"""
        session = self.get_session()
        try:
            # Parse price to float
            price_float = self._parse_price_to_float(final_price)
            
            product_price = ProductPrice(
                articule=articule,
                product_name=product_name,
                final_price=final_price,
                price_float=price_float,
                is_sold_out=is_sold_out,
                user_id=user_id
            )
            
            session.add(product_price)
            session.commit()
            session.refresh(product_price)
            return product_price
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error saving product price: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_latest_prices(self, user_id: int) -> Dict[str, float]:
        """Get latest prices for user's articles"""
        session = self.get_session()
        try:
            # Get latest price for each article
            latest_prices = session.query(ProductPrice).filter(
                ProductPrice.user_id == user_id
            ).order_by(ProductPrice.articule, ProductPrice.scraped_at.desc()).all()
            
            # Group by articule and take latest
            price_map = {}
            for price in latest_prices:
                if price.articule not in price_map:
                    price_map[price.articule] = price.price_float or 0.0
            
            return price_map
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest prices: {e}")
            raise
        finally:
            self.close_session(session)
    
    # Cache operations
    def cache_product(self, articule: str, product_name: str, final_price: str, 
                     ttl_minutes: int = 15) -> CacheEntry:
        """Cache product data"""
        session = self.get_session()
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            
            # Remove existing cache entry
            session.query(CacheEntry).filter(CacheEntry.articule == articule).delete()
            
            cache_entry = CacheEntry(
                articule=articule,
                product_name=product_name,
                final_price=final_price,
                expires_at=expires_at
            )
            
            session.add(cache_entry)
            session.commit()
            session.refresh(cache_entry)
            return cache_entry
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error caching product: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_cached_product(self, articule: str) -> Optional[CacheEntry]:
        """Get cached product if not expired"""
        session = self.get_session()
        try:
            cache_entry = session.query(CacheEntry).filter(
                CacheEntry.articule == articule,
                CacheEntry.expires_at > datetime.utcnow()
            ).first()
            return cache_entry
        except SQLAlchemyError as e:
            logger.error(f"Error getting cached product: {e}")
            raise
        finally:
            self.close_session(session)
    
    def clear_expired_cache(self) -> int:
        """Clear expired cache entries"""
        session = self.get_session()
        try:
            deleted_count = session.query(CacheEntry).filter(
                CacheEntry.expires_at <= datetime.utcnow()
            ).delete()
            session.commit()
            return deleted_count
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error clearing expired cache: {e}")
            raise
        finally:
            self.close_session(session)
    
    # Subscription operations
    def save_subscription(self, user_id: int, interval_seconds: int = 300) -> Subscription:
        """Save user subscription"""
        session = self.get_session()
        try:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()
            
            if subscription:
                subscription.interval_seconds = interval_seconds
                subscription.is_active = True
            else:
                subscription = Subscription(
                    user_id=user_id,
                    interval_seconds=interval_seconds
                )
                session.add(subscription)
            
            session.commit()
            session.refresh(subscription)
            return subscription
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error saving subscription: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_active_subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions"""
        session = self.get_session()
        try:
            return session.query(Subscription).filter(Subscription.is_active == True).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active subscriptions: {e}")
            raise
        finally:
            self.close_session(session)
    
    def remove_subscription(self, user_id: int) -> bool:
        """Remove user subscription"""
        session = self.get_session()
        try:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()
            
            if subscription:
                subscription.is_active = False
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error removing subscription: {e}")
            raise
        finally:
            self.close_session(session)
    
    # Error logging
    def log_error(self, error_type: str, error_message: str, user_id: int = None, 
                  articule: str = None, context: str = None) -> ErrorLog:
        """Log error to database"""
        session = self.get_session()
        try:
            error_log = ErrorLog(
                error_type=error_type,
                error_message=error_message,
                user_id=user_id,
                articule=articule,
                context=context
            )
            
            session.add(error_log)
            session.commit()
            session.refresh(error_log)
            return error_log
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging error: {e}")
            raise
        finally:
            self.close_session(session)
    
    # Utility methods
    def _parse_price_to_float(self, price_str: str) -> float:
        """Parse price string to float"""
        try:
            import re
            m = re.search(r"[\d\s]+,\d{2}", price_str)
            if m:
                return float(m.group().replace(" ", "").replace(",", "."))
            else:
                numbers = re.findall(r'[\d\s,]+', price_str)
                if numbers:
                    clean_number = numbers[0].replace(" ", "").replace(",", ".")
                    return float(clean_number)
                return 0.0
        except Exception:
            return 0.0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        try:
            stats = {
                'users_count': session.query(User).count(),
                'articles_count': session.query(Article).count(),
                'prices_count': session.query(ProductPrice).count(),
                'cache_entries_count': session.query(CacheEntry).count(),
                'active_subscriptions_count': session.query(Subscription).filter(Subscription.is_active == True).count(),
                'error_logs_count': session.query(ErrorLog).count()
            }
            return stats
        except SQLAlchemyError as e:
            logger.error(f"Error getting database stats: {e}")
            raise
        finally:
            self.close_session(session)


    def get_latest_prices_with_names(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Get latest prices with product names for user's articles"""
        session = self.get_session()
        try:
            # Get latest price for each article with product name
            latest_prices = session.query(ProductPrice).filter(
                ProductPrice.user_id == user_id
            ).order_by(ProductPrice.articule, ProductPrice.scraped_at.desc()).all()
            
            # Group by articule and take latest
            price_map = {}
            for price in latest_prices:
                if price.articule not in price_map:
                    price_map[price.articule] = {
                        "price": price.price_float or 0.0,
                        "price_string": price.final_price,  # Original scraped price string
                        "product_name": price.product_name,
                        "scraped_at": price.scraped_at.isoformat()
                    }
            
            return price_map
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest prices with names: {e}")
            raise
        finally:
            self.close_session(session)

    def get_user_last_interval(self, user_id: int) -> Optional[int]:
        """Get user's last interval (even if subscription is inactive)"""
        session = self.get_session()
        try:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()
            
            if subscription and subscription.interval_seconds != settings.bot.default_interval:
                return subscription.interval_seconds
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error getting user last interval: {e}")
            return None
        finally:
            self.close_session(session)
