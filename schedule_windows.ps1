# Python 실행 파일 경로 가져오기
$pythonPath = (Get-Command python).Source
if (-not $pythonPath) {
    Write-Error "Python을 찾을 수 없습니다. Python이 설치되어 있고 PATH에 추가되었는지 확인해주세요."
    exit 1
}

# 작업 실행 설정
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "$PSScriptRoot\main.py" -WorkingDirectory $PSScriptRoot

# 매시간 반복 실행 트리거 설정 (1년 동안 유효)
$startTime = Get-Date
$endTime = $startTime.AddYears(1)  # 1년 후까지 실행
$trigger = New-ScheduledTaskTrigger -Once -At $startTime -RepetitionInterval (New-TimeSpan -Hours 1) -End $endTime

# 작업 보안 주체 설정 (최고 권한으로 실행)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Highest -LogonType S4U

# 기존 작업이 있으면 제거
$existingTask = Get-ScheduledTask -TaskName "StockScraper" -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName "StockScraper" -Confirm:$false
}

# 작업 스케줄러에 등록
Register-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -TaskName "StockScraper" -Description "주식 스크래퍼를 매시간 실행합니다." -Force

# 작업이 성공적으로 등록되었는지 확인
$task = Get-ScheduledTask -TaskName "StockScraper" -ErrorAction SilentlyContinue
if ($task) {
    Write-Host "성공: 'StockScraper' 작업이 성공적으로 등록되었습니다." -ForegroundColor Green
    Write-Host "Python 경로: $pythonPath"
    Write-Host "작업 디렉토리: $PSScriptRoot"
    Write-Host "`n작업 정보 확인:"
    Get-ScheduledTask -TaskName "StockScraper" | Select-Object TaskName, State, LastRunTime, NextRunTime
    Write-Host "`n작업을 수정하거나 삭제하려면 다음 명령어를 사용하세요:"
    Write-Host "작업 스케줄러에서 수정: taskschd.msc"
    Write-Host "작업 삭제: Unregister-ScheduledTask -TaskName 'StockScraper' -Confirm:`$false"
} else {
    Write-Error "작업 등록에 실패했습니다. 관리자 권한으로 실행해보세요."
}
