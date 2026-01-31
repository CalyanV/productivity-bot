# Coolify Deployment Guide

This directory contains configuration for deploying the Productivity Bot to [Coolify](https://coolify.io).

## Prerequisites

1. **Coolify Instance**: Have a Coolify instance running (self-hosted or managed)
2. **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/BotFather)
3. **OpenRouter API Key**: Sign up at [OpenRouter](https://openrouter.ai) and get an API key

## Quick Start

### 1. Create Application in Coolify

1. Log into your Coolify dashboard
2. Click **"New Resource"** → **"Application"**
3. Choose **"Docker Compose"** or **"Dockerfile"**
4. Connect your Git repository

### 2. Configure Environment Variables

Required variables:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_token_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

Optional variables (recommended):
```bash
# Admin chat ID for scheduled check-ins
TELEGRAM_ADMIN_CHAT_ID=your_telegram_chat_id

# Google Calendar integration
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token

# Notifications via ntfy.sh
NTFY_TOPIC=your_unique_topic

# Timezone
TZ=America/New_York
```

### 3. Deploy

1. Click **"Deploy"**
2. Wait for build to complete
3. Check logs to verify bot started successfully

### 4. Verify Deployment

Send `/start` to your Telegram bot. You should receive a welcome message.

## Configuration Details

### Resource Limits

- **Memory**: 512MB limit, 256MB reservation
- **CPU**: 1.0 limit, 0.25 reservation

Adjust in `deploy.yml` if needed.

### Health Checks

The bot includes a basic health check that runs every 30 seconds. Coolify will restart the container if health checks fail.

### Persistent Storage

Two volumes are mounted:
- `/app/data` - SQLite database and logs
- `/app/obsidian-vault` - Markdown files

**Important**: Ensure these volumes are backed up regularly!

### Backups

Automatic backups are configured in `deploy.yml`:
- **Schedule**: Daily at 2 AM
- **Retention**: 30 days
- **Paths**: Database and vault

## Getting Your Telegram Chat ID

To enable scheduled check-ins:

1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}`
4. Set `TELEGRAM_ADMIN_CHAT_ID=123456789` in Coolify

## Optional: Google Calendar Integration

See `../scripts/setup_google_auth.py` to get OAuth credentials.

1. Run the setup script locally
2. Copy the refresh token to Coolify environment variables

## Optional: Git Sync

To sync your Obsidian vault to a Git repository:

1. Create a bare git repository on your server
2. Set `GIT_SYNC_ENABLED=true`
3. Set `GIT_REMOTE_URL=user@server:/path/to/repo.git`
4. Mount SSH keys as volume (see `docker-compose.yml`)

## Monitoring

### View Logs

In Coolify dashboard:
1. Navigate to your application
2. Click **"Logs"**
3. View real-time logs

Or via CLI:
```bash
docker logs -f productivity-bot
```

### Check Health

```bash
docker inspect productivity-bot | grep -A 5 Health
```

## Troubleshooting

### Bot not responding

1. Check logs for errors
2. Verify `TELEGRAM_BOT_TOKEN` is correct
3. Ensure bot is not rate-limited

### LLM requests failing

1. Verify `OPENROUTER_API_KEY` is valid
2. Check OpenRouter account has credits
3. Review logs for specific error messages

### Database locked errors

1. Ensure only one instance is running
2. Check file permissions on `/app/data`
3. Verify volume is properly mounted

### Calendar integration not working

1. Verify all Google credentials are set
2. Run `setup_google_auth.py` to refresh token
3. Check Google Calendar API is enabled

## Updating

Coolify can auto-deploy on git push:

1. Enable **"Auto Deploy"** in Coolify
2. Push changes to your repository
3. Coolify will rebuild and redeploy automatically

## Scaling

This bot is designed for single-user or small team use. For multiple users:

1. Each user should have their own bot instance
2. Use separate databases per instance
3. Consider resource limits per instance

## Support

- **Bot Issues**: Check logs and GitHub issues
- **Coolify Issues**: See [Coolify Docs](https://coolify.io/docs)
- **Telegram Bot API**: See [Telegram Docs](https://core.telegram.org/bots/api)
