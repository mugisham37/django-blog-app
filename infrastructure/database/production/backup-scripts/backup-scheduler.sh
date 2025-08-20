#!/bin/bash
set -e

# PostgreSQL Production Backup Scheduler
# Handles automated backups with retention and S3 upload

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/postgresql/backup.log"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Install required packages
apk add --no-cache aws-cli cron

# Create crontab entry
echo "$BACKUP_SCHEDULE root $SCRIPT_DIR/perform-backup.sh" > /etc/crontabs/root

# Start cron daemon
crond -f -d 8 &

# Keep container running
while true; do
    sleep 3600
    
    # Health check - ensure backup process is working
    if [ -f "$BACKUP_DIR/last_backup_status" ]; then
        LAST_BACKUP=$(cat "$BACKUP_DIR/last_backup_status")
        CURRENT_TIME=$(date +%s)
        
        # Alert if last backup is older than 25 hours
        if [ $((CURRENT_TIME - LAST_BACKUP)) -gt 90000 ]; then
            log "WARNING: Last backup is older than 25 hours"
        fi
    fi
done