#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Remove any existing entries for this script to avoid duplicates
crontab -l | grep -v "$SCRIPT_DIR/main.py" | crontab -

# Add a new cron job to run every hour
(crontab -l 2>/dev/null; echo "0 * * * * cd $SCRIPT_DIR && python3 main.py") | crontab -

# Run immediately for the first time
cd "$SCRIPT_DIR" && python3 main.py &

echo "Cron job has been set up to run at the start of every hour."
echo "Current crontab entries:"
crontab -l
