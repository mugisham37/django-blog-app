#!/bin/bash
set -e

# PostgreSQL Production Restore Script
# Restores database from backup with safety checks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/postgresql/restore.log"
BACKUP_DIR="/backups"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -f, --file BACKUP_FILE    Backup file to restore from"
    echo "  -s, --s3-key S3_KEY       S3 key to download and restore from"
    echo "  -d, --database DATABASE   Target database name (default: from env)"
    echo "  --force                   Skip confirmation prompts"
    echo "  --dry-run                 Show what would be done without executing"
    echo "  -h, --help               Show this help message"
    exit 1
}

# Parse command line arguments
BACKUP_FILE=""
S3_KEY=""
TARGET_DB="$POSTGRES_DB"
FORCE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -s|--s3-key)
            S3_KEY="$2"
            shift 2
            ;;
        -d|--database)
            TARGET_DB="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate inputs
if [ -z "$BACKUP_FILE" ] && [ -z "$S3_KEY" ]; then
    error_exit "Either --file or --s3-key must be specified"
fi

if [ -z "$TARGET_DB" ]; then
    error_exit "Target database not specified"
fi

log "Starting PostgreSQL restore process"

# Download from S3 if specified
if [ -n "$S3_KEY" ]; then
    if [ -z "$S3_BUCKET" ]; then
        error_exit "S3_BUCKET environment variable not set"
    fi
    
    BACKUP_FILE="$BACKUP_DIR/$(basename "$S3_KEY")"
    log "Downloading backup from S3: s3://$S3_BUCKET/$S3_KEY"
    
    if [ "$DRY_RUN" = false ]; then
        aws s3 cp "s3://$S3_BUCKET/$S3_KEY" "$BACKUP_FILE" || error_exit "Failed to download backup from S3"
    fi
fi

# Validate backup file
if [ ! -f "$BACKUP_FILE" ] && [ "$DRY_RUN" = false ]; then
    error_exit "Backup file not found: $BACKUP_FILE"
fi

# Check backup file integrity
if [ "$DRY_RUN" = false ]; then
    log "Verifying backup file integrity"
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        if ! gzip -t "$BACKUP_FILE"; then
            error_exit "Backup file integrity check failed"
        fi
    fi
fi

# Safety confirmation
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    echo "WARNING: This will completely replace the database '$TARGET_DB'"
    echo "Backup file: $BACKUP_FILE"
    echo "Target database: $TARGET_DB"
    echo "Target host: $POSTGRES_HOST"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
fi

if [ "$DRY_RUN" = true ]; then
    log "DRY RUN: Would restore $BACKUP_FILE to database $TARGET_DB"
    exit 0
fi

# Wait for PostgreSQL to be ready
log "Checking PostgreSQL connectivity"
export PGPASSWORD="$POSTGRES_PASSWORD"
until pg_isready -h "$POSTGRES_HOST" -p 5432 -U "$POSTGRES_USER"; do
    log "Waiting for PostgreSQL to be ready..."
    sleep 5
done

# Create backup of current database before restore
CURRENT_BACKUP="$BACKUP_DIR/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
log "Creating backup of current database: $CURRENT_BACKUP"
pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$TARGET_DB" | gzip > "$CURRENT_BACKUP"

# Terminate active connections to the database
log "Terminating active connections to database: $TARGET_DB"
psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "
    SELECT pg_terminate_backend(pid) 
    FROM pg_stat_activity 
    WHERE datname = '$TARGET_DB' AND pid <> pg_backend_pid();
"

# Drop and recreate database
log "Dropping and recreating database: $TARGET_DB"
psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$TARGET_DB\";"
psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$TARGET_DB\";"

# Restore from backup
log "Restoring database from backup: $BACKUP_FILE"
if [[ "$BACKUP_FILE" == *.custom ]]; then
    # Custom format restore
    pg_restore -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$TARGET_DB" \
        --verbose \
        --clean \
        --no-owner \
        --no-privileges \
        "$BACKUP_FILE"
else
    # SQL dump restore
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        gunzip -c "$BACKUP_FILE" | psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$TARGET_DB"
    else
        psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$TARGET_DB" < "$BACKUP_FILE"
    fi
fi

# Verify restore
log "Verifying database restore"
TABLE_COUNT=$(psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$TARGET_DB" -t -c "
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
")

if [ "$TABLE_COUNT" -gt 0 ]; then
    log "Database restore completed successfully ($TABLE_COUNT tables restored)"
else
    error_exit "Database restore verification failed - no tables found"
fi

# Generate restore report
cat > "$BACKUP_DIR/restore_report_$(date +%Y%m%d_%H%M%S).json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "backup_file": "$BACKUP_FILE",
  "target_database": "$TARGET_DB",
  "host": "$POSTGRES_HOST",
  "tables_restored": $TABLE_COUNT,
  "pre_restore_backup": "$CURRENT_BACKUP",
  "status": "success"
}
EOF

log "Database restore process completed successfully"