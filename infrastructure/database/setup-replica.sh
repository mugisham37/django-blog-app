#!/bin/bash
# PostgreSQL Read Replica Setup Script

set -e

# Configuration
PRIMARY_HOST=${PRIMARY_HOST:-"postgres-primary"}
PRIMARY_PORT=${PRIMARY_PORT:-5432}
REPLICA_USER=${REPLICA_USER:-"replicator"}
REPLICA_PASSWORD=${REPLICA_PASSWORD:-"replica_password"}
PGDATA=${PGDATA:-"/var/lib/postgresql/data"}

echo "Setting up PostgreSQL read replica..."

# Stop PostgreSQL if running
pg_ctl stop -D "$PGDATA" -m fast || true

# Remove existing data directory
rm -rf "$PGDATA"/*

# Create base backup from primary
echo "Creating base backup from primary server..."
PGPASSWORD="$REPLICA_PASSWORD" pg_basebackup \
    -h "$PRIMARY_HOST" \
    -p "$PRIMARY_PORT" \
    -U "$REPLICA_USER" \
    -D "$PGDATA" \
    -P \
    -W \
    -R \
    -X stream

# Copy replica configuration
cp /etc/postgresql/postgresql-replica.conf "$PGDATA/postgresql.conf"

# Create recovery configuration
cat > "$PGDATA/postgresql.auto.conf" << EOF
# Replica configuration
primary_conninfo = 'host=$PRIMARY_HOST port=$PRIMARY_PORT user=$REPLICA_USER password=$REPLICA_PASSWORD application_name=replica1'
primary_slot_name = 'replica1_slot'
restore_command = 'cp /var/lib/postgresql/archive/%f %p'
recovery_target_timeline = 'latest'
EOF

# Set proper permissions
chown -R postgres:postgres "$PGDATA"
chmod 700 "$PGDATA"

echo "Read replica setup completed successfully!"
echo "Starting PostgreSQL replica..."

# Start PostgreSQL
pg_ctl start -D "$PGDATA" -l "$PGDATA/log/postgresql.log"

echo "PostgreSQL read replica is now running!"