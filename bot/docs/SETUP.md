# Setup Guide

Complete guide to setting up the Self-Auditing Productivity System.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: Create Telegram Bot](#step-1-create-telegram-bot)
- [Step 2: Get OpenRouter API Key](#step-2-get-openrouter-api-key)
- [Step 3: Install the Bot](#step-3-install-the-bot)
- [Step 4: Configure Environment](#step-4-configure-environment)
- [Step 5: Optional Integrations](#step-5-optional-integrations)
- [Step 6: Start the Bot](#step-6-start-the-bot)
- [Step 7: Get Your Chat ID](#step-7-get-your-chat-id)
- [Step 8: Enable Scheduled Check-ins](#step-8-enable-scheduled-check-ins)
- [Step 9: Setup Backups](#step-9-setup-backups)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- **Python 3.11 or higher**
  ```bash
  python3 --version  # Should be 3.11+
  ```

- **Git**
  ```bash
  git --version
  ```

- **Telegram account** on your phone or desktop

### Optional

- **Docker** (for containerized deployment)
- **Google account** (for calendar integration)
- **Linux server or VPS** (for production deployment)

## Step 1: Create Telegram Bot

1. **Open Telegram** and search for [@BotFather](https://t.me/BotFather)

2. **Start a chat** with BotFather and send `/newbot`

3. **Choose a name** for your bot (e.g., "My Productivity Assistant")

4. **Choose a username** (must end in 'bot', e.g., "myproductivity_bot")

5. **Save the bot token**
   - BotFather will send you a token like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - **Keep this secret!**

6. **Configure bot settings** (recommended):
   ```
   /setdescription - Set a description
   /setabouttext - Set about text
   /setcommands - Set command list
   ```

   Command list to copy:
   ```
   start - Get started with the bot
   help - Show all commands
   add - Add a new task
   tasks - List your tasks
   schedule - Schedule a task on calendar
   suggest - Get time slot suggestions
   calendar - View upcoming events
   people - List people in your network
   person - Add or view a person
   contact - Update last contact date
   settings - View and update preferences
   ```

## Step 2: Get OpenRouter API Key

1. **Sign up** at [https://openrouter.ai](https://openrouter.ai)

2. **Add credits** to your account
   - Recommended: Start with $5-10
   - DeepSeek is very cheap (~$0.14 per million tokens)
   - Claude is more expensive but used only as fallback

3. **Create API key**
   - Go to Keys tab
   - Click "Create Key"
   - Copy and save the key

4. **Estimate costs** (typical usage):
   - 100 tasks/day with DeepSeek: ~$0.05/day
   - 10 complex queries with Claude: ~$0.10/day
   - Total: ~$5/month for moderate use

## Step 3: Install the Bot

### Option A: Local Installation

```bash
# Clone repository
git clone <repository-url>
cd bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option B: Docker Installation

```bash
# Clone repository
git clone <repository-url>
cd bot

# Build image
docker build -t productivity-bot .

# Or use docker-compose (recommended)
docker-compose build
```

## Step 4: Configure Environment

1. **Copy example environment file**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file**
   ```bash
   nano .env  # or vim, code, etc.
   ```

3. **Set required variables**
   ```bash
   # Required
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   OPENROUTER_API_KEY=sk-or-v1-...

   # Paths (adjust if needed)
   DATABASE_PATH=./data/bot.db
   VAULT_PATH=./obsidian-vault

   # LLM models (defaults are good)
   PRIMARY_MODEL=deepseek/deepseek-chat
   FALLBACK_MODEL=anthropic/claude-3.5-sonnet

   # Timezone (change to yours)
   TZ=America/New_York
   ```

## Step 5: Optional Integrations

### Google Calendar (Recommended)

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project
   - Enable Google Calendar API

2. **Create OAuth credentials**
   - Go to Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: Desktop app
   - Download credentials JSON

3. **Run authentication script**
   ```bash
   python scripts/setup_google_auth.py
   ```

   This will:
   - Open browser for Google login
   - Request calendar permissions
   - Generate refresh token
   - Display token to add to `.env`

4. **Add to `.env`**
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REFRESH_TOKEN=your_refresh_token
   ```

### Push Notifications via ntfy.sh

1. **Choose a unique topic**
   ```bash
   # Use a random string to keep it private
   # Example: mybot_8h32kf9s2j
   ```

2. **Add to `.env`**
   ```bash
   NTFY_URL=https://ntfy.sh
   NTFY_TOPIC=your_unique_topic
   ```

3. **Subscribe on your phone**
   - Install ntfy app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy), [iOS](https://apps.apple.com/app/ntfy/id1625396347))
   - Subscribe to your topic

### Git Sync for Obsidian Vault

1. **Create bare git repository** on your server
   ```bash
   # On your server
   mkdir -p /var/git/obsidian-vault.git
   cd /var/git/obsidian-vault.git
   git init --bare
   ```

2. **Run setup script**
   ```bash
   cd scripts
   ./setup_git_sync.sh user@server:/var/git/obsidian-vault.git
   ```

3. **Add to `.env`**
   ```bash
   GIT_SYNC_ENABLED=true
   GIT_REMOTE_URL=user@server:/var/git/obsidian-vault.git
   ```

## Step 6: Start the Bot

### Option A: Local Run

```bash
# Activate virtual environment
source venv/bin/activate

# Run bot
python -m src.main
```

You should see:
```
INFO - Starting Productivity Bot
INFO - Bot initialized
INFO - Bot started
INFO - Bot is ready! Press Ctrl+C to stop.
```

### Option B: Docker Run

```bash
# Using docker-compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Or using docker directly
docker run -d \
  --name productivity-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/obsidian-vault:/app/obsidian-vault \
  productivity-bot
```

### Option C: Background Process (Linux)

```bash
# Using systemd
sudo cp scripts/productivity-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable productivity-bot
sudo systemctl start productivity-bot

# Check status
sudo systemctl status productivity-bot
```

## Step 7: Get Your Chat ID

1. **Send `/start` to your bot** in Telegram

2. **Get updates** from Telegram API:
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```

   Look for:
   ```json
   "chat": {
     "id": 123456789,
     "first_name": "Your Name",
     "type": "private"
   }
   ```

3. **Save your chat ID** - You'll need this for scheduled check-ins

## Step 8: Enable Scheduled Check-ins

1. **Add chat ID to `.env`**
   ```bash
   TELEGRAM_ADMIN_CHAT_ID=123456789
   ```

2. **Restart the bot**
   ```bash
   # Docker
   docker-compose restart

   # Local
   # Press Ctrl+C, then run again
   python -m src.main
   ```

3. **Verify scheduling** in logs:
   ```
   INFO - Scheduled morning check-in at 04:30:00
   INFO - Scheduled periodic check-ins (9 AM - 5 PM)
   INFO - Scheduled evening review at 20:00:00
   ```

4. **Customize check-in times** (optional):
   - Use `/settings` command in bot
   - Or edit `.env` and restart

## Step 9: Setup Backups

### Automated Backups (Recommended)

```bash
cd scripts
./setup_backup_cron.sh  # Daily at 2 AM
```

### Manual Backup

```bash
cd scripts
./backup.sh
```

### Test Restore

```bash
# List backups
ls -lh ./backups/

# Test restore
./restore.sh ./backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

See [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md) for detailed backup documentation.

## Verify Installation

1. **Send `/start` to bot** → Should receive welcome message
2. **Send `/add Test task`** → Should acknowledge task creation
3. **Send `/tasks`** → Should list tasks
4. **Send `/settings`** → Should show current settings
5. **Wait for check-in** (or test manually) → Should receive prompts

## Next Steps

1. **Read the User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
2. **Customize settings**: Use `/settings` in bot
3. **Set up calendar** if you added credentials
4. **Start using**: Add your first real task!

## Troubleshooting

### Bot doesn't respond

**Check if bot is running**:
```bash
# Docker
docker ps | grep productivity

# Local
ps aux | grep python
```

**Check logs**:
```bash
# Docker
docker logs productivity-bot

# Local
tail -f data/bot.log
```

**Common issues**:
- Wrong bot token → Double-check `.env`
- Bot not started → Run start command
- Firewall blocking → Check network settings

### "Module not found" errors

**Reinstall dependencies**:
```bash
pip install -r requirements.txt --upgrade
```

### Database errors

**Reinitialize database**:
```bash
rm data/bot.db  # WARNING: Deletes all data!
python -m src.database
```

### LLM requests failing

**Check OpenRouter**:
- Verify API key is correct
- Check account has credits
- Review rate limits

**Test manually**:
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Calendar integration not working

**Verify credentials**:
```bash
# Test OAuth token
python scripts/test_google_auth.py
```

**Refresh token**:
```bash
python scripts/setup_google_auth.py
```

### Permission denied errors

**Fix file permissions**:
```bash
chmod +x scripts/*.sh
chmod 644 .env
chmod 755 data/ obsidian-vault/
```

### Port already in use

This bot doesn't use ports, but if running other services:
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>
```

## Getting Help

1. **Check logs first** - Most issues are logged
2. **Review documentation** - README, USER_GUIDE, BACKUP_RECOVERY
3. **Search issues** - GitHub Issues
4. **Ask for help** - GitHub Discussions
5. **Report bugs** - GitHub Issues with logs

## Production Deployment

For production deployment to a VPS or cloud:

1. **Use Docker** - Easier to manage and update
2. **Setup Coolify** - See [.coolify/README.md](../.coolify/README.md)
3. **Enable backups** - Critical for production
4. **Use monitoring** - Set up alerts for failures
5. **Secure secrets** - Use environment variable management
6. **Setup HTTPS** - If exposing any web interface
7. **Regular updates** - Keep dependencies updated

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production setup.
