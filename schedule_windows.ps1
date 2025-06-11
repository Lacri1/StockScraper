# Create a scheduled task to run the stock scraper every hour
$action = New-ScheduledTaskAction -Execute "python" -Argument "$PSScriptRoot\main.py" -WorkingDirectory $PSScriptRoot

# Set trigger to run every hour, starting immediately
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Highest -LogonType S4U

# Register the scheduled task
Register-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -TaskName "StockScraper" -Description "Runs stock scraper every hour" -Force

Write-Host "Scheduled task 'StockScraper' has been created to run every hour."
Write-Host "To modify or remove the task, use Task Scheduler (taskschd.msc)"
