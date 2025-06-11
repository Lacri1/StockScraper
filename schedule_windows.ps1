# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $scriptDir ".venv\Scripts\python.exe"
$scriptPath = Join-Path $scriptDir "main.py"

# Create a scheduled task action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory $scriptDir

# Create a trigger that runs every hour
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)

# Register the scheduled task
$taskName = "StockScraperHourly"
$description = "Runs the StockScraper script every hour"

# Remove the task if it already exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Register the new task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description $description -RunLevel Highest -Force

# Run the script immediately for the first time
Start-Process -NoNewWindow -FilePath $pythonPath -ArgumentList $scriptPath -WorkingDirectory $scriptDir

Write-Host "Scheduled task '$taskName' has been created to run every hour."
Write-Host "Current scheduled tasks:"
Get-ScheduledTask -TaskName $taskName
