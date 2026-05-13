$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bat = Join-Path $Root "actualizar-productos.bat"
$TaskName = "AhorraGo - Actualizar productos"

if (-not (Test-Path $Bat)) {
    Write-Error "No existe $Bat"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $Bat -WorkingDirectory $Root
$Triggers = @(
    New-ScheduledTaskTrigger -Daily -At 07:00
    New-ScheduledTaskTrigger -Daily -At 14:00
    New-ScheduledTaskTrigger -Daily -At 21:00
)
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Triggers `
    -Settings $Settings `
    -Description "Actualiza productos AhorraGo 3 veces al día con backup, logs y validación." `
    -Force | Out-Null

Write-Host "Tarea programada creada: $TaskName"
Write-Host "Horarios: 07:00, 14:00, 21:00"
Write-Host "Para probar ahora: .\actualizar-productos.bat"
