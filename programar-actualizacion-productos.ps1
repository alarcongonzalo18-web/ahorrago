$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bat = Join-Path $Root "actualizar-productos.bat"
$TaskName = "AhorraGo - Actualizar productos"

if (-not (Test-Path $Bat)) {
    Write-Error "No existe $Bat"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $Bat -WorkingDirectory $Root
# 2 veces al dia. Antes eran 4 (06/12/18/00), pero una corrida completa tarda
# ~1.5 h: 4 al dia son ~6 h diarias de scraping sobre los retailers, lo que
# dispara throttling (y el guard anti-regresion termina bloqueando la
# actualizacion). Los precios de supermercado no cambian tantas veces al dia.
$Triggers = @(
    New-ScheduledTaskTrigger -Daily -At 06:00
    New-ScheduledTaskTrigger -Daily -At 18:00
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
    -Description "Actualiza productos AhorraGo 2 veces al dia: 06:00 y 18:00." `
    -Force | Out-Null

Write-Host "Tarea programada ACTIVADA: $TaskName"
Write-Host "Horarios: 06:00 y 18:00"
Write-Host "Para desactivar: .\pausar-actualizacion-productos.ps1"
Write-Host "Para probar ahora: .\actualizar-productos.bat"
