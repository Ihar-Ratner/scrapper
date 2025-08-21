
## �� Prerequisites

### **System Requirements**
- **OS**: Ubuntu 20.04+ / Debian 11+ / macOS / Windows 10+
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 5GB free space
- **Network**: Stable internet connection

### **Software Requirements**
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Git**: For cloning the repository

### **External Services**
- **Telegram Bot Token**: Get from [@BotFather](https://t.me/botfather)
- **PostgreSQL**: Included via Docker (no external setup needed)

## 🚀 Quick Start

### **1. Clone Repository**
```bash
git clone <your-repo-url>
cd scrapper
```

### **2. Create Environment File**
```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Required Environment Variables:**
```env
# Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here
DB_PASSWORD=your_secure_database_password

# Optional Settings
LOG_LEVEL=INFO
DEBUG=false
```

### **3. Start Services**
```bash
# Start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### **4. Verify Installation**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs wb_bot

# Test database connection
docker exec wb_db psql -U wb_bot -d wb -c "SELECT 1;"
```

## 🤖 Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot and show welcome message | `/start` |
| `/help` | Display available commands | `/help` |
| `/add <article>` | Add product to tracking list | `/add 12345678` |
| `/show` | Display tracked products and prices | `/show` |
| `/check` | Manually check all tracked prices | `/check` |
| `/remove <article>` | Remove product from tracking | `/remove 12345678` |
| `/subscribe <minutes>` | Enable automatic monitoring | `/subscribe 30` |
| `/unsubscribe` | Disable automatic monitoring | `/unsubscribe` |
| `/setinterval <minutes>` | Change monitoring interval | `/setinterval 60` |
| `/cache` | Manage cache settings | `/cache clear` |

## ⚙️ Configuration

### **Bot Settings**
```python
# src/config/settings.py
class Settings:
    telegram_token: str
    max_browsers: int = 3
    headless: bool = True
    scrape_timeout: int = 45
    retry_attempts: int = 3
    rate_limit_delay: float = 2.0
    default_interval: int = 300  # 5 minutes
```

### **Cache Configuration**
```python
class CacheConfig:
    memory_cache_size: int = 1000
    cache_ttl_minutes: int = 30
    disk_cache_enabled: bool = True
    cache_dir: Path = Path("cache")
```

### **Database Configuration**
```python
class DatabaseConfig:
    host: str = "db"
    port: int = 5432
    database: str = "wb"
    username: str = "wb_bot"
    password: str = "from_env"
```

## ��️ Database Schema

### **Core Tables**
- **`users`**: Bot user information and preferences
- **`articles`**: Products being tracked by users
- **`product_prices`**: Price history and monitoring data
- **`subscriptions`**: User subscription settings
- **`error_logs`**: Error tracking and debugging

### **Data Migration**
```bash
# If you have existing data, import it:
docker cp your_dump.sql wb_db:/tmp/
docker exec wb_db psql -U wb_bot -d wb -f /tmp/your_dump.sql
```

## 🔧 Development Setup

### **Local Development**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Set up local database
# (Use docker-compose for database, run bot locally)

# Run bot locally
python main.py
```

### **Testing**
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_scraper.py
```

## 📊 Monitoring & Logs

### **View Logs**
```bash
# Bot logs
docker-compose logs wb_bot

# Database logs
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f wb_bot
```

### **Health Checks**
```bash
# Check bot status
docker exec wb_bot ps aux | grep python

# Check database health
docker exec wb_db pg_isready -U wb_bot -d wb

# Check cache statistics
# Use /cache command in Telegram
```

## 🚨 Troubleshooting

### **Common Issues**

#### **Bot Won't Start**
```bash
# Check environment variables
docker-compose logs wb_bot | grep "Error"

# Verify Telegram token
echo $TELEGRAM_TOKEN

# Check database connection
docker exec wb_db psql -U wb_bot -d wb -c "SELECT 1;"
```

#### **Database Connection Issues**
```bash
# Restart database service
docker-compose restart db

# Check database logs
docker-compose logs db

# Verify volume permissions
docker volume inspect scrapper_pg_data
```

#### **Scraping Failures**
```bash
# Check browser pool status
docker exec wb_bot ps aux | grep chrome

# Clear cache
docker-compose exec wb_bot python -c "from src.services.cache_manager import CacheManager; CacheManager().clear_all()"

# Check network connectivity
docker exec wb_bot ping wildberries.by
```

### **Performance Issues**
```bash
# Monitor resource usage
docker stats

# Check cache hit rates
# Use /cache command in bot

# Adjust browser pool size in settings
# Increase max_browsers if needed
```

## 🔒 Security Considerations

- **Environment Variables**: Never commit `.env` files to version control
- **Database Passwords**: Use strong, unique passwords
- **Telegram Token**: Keep your bot token secure
- **Rate Limiting**: Built-in rate limiting prevents abuse
- **Error Logging**: Sensitive data is not logged

### **Backup Strategy**
```bash
# Database backup
docker exec wb_db pg_dump -U wb_bot -d wb > backup_$(date +%Y%m%d).sql

# Volume backup
docker run --rm -v scrapper_pg_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/volume_backup.tar.gz -C /data .
```
