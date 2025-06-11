#!/bin/bash

# Get the absolute path of the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Create a cron job to run every hour
(crontab -l 2>/dev/null; echo "0 * * * * cd $SCRIPT_DIR && python3 $SCRIPT_DIR/main.py") | crontab -

echo "Cron job has been set up to run every hour."
echo "Current crontab entries:"
crontab -l
