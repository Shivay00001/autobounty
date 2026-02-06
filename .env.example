# backend/.env.example
# Copy this file to .env and fill in your values

# ==================================================
# DATABASE CONFIGURATION
# ==================================================
# For SQLite (default, good for single-user):
DATABASE_URL=sqlite:///./autobounty.db

# For PostgreSQL (recommended for production):
# DATABASE_URL=postgresql://username:password@localhost:5432/autobounty

# For MySQL:
# DATABASE_URL=mysql://username:password@localhost:3306/autobounty

# ==================================================
# APPLICATION SETTINGS
# ==================================================
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# ==================================================
# HACKERONE API CONFIGURATION
# ==================================================
# Get your API token from: https://hackerone.com/settings/api_token/edit
HACKERONE_API_TOKEN=
HACKERONE_TEAM_HANDLE=
HACKERONE_API_URL=https://api.hackerone.com/v1

# ==================================================
# INTIGRITI API CONFIGURATION
# ==================================================
INTIGRITI_API_TOKEN=
INTIGRITI_API_URL=https://api.intigriti.com

# ==================================================
# TELEGRAM NOTIFICATIONS
# ==================================================
# Create a bot with @BotFather and get the token
# Get your chat ID from https://api.telegram.org/bot<TOKEN>/getUpdates
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# ==================================================
# SLACK NOTIFICATIONS
# ==================================================
# Create an incoming webhook at https://api.slack.com/apps
SLACK_WEBHOOK_URL=

# ==================================================
# CHROME/SELENIUM CONFIGURATION
# ==================================================
# Leave empty to use system Chrome/Chromium
# Or specify path: /usr/bin/chromedriver
CHROME_DRIVER_PATH=

# Run browser in headless mode (recommended for servers)
HEADLESS_BROWSER=True

# ==================================================
# EVIDENCE STORAGE
# ==================================================
# Path where screenshots and evidence will be stored
EVIDENCE_BASE_PATH=./evidence

# ==================================================
# SCHEDULER CONFIGURATION
# ==================================================
# Enable/disable automatic scheduled scans
SCHEDULER_ENABLED=False

# How often to run scheduled scans (in hours)
SCHEDULER_INTERVAL_HOURS=24

# ==================================================
# RECON SETTINGS
# ==================================================
# Maximum pages to crawl per target
MAX_CRAWL_PAGES=50

# Rate limit between requests (in seconds)
CRAWL_RATE_LIMIT_SECONDS=1.0

# ==================================================
# SECURITY
# ==================================================
# IMPORTANT: Change this to a strong random key in production!
# Generate with: openssl rand -hex 32
SECRET_KEY=change-this-to-a-strong-random-key-in-production-use-openssl-rand-hex-32


# ==================================================
# ADVANCED SETTINGS (Optional)
# ==================================================

# API rate limiting
# API_RATE_LIMIT=100

# Maximum file upload size (in MB)
# MAX_UPLOAD_SIZE=10

# Session timeout (in minutes)
# SESSION_TIMEOUT=30

# Log level: DEBUG, INFO, WARNING, ERROR
# LOG_LEVEL=INFO

# ==================================================
# NOTES
# ==================================================
# - Never commit this file to version control
# - Add .env to your .gitignore
# - Use environment-specific files (.env.dev, .env.prod)
# - Restart the application after changing these values