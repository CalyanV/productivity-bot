# Backup and Recovery Guide

This guide covers backup strategies, automated backups, and disaster recovery procedures for the Productivity Bot.

## Table of Contents

- [Backup Strategy](#backup-strategy)
- [What Gets Backed Up](#what-gets-backed-up)
- [Manual Backup](#manual-backup)
- [Automated Backups](#automated-backups)
- [Restoring from Backup](#restoring-from-backup)
- [Disaster Recovery](#disaster-recovery)
- [Best Practices](#best-practices)

## Backup Strategy

The bot uses a **3-2-1 backup strategy**:
- **3** copies of your data (production + 2 backups)
- **2** different storage media (local + remote)
- **1** offsite copy (cloud storage or remote server)

### Default Configuration

- **Frequency**: Daily at 2:00 AM
- **Retention**: 30 days
- **Format**: Compressed tar.gz archives
- **Location**: `./backups/`

## What Gets Backed Up

### 1. SQLite Database (`bot.db`)
Contains:
- Tasks and projects
- People/contacts
- Daily logs
- Conversation history
- User settings
- Calendar sync data
- Notification history

**Backup format**:
- Binary copy (`bot.db`)
- SQL dump (`bot_dump.sql`) for easier recovery

### 2. Obsidian Vault
Contains:
- Task markdown files
- People notes
- Daily logs
- Project notes

**Backup format**:
- Complete directory copy
- Excludes `.git` folder (if using git sync)

### 3. Metadata
Each backup includes:
- Timestamp
- Source paths
- Backup version

## Manual Backup

### Run Backup Manually

```bash
cd scripts
./backup.sh
```

### Custom Backup Location

```bash
BACKUP_DIR=/path/to/backups ./backup.sh
```

### Custom Retention Period

```bash
RETENTION_DAYS=60 ./backup.sh
```

### Verify Backup

```bash
# List backups
ls -lh ./backups/

# Inspect backup contents
tar -tzf ./backups/backup_20260131_120000.tar.gz
```

## Automated Backups

### Setup Cron Job

```bash
cd scripts
./setup_backup_cron.sh
```

This creates a daily backup at 2:00 AM.

### Custom Schedule

```bash
# Every 6 hours
./setup_backup_cron.sh "0 */6 * * *"

# Weekly on Sunday at midnight
./setup_backup_cron.sh "0 0 * * 0"

# Twice daily (2 AM and 2 PM)
./setup_backup_cron.sh "0 2,14 * * *"
```

### Verify Cron Job

```bash
crontab -l | grep backup
```

### View Backup Logs

```bash
tail -f /var/log/productivity-bot-backup.log
```

### Docker/Coolify Backups

If using Docker with Coolify, backups are configured in `.coolify/deploy.yml`:

```yaml
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  paths:
    - /app/data/bot.db
    - /app/obsidian-vault
  retention: 30
```

## Restoring from Backup

### List Available Backups

```bash
ls -lh ./backups/backup_*.tar.gz
```

### Restore from Backup

```bash
cd scripts
./restore.sh ./backups/backup_20260131_120000.tar.gz
```

**Warning**: This will overwrite existing data!

### Pre-Restore Safety

The restore script automatically:
1. Shows backup metadata
2. Asks for confirmation
3. Creates a pre-restore backup
4. Restores data
5. Saves pre-restore backup for rollback

### Rollback if Needed

If the restore didn't work:

```bash
# Find pre-restore backup
ls -lh ./backups/pre_restore_*

# Restore from pre-restore backup
./restore.sh ./backups/pre_restore_20260131_130000
```

### Selective Restore

#### Restore Only Database

```bash
tar -xzf ./backups/backup_20260131_120000.tar.gz
cp backup_20260131_120000/bot.db ../data/bot.db
```

#### Restore Only Vault

```bash
tar -xzf ./backups/backup_20260131_120000.tar.gz
rm -rf ../obsidian-vault/*
cp -r backup_20260131_120000/obsidian-vault/* ../obsidian-vault/
```

#### Restore from SQL Dump

If the binary database is corrupted:

```bash
tar -xzf ./backups/backup_20260131_120000.tar.gz
sqlite3 ../data/bot.db < backup_20260131_120000/bot_dump.sql
```

## Disaster Recovery

### Scenario 1: Database Corrupted

```bash
# Stop the bot
docker stop productivity-bot

# Restore from latest backup
cd scripts
./restore.sh $(ls -t ./backups/backup_*.tar.gz | head -n 1)

# Start the bot
docker start productivity-bot
```

### Scenario 2: Vault Accidentally Deleted

```bash
# Extract and restore only vault
tar -xzf ./backups/backup_20260131_120000.tar.gz
cp -r backup_20260131_120000/obsidian-vault/* ../obsidian-vault/

# Rebuild database index from vault
# (The bot will do this on next start if git sync is enabled)
```

### Scenario 3: Complete Server Loss

1. **Setup new server**
2. **Install bot** (Docker + Coolify)
3. **Copy backups** to new server
4. **Restore from backup**:
   ```bash
   ./restore.sh ./backups/backup_YYYYMMDD_HHMMSS.tar.gz
   ```
5. **Update environment variables** (tokens, API keys)
6. **Start bot**

### Scenario 4: Backup Files Corrupted

If backups are corrupted, try:

1. **Use SQL dump** instead of binary:
   ```bash
   sqlite3 ../data/bot.db < backup_*/bot_dump.sql
   ```

2. **Recover from git** (if using git sync):
   ```bash
   cd ../obsidian-vault
   git log  # Find good commit
   git checkout <commit-hash>
   ```

3. **Rebuild from Obsidian**:
   ```bash
   # If vault is intact but database is lost
   # Bot will rebuild index on startup
   ```

## Best Practices

### 1. Test Restores Regularly

```bash
# Monthly test restore to verify backups work
cd scripts
./restore.sh ./backups/backup_latest.tar.gz
```

### 2. Offsite Backups

Copy backups to remote storage:

```bash
# To S3
aws s3 sync ./backups/ s3://my-bucket/bot-backups/

# To remote server via rsync
rsync -avz ./backups/ user@remote:/backups/bot/

# To cloud storage (rclone)
rclone sync ./backups/ remote:bot-backups/
```

### 3. Monitor Backup Success

Check logs regularly:

```bash
tail -20 /var/log/productivity-bot-backup.log
```

Set up alerts for backup failures (e.g., via cron + email):

```bash
# In crontab, change from:
0 2 * * * cd /path/to/scripts && ./backup.sh

# To:
0 2 * * * cd /path/to/scripts && ./backup.sh || echo "Backup failed" | mail -s "Bot Backup Failed" you@example.com
```

### 4. Version Your Backups

Keep multiple versions:
- Daily backups: 30 days
- Weekly backups: 3 months
- Monthly backups: 1 year

```bash
# In backup.sh, add separate retention for weekly/monthly
if [ $(date +%u) -eq 7 ]; then
    # Sunday - keep as weekly
    cp backup_${TIMESTAMP}.tar.gz weekly_backup_${TIMESTAMP}.tar.gz
fi
```

### 5. Encrypt Sensitive Backups

If backups contain sensitive data:

```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup_20260131_120000.tar.gz

# Decrypt when needed
gpg --decrypt backup_20260131_120000.tar.gz.gpg > backup_20260131_120000.tar.gz
```

### 6. Document Your Recovery Plan

Keep a printed copy of:
- Backup locations
- Restoration commands
- Access credentials (encrypted)
- Emergency contacts

## Troubleshooting

### Backup Script Fails

```bash
# Check permissions
ls -la scripts/backup.sh
chmod +x scripts/backup.sh

# Check disk space
df -h

# Run with verbose output
bash -x scripts/backup.sh
```

### Cron Job Not Running

```bash
# Check cron service
systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test cron job manually
cd /path/to/scripts && ./backup.sh
```

### Restore Fails

```bash
# Verify backup integrity
tar -tzf backup_file.tar.gz

# Extract to temp location first
mkdir temp_restore
tar -xzf backup_file.tar.gz -C temp_restore
ls -la temp_restore/

# Copy manually
cp temp_restore/backup_*/bot.db ../data/
```

## Support

For backup issues:
1. Check logs in `/var/log/productivity-bot-backup.log`
2. Verify disk space with `df -h`
3. Test backup script manually
4. Review this documentation
5. Open an issue on GitHub with logs
