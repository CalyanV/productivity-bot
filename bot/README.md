# Self-Auditing Productivity System

A conversational Telegram bot that helps you capture tasks, manage your calendar, track relationships, and stay accountable through daily check-ins.

## Features

### 🎯 Task Management
- **Natural language input**: Just tell the bot what you need to do
- **Smart parsing**: Extracts due dates, priorities, tags, and people from your messages
- **Time estimation**: AI-powered time estimates for better planning
- **Dual storage**: SQLite for fast queries + Obsidian markdown for human access

### 📅 Calendar Integration
- **Google Calendar sync**: Automatically time-block tasks on your calendar
- **Smart scheduling**: Finds optimal time slots based on your availability
- **Conflict detection**: Prevents double-booking
- **Bidirectional sync**: Changes in calendar reflect in tasks and vice versa

### 👥 Personal CRM
- **Track relationships**: Keep notes on people you work with
- **Contact reminders**: Get notified when it's time to reach out
- **Context at your fingertips**: Quick access to conversation history and notes

### ⏰ Daily Check-ins
- **Morning check-in**: Set intentions, track habits, define priorities (4:30 AM default)
- **Periodic reminders**: Stay focused with regular check-ins (every 2 hours)
- **Evening review**: Reflect on accomplishments and learnings (8:00 PM default)

### 🔄 Sync & Backup
- **Git synchronization**: Sync your Obsidian vault to a remote repository
- **Automatic backups**: Daily backups with 30-day retention
- **Conflict resolution**: Smart merge strategies for multi-device workflows

### 🤖 LLM-Powered
- **OpenRouter integration**: Access to multiple LLM models
- **Cost optimization**: DeepSeek for fast, cheap tasks; Claude for complex reasoning
- **Conversation summarization**: Save storage while preserving context

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram account
- OpenRouter API key ([sign up](https://openrouter.ai))
- (Optional) Google Calendar API credentials
- (Optional) ntfy.sh for push notifications

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Initialize database**
   ```bash
   python -m src.database
   ```

5. **Run the bot**
   ```bash
   python -m src.main
   ```

See [SETUP.md](docs/SETUP.md) for detailed installation instructions.

## Docker Deployment

### Using Docker Compose

```bash
# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Using Coolify

See [.coolify/README.md](.coolify/README.md) for Coolify deployment instructions.

## Usage

### Basic Commands

- `/start` - Welcome message and quick start guide
- `/help` - List all available commands
- `/add <task>` - Add a new task
- `/tasks` - List your tasks
- `/schedule <task_id>` - Schedule a task on your calendar
- `/people` - List people in your network
- `/person <name>` - Add or view a person
- `/settings` - View and update preferences

### Natural Language

Just send a message to the bot:

```
"Call John about the proposal by Friday"
→ Creates task with due date, links to John's contact

"Meeting with Sarah tomorrow at 2pm for 1 hour"
→ Creates task and calendar event

"Remind me to follow up with client next week"
→ Creates task with estimated due date
```

### Daily Workflow

1. **Morning (4:30 AM)**
   - Receive morning check-in prompt
   - Log energy level, mood, habits
   - Set top 3 priorities for the day

2. **During Day (every 2 hours, 9 AM - 5 PM)**
   - Quick check-in: "What are you working on?"
   - Helps track actual work vs. planned

3. **Evening (8:00 PM)**
   - Review accomplishments
   - Note what's still pending
   - Capture learnings
   - Set tomorrow's top priority

## Architecture

```
┌─────────────────┐
│  Telegram Bot   │
└────────┬────────┘
         │
    ┌────┴────┐
    │  NLP    │  ← OpenRouter (DeepSeek/Claude)
    └────┬────┘
         │
    ┌────┴────────────────┐
    │                     │
┌───┴────┐         ┌──────┴──────┐
│ SQLite │         │  Obsidian   │
│  (DB)  │  ←──→   │   (Vault)   │
└────────┘         └──────┬──────┘
                          │
                     ┌────┴────┐
                     │   Git   │  ← Remote Sync
                     └─────────┘
```

### Tech Stack

- **Bot Framework**: python-telegram-bot 20.7
- **LLM**: OpenRouter (DeepSeek V3 + Claude 3.5 Sonnet)
- **Database**: SQLite with aiosqlite
- **Storage**: Obsidian markdown with frontmatter
- **Calendar**: Google Calendar API
- **Scheduling**: APScheduler
- **Notifications**: ntfy.sh
- **Voice**: OpenAI Whisper

## Configuration

### Environment Variables

See `.env.example` for all available options.

**Required**:
- `TELEGRAM_BOT_TOKEN` - From [@BotFather](https://t.me/BotFather)
- `OPENROUTER_API_KEY` - From [OpenRouter](https://openrouter.ai)

**Optional**:
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` - For calendar integration
- `NTFY_TOPIC` - For push notifications
- `GIT_REMOTE_URL` - For vault synchronization
- `TELEGRAM_ADMIN_CHAT_ID` - For scheduled check-ins

### User Settings

Customize per-user via `/settings`:

- Timezone
- Check-in times (morning, evening, periodic)
- Work hours
- Notification preferences
- Weekend scheduling

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_nlp.py

# Run integration tests
pytest tests/test_integration.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Database Migrations

Migrations are in `migrations/` directory. Applied automatically on bot startup.

## Backup & Recovery

### Manual Backup

```bash
cd scripts
./backup.sh
```

### Automated Backups

```bash
cd scripts
./setup_backup_cron.sh  # Daily at 2 AM
```

### Restore from Backup

```bash
cd scripts
./restore.sh ./backups/backup_20260131_120000.tar.gz
```

See [BACKUP_RECOVERY.md](docs/BACKUP_RECOVERY.md) for detailed backup documentation.

## Troubleshooting

### Bot not responding

1. Check if bot is running: `docker ps` or `ps aux | grep python`
2. View logs: `docker logs productivity-bot` or check log files
3. Verify `TELEGRAM_BOT_TOKEN` is correct
4. Ensure bot is not rate-limited by Telegram

### LLM requests failing

1. Verify `OPENROUTER_API_KEY` is valid
2. Check OpenRouter account has credits
3. Review logs for specific error messages
4. Try fallback model manually

### Calendar integration not working

1. Verify all Google credentials are set
2. Run `scripts/setup_google_auth.py` to refresh token
3. Ensure Google Calendar API is enabled in Google Cloud Console
4. Check token hasn't expired

### Database locked

1. Ensure only one bot instance is running
2. Check file permissions on database
3. Restart bot to release locks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [python-telegram-bot](https://python-telegram-bot.org/)
- LLM access via [OpenRouter](https://openrouter.ai)
- Inspired by [Obsidian](https://obsidian.md) for knowledge management
- Notifications powered by [ntfy.sh](https://ntfy.sh)

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## Roadmap

- [ ] Mobile app for offline task capture
- [ ] Email integration for task creation
- [ ] Team collaboration features
- [ ] Advanced analytics and insights
- [ ] Voice-first interaction mode
- [ ] Custom LLM model fine-tuning
