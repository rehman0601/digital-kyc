#!/bin/bash
# Disaster Recovery - Platform Restoration Script
# Pulls database dump and upload archives from S3, restoring application state.

set -e

# Usage check
if [ -z "$1" ]; then
  echo "Usage: $0 <TIMESTAMP>"
  echo "Example: $0 20260621_211530"
  exit 1
fi

BACKUP_TS="$1"

# Configuration variables (overridden via env vars in production)
DB_HOST=${DB_HOST:-"localhost"}
DB_USER=${DB_USER:-"kyc_user"}
DB_PASS=${DB_PASS:-"kyc_pass"}
DB_NAME=${DB_NAME:-"kyc_db"}
S3_BUCKET=${S3_BUCKET_NAME:-"digital-kyc-documents-bucket"}
TEMP_RESTORE_DIR="/tmp/kyc-restore"

echo "=== [Disaster Recovery: STARTING RESTORATION FOR BACKUP $BACKUP_TS] ==="

# Create temporary local restore directory
mkdir -p "$TEMP_RESTORE_DIR"

# 1. Download backup files from AWS S3
echo "[1/3] Downloading backups from S3..."
if command -v aws &> /dev/null; then
  aws s3 cp "s3://$S3_BUCKET/backups/db_backup_$BACKUP_TS.sql" "$TEMP_RESTORE_DIR/db_backup.sql"
  aws s3 cp "s3://$S3_BUCKET/backups/uploads_backup_$BACKUP_TS.tar.gz" "$TEMP_RESTORE_DIR/uploads_backup.tar.gz"
else
  echo "[ERROR] AWS CLI not found. Cannot download from S3. Place the files in $TEMP_RESTORE_DIR manually and run this script again."
  exit 1
fi

# 2. Restore MySQL Database
echo "[2/3] Restoring MySQL database: $DB_NAME..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$TEMP_RESTORE_DIR/db_backup.sql"

# 3. Restore files in uploads/ folder
echo "[3/3] Restoring KYC uploads directory..."
tar -xzf "$TEMP_RESTORE_DIR/uploads_backup.tar.gz" -C .

# Cleanup
rm -rf "$TEMP_RESTORE_DIR"
echo "=== [Disaster Recovery: RESTORATION COMPLETE] ==="
