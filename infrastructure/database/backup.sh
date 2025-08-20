#!/bin/bash
# PostgreSQL Backup Script with rotation and compression

set -e

# Configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-"enterprise_db"}
DB_USER=${DB_USER:-"postgres"}
BACKUP_DIR=${BACKUP_DIR:-"/var/backups/postgresql"}
RETENTION_DAYS=${RETENTION_DAYS:-30}
COMPRESSION=${COMPRESSION:-"gzip"}
S3_BUCKET=${S3_BUCKET:-""}
SLACK_WEBHOOK=${SLACK_WEBHOOK:-""}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

# Function to send notification
send_notification() {
    local message="$1"
    local status="$2"
    
    echo "$message"
    
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local color="good"
        if [[ "$status" == "error" ]]; then
            color="danger"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK" || true
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "${DB_NAME}_*.sql*" -mtime +$RETENTION_DAYS -delete
    echo "Cleanup completed"
}

# Function to upload to S3
upload_to_s3() {
    if [[ -n "$S3_BUCKET" ]]; then
        echo "Uploading backup to S3..."
        aws s3 cp "$COMPRESSED_FILE" "s3://$S3_BUCKET/database-backups/" || {
            send_notification "❌ Failed to upload backup to S3" "error"
            return 1
        }
        echo "Backup uploaded to S3 successfully"
    fi
}

# Function to verify backup
verify_backup() {
    local backup_file="$1"
    
    echo "Verifying backup integrity..."
    
    if [[ "$backup_file" == *.gz ]]; then
        gzip -t "$backup_file" || {
            send_notification "❌ Backup file is corrupted (gzip test failed)" "error"
            return 1
        }
    fi
    
    # Check if backup file is not empty
    if [[ ! -s "$backup_file" ]]; then
        send_notification "❌ Backup file is empty" "error"
        return 1
    fi
    
    echo "Backup verification passed"
    return 0
}

# Main backup process
main() {
    echo "Starting PostgreSQL backup for database: $DB_NAME"
    echo "Backup will be saved to: $BACKUP_FILE"
    
    # Create database dump
    PGPASSWORD="$PGPASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --file="$BACKUP_FILE" || {
        send_notification "❌ Database backup failed for $DB_NAME" "error"
        exit 1
    }
    
    # Compress backup if requested
    if [[ "$COMPRESSION" == "gzip" ]]; then
        echo "Compressing backup..."
        gzip "$BACKUP_FILE"
        BACKUP_FILE="$COMPRESSED_FILE"
    fi
    
    # Verify backup
    verify_backup "$BACKUP_FILE" || exit 1
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    
    # Upload to S3 if configured
    upload_to_s3
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Send success notification
    send_notification "✅ Database backup completed successfully
Database: $DB_NAME
File: $(basename "$BACKUP_FILE")
Size: $BACKUP_SIZE
Location: $BACKUP_FILE" "success"
    
    echo "Backup completed successfully!"
}

# Handle script interruption
trap 'send_notification "❌ Backup process was interrupted" "error"; exit 1' INT TERM

# Run main function
main "$@"