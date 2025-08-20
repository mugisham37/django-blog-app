#!/bin/bash
set -e

# PostgreSQL Production Backup Script
# Performs full database backup with compression and S3 upload

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/postgresql/backup.log"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="postgres_backup_${DATE}.sql.gz"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    # Update backup status with error
    echo "$(date +%s)" > "$BACKUP_DIR/last_backup_error"
    exit 1
}

log "Starting PostgreSQL backup process"

# Check if required environment variables are set
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    error_exit "Required PostgreSQL environment variables not set"
fi

# Wait for PostgreSQL to be ready
log "Checking PostgreSQL connectivity"
until pg_isready -h "$POSTGRES_HOST" -p 5432 -U "$POSTGRES_USER"; do
    log "Waiting for PostgreSQL to be ready..."
    sleep 5
done

# Perform database backup
log "Creating database backup: $BACKUP_FILE"
export PGPASSWORD="$POSTGRES_PASSWORD"

if ! pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --verbose \
    --no-owner \
    --no-privileges \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_PATH.custom"; then
    error_exit "Database backup failed"
fi

# Create SQL dump as well for easier restoration
if ! pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --verbose \
    --no-owner \
    --no-privileges \
    | gzip > "$BACKUP_PATH"; then
    error_exit "SQL dump creation failed"
fi

# Verify backup integrity
log "Verifying backup integrity"
if ! gzip -t "$BACKUP_PATH"; then
    error_exit "Backup file integrity check failed"
fi

# Get backup file size
BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
log "Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    log "Uploading backup to S3: s3://$S3_BUCKET/database-backups/"
    
    if aws s3 cp "$BACKUP_PATH" "s3://$S3_BUCKET/database-backups/" \
        --storage-class STANDARD_IA \
        --metadata "backup-date=$DATE,database=$POSTGRES_DB"; then
        log "Backup uploaded to S3 successfully"
        
        # Upload custom format backup as well
        aws s3 cp "$BACKUP_PATH.custom" "s3://$S3_BUCKET/database-backups/" \
            --storage-class STANDARD_IA \
            --metadata "backup-date=$DATE,database=$POSTGRES_DB,format=custom"
    else
        log "WARNING: S3 upload failed, backup retained locally"
    fi
fi

# Clean up old local backups
log "Cleaning up old backups (retention: ${BACKUP_RETENTION_DAYS:-30} days)"
find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz" -mtime +${BACKUP_RETENTION_DAYS:-30} -delete
find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz.custom" -mtime +${BACKUP_RETENTION_DAYS:-30} -delete

# Update backup status
echo "$(date +%s)" > "$BACKUP_DIR/last_backup_status"
log "Backup process completed successfully"

# Generate backup report
cat > "$BACKUP_DIR/backup_report_${DATE}.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "backup_file": "$BACKUP_FILE",
  "backup_size": "$BACKUP_SIZE",
  "database": "$POSTGRES_DB",
  "host": "$POSTGRES_HOST",
  "s3_upload": $([ -n "$S3_BUCKET" ] && echo "true" || echo "false"),
  "status": "success"
}
EOF

log "Backup report generated: backup_report_${DATE}.json"