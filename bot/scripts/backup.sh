#!/bin/bash
# Backup script for productivity bot
#
# This script backs up:
# - SQLite database
# - Obsidian vault
# - Git repository (if configured)
#
# Usage:
#   ./backup.sh
#
# Environment variables:
#   BACKUP_DIR - Directory to store backups (default: ./backups)
#   DATABASE_PATH - Path to SQLite database (default: ../data/bot.db)
#   VAULT_PATH - Path to Obsidian vault (default: ../obsidian-vault)
#   RETENTION_DAYS - Days to keep backups (default: 30)

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATABASE_PATH="${DATABASE_PATH:-../data/bot.db}"
VAULT_PATH="${VAULT_PATH:-../obsidian-vault}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "🔄 Starting backup: ${BACKUP_NAME}"
echo ""

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Backup database
if [ -f "${DATABASE_PATH}" ]; then
    echo "📦 Backing up database..."
    cp "${DATABASE_PATH}" "${BACKUP_PATH}/bot.db"

    # Create a text dump for easier recovery
    sqlite3 "${DATABASE_PATH}" .dump > "${BACKUP_PATH}/bot_dump.sql"

    echo "✅ Database backed up"
else
    echo "⚠️  Database not found at ${DATABASE_PATH}"
fi

# Backup Obsidian vault
if [ -d "${VAULT_PATH}" ]; then
    echo "📦 Backing up Obsidian vault..."

    # Use rsync for efficient backup
    if command -v rsync &> /dev/null; then
        rsync -av --exclude='.git' "${VAULT_PATH}/" "${BACKUP_PATH}/obsidian-vault/"
    else
        cp -r "${VAULT_PATH}" "${BACKUP_PATH}/obsidian-vault"
    fi

    echo "✅ Vault backed up"
else
    echo "⚠️  Vault not found at ${VAULT_PATH}"
fi

# Create backup metadata
cat > "${BACKUP_PATH}/metadata.json" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "database_path": "${DATABASE_PATH}",
    "vault_path": "${VAULT_PATH}",
    "backup_version": "1.0"
}
EOF

# Compress backup
echo "🗜️  Compressing backup..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"

BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
echo "✅ Backup compressed: ${BACKUP_SIZE}"

# Cleanup old backups
echo "🧹 Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING=$(find "${BACKUP_DIR}" -name "backup_*.tar.gz" | wc -l)
echo "✅ ${REMAINING} backups remaining"

echo ""
echo "✅ Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""
echo "To restore this backup, run:"
echo "  ./restore.sh ${BACKUP_NAME}.tar.gz"
