#!/bin/bash
# Setup automated backups with cron
#
# Usage: ./scripts/setup_cron.sh

set -e

echo "Setting up automated cloud backups with cron..."
echo ""

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Add cron jobs (avoid duplicates)
(
    crontab -l 2>/dev/null | grep -v "backup_to_cloud.py" | grep -v "apply-retention"
    echo "# Peak Trade Cloud Backup - Daily at 2 AM"
    echo "0 2 * * * cd $PROJECT_DIR && python3 scripts/backup_to_cloud.py >> logs/backup.log 2>&1"
    echo ""
    echo "# Peak Trade Cloud Backup - Weekly retention cleanup on Sundays at 3 AM"
    echo "0 3 * * 0 cd $PROJECT_DIR && python3 scripts/backup_to_cloud.py --apply-retention >> logs/backup.log 2>&1"
) | crontab -

echo "✅ Cron jobs setup completed:"
echo ""
echo "  Daily backup:     Every day at 2:00 AM"
echo "  Retention cleanup: Every Sunday at 3:00 AM"
echo ""
echo "Logs will be written to: $PROJECT_DIR/logs/backup.log"
echo ""
echo "To view current cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove cron jobs:"
echo "  crontab -e  (then delete the Peak Trade lines)"
echo ""
