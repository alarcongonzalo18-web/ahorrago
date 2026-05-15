$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bat = Join-Path $Root "actualizar-productos.bat"
$TaskName = "AhorraGo - Actualizar productos"

if (-not (Test-Path $Bat)) {
    Write-Error "No existe $Bat"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $Bat -WorkingDirectory $Root
$Triggers = @(
    New-ScheduledTaskTrigger -Daily -At 06:00
    New-ScheduledTaskTrigger -Daily -At 12:00
    New-ScheduledTaskTrigger -Daily -At 18:00
    New-ScheduledTaskTrigger -Daily -At 00:00
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
    -Description "Actualiza productos AhorraGo 4 veces al dia: 06:00, 12:00, 18:00, 00:00." `
    -Force | Out-Null

Write-Host "Tarea programada ACTIVADA: $TaskName"
Write-Host "Horarios: 06:00, 12:00, 18:00, 00:00"
Write-Host "Para desactivar: .\pausar-actualizacion-productos.ps1"
Write-Host "Para probar ahora: .\actualizar-productos.bat"
