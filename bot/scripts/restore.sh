#!/bin/bash
# Restore script for productivity bot
#
# This script restores from a backup created by backup.sh
#
# Usage:
#   ./restore.sh <backup_file.tar.gz>
#
# Example:
#   ./restore.sh ./backups/backup_20260131_120000.tar.gz

set -e

BACKUP_FILE="$1"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Error: Backup file required"
    echo "Usage: $0 <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/backup_*.tar.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Configuration
DATABASE_PATH="${DATABASE_PATH:-../data/bot.db}"
VAULT_PATH="${VAULT_PATH:-../obsidian-vault}"
RESTORE_DIR=$(mktemp -d)

echo "🔄 Restoring from backup: ${BACKUP_FILE}"
echo ""
echo "⚠️  WARNING: This will OVERWRITE existing data!"
echo ""
echo "Target locations:"
echo "  Database: ${DATABASE_PATH}"
echo "  Vault: ${VAULT_PATH}"
echo ""
read -p "Continue with restore? (yes/no): " confirm

if [ "${confirm}" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Extract backup
echo "📦 Extracting backup..."
tar -xzf "${BACKUP_FILE}" -C "${RESTORE_DIR}"

# Find extracted directory
BACKUP_DIR=$(find "${RESTORE_DIR}" -maxdepth 1 -type d -name "backup_*" | head -n 1)

if [ -z "${BACKUP_DIR}" ]; then
    echo "Error: Invalid backup file"
    rm -rf "${RESTORE_DIR}"
    exit 1
fi

# Show backup metadata
if [ -f "${BACKUP_DIR}/metadata.json" ]; then
    echo "📋 Backup information:"
    cat "${BACKUP_DIR}/metadata.json"
    echo ""
fi

# Backup current data before restore
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PRE_RESTORE_BACKUP="./backups/pre_restore_${TIMESTAMP}"

echo "💾 Creating pre-restore backup at ${PRE_RESTORE_BACKUP}..."
mkdir -p "${PRE_RESTORE_BACKUP}"

if [ -f "${DATABASE_PATH}" ]; then
    cp "${DATABASE_PATH}" "${PRE_RESTORE_BACKUP}/bot.db.before"
fi

if [ -d "${VAULT_PATH}" ]; then
    cp -r "${VAULT_PATH}" "${PRE_RESTORE_BACKUP}/obsidian-vault.before"
fi

# Restore database
if [ -f "${BACKUP_DIR}/bot.db" ]; then
    echo "📦 Restoring database..."
    mkdir -p "$(dirname "${DATABASE_PATH}")"
    cp "${BACKUP_DIR}/bot.db" "${DATABASE_PATH}"
    echo "✅ Database restored"
else
    echo "⚠️  No database found in backup"
fi

# Restore vault
if [ -d "${BACKUP_DIR}/obsidian-vault" ]; then
    echo "📦 Restoring Obsidian vault..."

    # Remove existing vault
    if [ -d "${VAULT_PATH}" ]; then
        rm -rf "${VAULT_PATH}"
    fi

    mkdir -p "${VAULT_PATH}"
    cp -r "${BACKUP_DIR}/obsidian-vault/"* "${VAULT_PATH}/"

    echo "✅ Vault restored"
else
    echo "⚠️  No vault found in backup"
fi

# Cleanup
rm -rf "${RESTORE_DIR}"

echo ""
echo "✅ Restore completed successfully!"
echo ""
echo "Pre-restore backup saved at: ${PRE_RESTORE_BACKUP}"
echo ""
echo "Next steps:"
echo "1. Restart the bot if it's running"
echo "2. Verify data is correct"
echo "3. If everything looks good, you can delete the pre-restore backup"
