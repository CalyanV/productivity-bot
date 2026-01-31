#!/bin/bash
# Setup automated backups via cron
#
# This script configures cron to run backups automatically
#
# Usage:
#   ./setup_backup_cron.sh [schedule]
#
# Examples:
#   ./setup_backup_cron.sh "0 2 * * *"    # Daily at 2 AM (default)
#   ./setup_backup_cron.sh "0 */6 * * *"  # Every 6 hours
#   ./setup_backup_cron.sh "0 0 * * 0"    # Weekly on Sunday midnight

set -e

SCHEDULE="${1:-0 2 * * *}"  # Default: Daily at 2 AM
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup.sh"

if [ ! -f "${BACKUP_SCRIPT}" ]; then
    echo "Error: backup.sh not found at ${BACKUP_SCRIPT}"
    exit 1
fi

# Make backup script executable
chmod +x "${BACKUP_SCRIPT}"

echo "🔧 Setting up automated backups"
echo ""
echo "Schedule: ${SCHEDULE}"
echo "Script: ${BACKUP_SCRIPT}"
echo ""

# Create cron job entry
CRON_JOB="${SCHEDULE} cd ${SCRIPT_DIR} && ./backup.sh >> /var/log/productivity-bot-backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup.sh"; then
    echo "⚠️  Backup cron job already exists"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "backup.sh"
    echo ""
    read -p "Remove existing and create new? (yes/no): " confirm

    if [ "${confirm}" = "yes" ]; then
        # Remove existing backup cron jobs
        crontab -l | grep -v "backup.sh" | crontab -
        echo "✅ Removed existing cron job"
    else
        echo "Setup cancelled"
        exit 0
    fi
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "${CRON_JOB}") | crontab -

echo "✅ Cron job created successfully!"
echo ""
echo "Backup schedule:"
crontab -l | grep "backup.sh"
echo ""
echo "Logs will be written to: /var/log/productivity-bot-backup.log"
echo ""
echo "To verify cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove automated backups:"
echo "  crontab -e  (then delete the backup.sh line)"
echo ""
echo "To test backup now:"
echo "  cd ${SCRIPT_DIR} && ./backup.sh"
