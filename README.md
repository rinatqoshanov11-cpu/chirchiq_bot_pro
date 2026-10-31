# Chirchiq Kvartira Bot - Professional Python Edition

Professional Telegram bot for apartment rentals and sales in Chirchiq city, Uzbekistan.

## 🌟 Features

### For Users:
- ✅ **Complete Registration System** - Name, phone number, address with validation
- 🏠 **Search Apartments** - Filter by type (rent/sale)
- ➕ **Post Listings** - Add apartments with multiple photos (up to 10)
- 📋 **My Listings** - Manage your own apartment listings
- 📱 **Contact Information** - Phone numbers and direct contact
- ⚙️ **User Settings** - View and manage profile

### For Admins:
- 🔐 **Admin Panel** - Comprehensive admin dashboard
- ✅ **Approve/Reject Listings** - Moderate apartment submissions
- 📊 **Statistics** - Real-time analytics and insights
- 👥 **User Management** - View, block/unblock users
- 📢 **Broadcast Messages** - Send announcements to all users
- 🗑️ **Manage Listings** - Archive or delete apartments

### Technical Features:
- 🤖 **Web Scraper** - Automatic import from OLX.uz
- 🔄 **Async/Await** - High-performance asynchronous architecture
- 🗃️ **PostgreSQL** - Professional database with SQLAlchemy ORM
- 📝 **Logging** - Comprehensive logging system
- ⏰ **Scheduled Tasks** - APScheduler for automated scraping
- 🎨 **FSM** - Finite State Machine for conversation flows
- 🔒 **Type Safety** - Pydantic settings validation
- 📦 **Modular Design** - Clean, maintainable code structure

## 🛠️ Technology Stack

- **Python 3.11+**
- **aiogram 3.13** - Modern Telegram Bot framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations
- **APScheduler** - Task scheduling
- **BeautifulSoup4** - Web scraping
- **Pydantic** - Settings validation
- **structlog** - Structured logging

## 📦 Installation

### Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python --version
   ```

2. **PostgreSQL 14 or higher**
   ```bash
   psql --version
   ```

3. **Git** (optional)

### Step 1: Clone or Download

```bash
cd chirchiq_bot_pro
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup PostgreSQL Database

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE chirchiq_bot;

-- Create user (optional)
CREATE USER chirchiq_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chirchiq_bot TO chirchiq_user;
```

### Step 5: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your settings
```

**.env Configuration:**
```env
# Telegram Bot Token from @BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Admin Telegram IDs (comma-separated)
ADMIN_IDS=123456789,987654321

# PostgreSQL Connection
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/chirchiq_bot

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
SCRAPER_ENABLED=True
SCRAPER_INTERVAL=3600
```

### Step 6: Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### Step 7: Run the Bot

```bash
python main.py
```

## 🚀 Getting Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Choose a name: `Chirchiq Kvartira Bot`
4. Choose username: `chirchiq_kvartira_bot`
5. Copy the token provided
6. Paste it in your `.env` file

## 📱 Getting Your Telegram ID

1. Open [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send `/start`
3. Bot will reply with your ID
4. Add it to `ADMIN_IDS` in `.env`

## 🗂️ Project Structure

```
chirchiq_bot_pro/
├── app/
│   ├── handlers/           # Message and callback handlers
│   │   ├── registration.py # User registration flow
│   │   ├── apartments.py   # Apartment CRUD operations
│   │   ├── admin.py        # Admin panel handlers
│   │   └── common.py       # Common handlers (menu, search)
│   ├── models/             # Database models
│   │   ├── user.py         # User model
│   │   ├── apartment.py    # Apartment model
│   │   └── base.py         # Base database setup
│   ├── services/           # Business logic
│   │   ├── user_service.py
│   │   └── apartment_service.py
│   ├── keyboards/          # Bot keyboards
│   ├── middlewares/        # Custom middlewares
│   ├── scrapers/           # Web scrapers
│   │   └── olx_scraper.py  # OLX scraper
│   ├── utils/              # Utility functions
│   └── states.py           # FSM states
├── config/                 # Configuration
│   └── settings.py         # Pydantic settings
├── alembic/                # Database migrations
├── logs/                   # Log files
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## 🎯 Usage

### For Users:

1. **Start Bot**: `/start`
2. **Register**: Enter name, phone, address
3. **Search**: Use "🏠 Kvartira qidirish" button
4. **Add Listing**: Use "➕ E'lon qo'shish" button
5. **My Listings**: View your apartments

### For Admins:

1. **Admin Panel**: `/admin`
2. **Approve Listings**: Review pending apartments
3. **View Stats**: Check system statistics
4. **Manage Users**: Block/unblock users
5. **Broadcast**: Send messages to all users

## 📊 Database Schema

### Users Table
- Telegram ID, username
- Full name, phone, address
- Admin status, registration status
- Activity timestamps

### Apartments Table
- Type (rent/sale)
- Rooms, area, floor info
- Address, price
- Photos (up to 10)
- Status (pending/approved/rejected)
- View count, contact count
- Source tracking (manual/scraper)

## 🔧 Maintenance

### View Logs
```bash
tail -f logs/bot.log
```

### Database Backup
```bash
pg_dump chirchiq_bot > backup.sql
```

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Create New Migration
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## 🐛 Troubleshooting

### Bot doesn't start
- Check BOT_TOKEN in .env
- Verify Python version (3.11+)
- Check all dependencies installed

### Database connection error
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database exists

### Scraper not working
- Check SCRAPER_ENABLED=True
- Verify internet connection
- Check logs for errors

## 📈 Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/chirchiq-bot.service`:

```ini
[Unit]
Description=Chirchiq Kvartira Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/chirchiq_bot_pro
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable chirchiq-bot
sudo systemctl start chirchiq-bot
sudo systemctl status chirchiq-bot
```

### Using Docker (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## 🔐 Security

- Never commit `.env` file
- Keep BOT_TOKEN secret
- Use strong database passwords
- Regularly update dependencies
- Enable PostgreSQL authentication
- Use HTTPS for webhooks (if applicable)

## 📝 License

MIT License - Feel free to use and modify

## 🤝 Support

For issues or questions:
- Check logs in `logs/bot.log`
- Review this README
- Check Telegram Bot API docs

## 🎓 Advanced Features

### Custom Scraper
Add new scrapers in `app/scrapers/`:
```python
from app.scrapers.olx_scraper import ApartmentScraper

class YourScraper(ApartmentScraper):
    async def scrape(self):
        # Your implementation
        pass
```

### Webhook Mode
Set in `.env`:
```env
USE_WEBHOOK=True
WEBHOOK_URL=https://yourdomain.com
```

## 📞 Commands

- `/start` - Start bot and register
- `/admin` - Open admin panel (admin only)
- `/cancel` - Cancel current operation

---

**Built with ❤️ for Chirchiq community**

Version: 1.0.0  
Last Updated: 2026-10-24
