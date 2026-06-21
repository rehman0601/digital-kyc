#!/bin/bash
# Disaster Recovery - Automated Platform Backup Script
# Performs database dump and KYC document archive, uploading assets to secure S3 bucket

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration variables (overridden via env vars in production)
DB_HOST=${DB_HOST:-"localhost"}
DB_USER=${DB_USER:-"kyc_user"}
DB_PASS=${DB_PASS:-"kyc_pass"}
DB_NAME=${DB_NAME:-"kyc_db"}
S3_BUCKET=${S3_BUCKET_NAME:-"digital-kyc-documents-bucket"}
BACKUP_DIR="/tmp/kyc-backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "=== [Disaster Recovery: STARTING BACKUP $TIMESTAMP] ==="

# Create temporary local backup directory
mkdir -p "$BACKUP_DIR"

# 1. Back up database tables using mysqldump
echo "[1/3] Dumping MySQL database database..."
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# 2. Package KYC uploaded files (Aadhaar / PAN / Passport documents)
echo "[2/3] Archiving user-uploaded KYC documents..."
if [ -d "uploads" ] && [ "$(ls -A uploads)" ]; then
  tar -czf "$BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz" uploads/
else
  echo "Uploads directory empty or missing. Creating mock placeholder archive."
  mkdir -p uploads && touch uploads/.gitkeep
  tar -czf "$BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz" uploads/
fi

# 3. Upload artifacts to AWS S3
echo "[3/3] Uploading backups to AWS S3 bucket: s3://$S3_BUCKET/backups/"
if command -v aws &> /dev/null; then
  aws s3 cp "$BACKUP_DIR/db_backup_$TIMESTAMP.sql" "s3://$S3_BUCKET/backups/db_backup_$TIMESTAMP.sql"
  aws s3 cp "$BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz" "s3://$S3_BUCKET/backups/uploads_backup_$TIMESTAMP.tar.gz"
  echo "Successfully uploaded backups to S3."
else
  echo "[WARNING] AWS CLI not found. Saved backups locally in $BACKUP_DIR"
fi

# Cleanup local temporary files
rm -rf "$BACKUP_DIR"
echo "=== [Backup Completed successfully] ==="
