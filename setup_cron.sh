#!/bin/bash
# Setup script for weekly cron job
# This script helps set up the cron job to update the knowledge base weekly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)
CRON_LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$CRON_LOG_DIR"

# Cron job runs every Sunday at 2 AM
# Format: minute hour day month weekday command
CRON_SCHEDULE="0 2 * * 0"

# Full command to run
CRON_COMMAND="cd $SCRIPT_DIR && $PYTHON_PATH $SCRIPT_DIR/update_knowledge_base.py >> $CRON_LOG_DIR/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "update_knowledge_base.py"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "update_knowledge_base"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing job
        crontab -l 2>/dev/null | grep -v "update_knowledge_base.py" | crontab -
        # Add new job
        (crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_COMMAND") | crontab -
        echo "✅ Cron job updated!"
    else
        echo "Cancelled."
        exit 0
    fi
else
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_COMMAND") | crontab -
    echo "✅ Cron job added successfully!"
fi

echo ""
echo "Cron job details:"
echo "  Schedule: Every Sunday at 2:00 AM"
echo "  Command: $CRON_COMMAND"
echo "  Logs: $CRON_LOG_DIR/cron.log"
echo ""
echo "To view your cron jobs: crontab -l"
echo "To edit cron jobs: crontab -e"
echo "To remove this cron job: crontab -e (then delete the line)"
echo ""
echo "To test the update script manually:"
echo "  cd $SCRIPT_DIR && $PYTHON_PATH update_knowledge_base.py"

