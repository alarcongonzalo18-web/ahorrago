$Tareas = @(
    "AhorraGo - Actualizar Unimarc",
    "AhorraGo - Actualizar Jumbo",
    "AhorraGo - Actualizar Lider",
    "AhorraGo - EAN (Jumbo y Unimarc)",
    "AhorraGo - Actualizar productos"   # tarea unica antigua, por si quedo dando vueltas
)

$encontradas = 0
foreach ($nombre in $Tareas) {
    $tarea = Get-ScheduledTask -TaskName $nombre -ErrorAction SilentlyContinue
    if ($tarea) {
        Disable-ScheduledTask -TaskName $nombre | Out-Null
        Write-Host "Tarea PAUSADA: $nombre"
        $encontradas++
    }
}

if ($encontradas -eq 0) {
    Write-Host "No hay tareas de AhorraGo registradas."
} else {
    Write-Host ""
    Write-Host "Para reactivar: .\programar-actualizacion-productos.ps1"
}
