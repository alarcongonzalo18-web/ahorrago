$TaskName = "AhorraGo - Actualizar productos"

$tarea = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $tarea) {
    Write-Host "La tarea no existe o ya fue eliminada."
    exit 0
}

Disable-ScheduledTask -TaskName $TaskName | Out-Null
Write-Host "Tarea PAUSADA: $TaskName"
Write-Host "Para reactivar: .\programar-actualizacion-productos.ps1"
