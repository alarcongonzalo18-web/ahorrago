$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bat = Join-Path $Root "actualizar-productos.bat"
$TaskName = "AhorraGo - Actualizar productos"

if (-not (Test-Path $Bat)) {
    Write-Error "No existe $Bat"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $Bat -WorkingDirectory $Root
# UNA corrida diaria a las 03:00, la ventana de menor trafico tanto para nuestra
# app como para los retailers.
#
# Historia de este horario: eran 4 al dia (06/12/18/00) -> se bajo a 2 (06/18)
# porque una corrida tarda ~1.5 h y 4 eran ~6 h diarias de scraping -> ahora 1 a
# las 03:00. Motivos:
#  - 18:00 era hora punta del e-commerce de supermercado: les sumabamos carga
#    cuando mas ocupados estaban, y es cuando mas probable es que throttleen
#    (Jumbo ya nos corto a los ~344 requests en un backfill diurno).
#  - Los precios de supermercado cambian a lo sumo una vez al dia; correr mas
#    seguido no da frescura real, solo mas riesgo de bloqueo.
#  - Menos corridas y mas limpias = datos mas completos (menos cortes del guard).
# Termina ~04:30, asi que el badge de frescura siempre dice "hoy".
$Triggers = @(
    New-ScheduledTaskTrigger -Daily -At 03:00
)
# WakeToRun: despierta el equipo si esta suspendido (no sirve si esta apagado del
#   todo; ver la nota de "equipo apagado" en app/docs/estado-y-handoff.md).
# StartWhenAvailable: si igual se salto el horario (equipo apagado), corre apenas
#   se pueda al prenderlo, para no quedarse un dia entero sin actualizar.
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Triggers `
    -Settings $Settings `
    -Description "Actualiza productos AhorraGo 1 vez al dia a las 03:00 (ventana de menor trafico)." `
    -Force | Out-Null

Write-Host "Tarea programada ACTIVADA: $TaskName"
Write-Host "Horario: 03:00 diario (ventana de menor trafico)"
Write-Host "Para desactivar: .\pausar-actualizacion-productos.ps1"
Write-Host "Para probar ahora: .\actualizar-productos.bat"
