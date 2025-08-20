#!/bin/bash
# PostgreSQL Restore Script with safety checks

set -e

# Configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-"enterprise_db"}
DB_USER=${DB_USER:-"postgres"}
BACKUP_DIR=${BACKUP_DIR:-"/var/backups/postgresql"}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS] BACKUP_FILE"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -f, --force             Skip confirmation prompts"
    echo "  -c, --create-db         Create database if it doesn't exist"
    echo "  -d, --drop-existing     Drop existing database before restore"
    echo "  --dry-run               Show what would be done without executing"
    echo ""
    echo "Environment variables:"
    echo "  DB_HOST                 Database host (default: localhost)"
    echo "  DB_PORT                 Database port (default: 5432)"
    echo "  DB_NAME                 Database name (default: enterprise_db)"
    echo "  DB_USER                 Database user (default: postgres)"
    echo "  PGPASSWORD              Database password"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/backup.sql"
    echo "  $0 --force --create-db backup_20231201_120000.sql.gz"
    echo "  $0 --dry-run latest"
}

# Function to find latest backup
find_latest_backup() {
    local latest_backup
    latest_backup=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql*" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -z "$latest_backup" ]]; then
        echo "❌ No backup files found in $BACKUP_DIR"
        exit 1
    fi
    
    echo "$latest_backup"
}

# Function to verify backup file
verify_backup_file() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        echo "❌ Backup file not found: $backup_file"
        exit 1
    fi
    
    echo "Verifying backup file: $backup_file"
    
    # Check if file is compressed
    if [[ "$backup_file" == *.gz ]]; then
        gzip -t "$backup_file" || {
            echo "❌ Backup file is corrupted (gzip test failed)"
            exit 1
        }
    fi
    
    # Check file size
    if [[ ! -s "$backup_file" ]]; then
        echo "❌ Backup file is empty"
        exit 1
    fi
    
    echo "✅ Backup file verification passed"
}

# Function to check database connection
check_db_connection() {
    echo "Checking database connection..."
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1;" > /dev/null || {
        echo "❌ Cannot connect to database server"
        exit 1
    }
    echo "✅ Database connection successful"
}

# Function to check if database exists
database_exists() {
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | grep -q 1
}

# Function to create database
create_database() {
    echo "Creating database: $DB_NAME"
    PGPASSWORD="$PGPASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" || {
        echo "❌ Failed to create database: $DB_NAME"
        exit 1
    }
    echo "✅ Database created successfully"
}

# Function to drop database
drop_database() {
    echo "Dropping existing database: $DB_NAME"
    PGPASSWORD="$PGPASSWORD" dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" || {
        echo "❌ Failed to drop database: $DB_NAME"
        exit 1
    }
    echo "✅ Database dropped successfully"
}

# Function to restore database
restore_database() {
    local backup_file="$1"
    
    echo "Starting database restore..."
    echo "Source: $backup_file"
    echo "Target: $DB_NAME on $DB_HOST:$DB_PORT"
    
    # Determine restore command based on file type
    if [[ "$backup_file" == *.gz ]]; then
        echo "Restoring from compressed backup..."
        gunzip -c "$backup_file" | PGPASSWORD="$PGPASSWORD" pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --verbose \
            --no-password || {
            echo "❌ Database restore failed"
            exit 1
        }
    elif [[ "$backup_file" == *.sql ]]; then
        echo "Restoring from SQL backup..."
        PGPASSWORD="$PGPASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -f "$backup_file" || {
            echo "❌ Database restore failed"
            exit 1
        }
    else
        # Assume custom format
        echo "Restoring from custom format backup..."
        PGPASSWORD="$PGPASSWORD" pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --verbose \
            --no-password \
            "$backup_file" || {
            echo "❌ Database restore failed"
            exit 1
        }
    fi
    
    echo "✅ Database restore completed successfully"
}

# Function to create pre-restore backup
create_pre_restore_backup() {
    if database_exists; then
        echo "Creating pre-restore backup..."
        local pre_backup_file="$BACKUP_DIR/${DB_NAME}_pre_restore_$(date +%Y%m%d_%H%M%S).sql"
        
        PGPASSWORD="$PGPASSWORD" pg_dump \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --format=custom \
            --file="$pre_backup_file" || {
            echo "❌ Failed to create pre-restore backup"
            exit 1
        }
        
        echo "✅ Pre-restore backup created: $pre_backup_file"
    fi
}

# Parse command line arguments
FORCE=false
CREATE_DB=false
DROP_EXISTING=false
DRY_RUN=false
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -c|--create-db)
            CREATE_DB=true
            shift
            ;;
        -d|--drop-existing)
            DROP_EXISTING=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        latest)
            BACKUP_FILE=$(find_latest_backup)
            shift
            ;;
        *)
            if [[ -z "$BACKUP_FILE" ]]; then
                BACKUP_FILE="$1"
            else
                echo "❌ Unknown option: $1"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [[ -z "$BACKUP_FILE" ]]; then
    echo "❌ Backup file not specified"
    usage
    exit 1
fi

# Convert relative path to absolute if needed
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

# Main restore process
main() {
    echo "PostgreSQL Database Restore"
    echo "=========================="
    
    # Verify backup file
    verify_backup_file "$BACKUP_FILE"
    
    # Check database connection
    check_db_connection
    
    # Show restore plan
    echo ""
    echo "Restore Plan:"
    echo "  Source file: $BACKUP_FILE"
    echo "  Target database: $DB_NAME"
    echo "  Database host: $DB_HOST:$DB_PORT"
    echo "  Database user: $DB_USER"
    echo "  Create database: $CREATE_DB"
    echo "  Drop existing: $DROP_EXISTING"
    echo ""
    
    if [[ "$DRY_RUN" == true ]]; then
        echo "🔍 DRY RUN - No changes will be made"
        exit 0
    fi
    
    # Confirmation prompt
    if [[ "$FORCE" != true ]]; then
        read -p "Do you want to proceed with the restore? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Restore cancelled"
            exit 0
        fi
    fi
    
    # Handle existing database
    if database_exists; then
        if [[ "$DROP_EXISTING" == true ]]; then
            create_pre_restore_backup
            drop_database
            create_database
        else
            echo "⚠️  Database $DB_NAME already exists"
            if [[ "$FORCE" != true ]]; then
                read -p "Continue with restore to existing database? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    echo "Restore cancelled"
                    exit 0
                fi
            fi
            create_pre_restore_backup
        fi
    else
        if [[ "$CREATE_DB" == true ]]; then
            create_database
        else
            echo "❌ Database $DB_NAME does not exist. Use --create-db to create it."
            exit 1
        fi
    fi
    
    # Perform restore
    restore_database "$BACKUP_FILE"
    
    echo ""
    echo "🎉 Database restore completed successfully!"
}

# Handle script interruption
trap 'echo "❌ Restore process was interrupted"; exit 1' INT TERM

# Run main function
main "$@"