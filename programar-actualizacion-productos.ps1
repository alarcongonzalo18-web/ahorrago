$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bat = Join-Path $Root "actualizar-productos.bat"

if (-not (Test-Path $Bat)) {
    Write-Error "No existe $Bat"
    exit 1
}

# Horarios ESCALONADOS: una tarea por cadena, en vez de una corrida unica de ~1.5 h.
#
# Por que escalonado:
#  - Reparte la carga sobre los retailers en vez de 1.5 h de golpe.
#  - Si una cadena falla, no arrastra a las otras (antes un scraper caido cortaba todo).
#  - Corridas mas cortas = menos chance de topar la cuota (Jumbo corta a los ~344 requests).
#
# Por que estos horarios:
#  - Lider y Jumbo son los de mas publico -> van en la ventana mas profunda de bajo trafico.
#  - Unimarc tiene menos publico -> tolera el horario mas temprano.
#  - Cada tarea corre su scraper + combinar + reconstruir, asi la base queda publicada
#    despues de cada cadena (no hay que esperar a que terminen las tres).
#
# El espaciado (1.5 h) es CONSERVADOR hasta tener duraciones reales: el log ahora
# mide cada paso ("-- Scraper X: N min --"). Con esos numeros se puede ajustar.
# Ojo: si una corrida se pasa de su ventana, la siguiente se saltea por el lock
# (MultipleInstances IgnoreNew) y se recupera con StartWhenAvailable.
$Tareas = @(
    @{ Nombre = "AhorraGo - Actualizar Unimarc"; Cadena = "unimarc"; Hora = "22:30" }
    @{ Nombre = "AhorraGo - Actualizar Jumbo";   Cadena = "jumbo";   Hora = "00:00" }
    @{ Nombre = "AhorraGo - Actualizar Lider";   Cadena = "lider";   Hora = "02:00" }
)

# Tarea de EAN, DESPUES de los scrapes (03:00): asi trabaja sobre los CSV recien
# actualizados y tambien captura los productos nuevos de la noche.
# Es incremental: cada noche consulta solo los slugs que falten, drena lo que la
# cuota de Jumbo permita (~344 por ventana) y retoma donde quedo. Con el tiempo el
# backlog se agota solo y despues queda como mantenimiento de productos nuevos.
# Corre backfill + publica a la base (--sin-scrape), sin pedirle nada extra a los
# retailers en el segundo paso.
$BatEan = Join-Path $Root "backfill-ean.bat"
$TareaEan = @{ Nombre = "AhorraGo - EAN (Jumbo y Unimarc)"; Args = "all"; Hora = "03:00" }

# WakeToRun: despierta el equipo si esta suspendido (no sirve si esta apagado del
#   todo; ver la nota de "equipo apagado" en app/docs/estado-y-handoff.md).
# StartWhenAvailable: si igual se salto el horario, corre apenas se pueda.
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3)

foreach ($t in $Tareas) {
    $Action = New-ScheduledTaskAction -Execute $Bat -Argument "--solo $($t.Cadena)" -WorkingDirectory $Root
    $Trigger = New-ScheduledTaskTrigger -Daily -At $t.Hora

    Register-ScheduledTask `
        -TaskName $t.Nombre `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Actualiza $($t.Cadena) en AhorraGo, diario a las $($t.Hora)." `
        -Force | Out-Null

    Write-Host "Tarea ACTIVADA: $($t.Nombre)  ->  $($t.Hora)  (--solo $($t.Cadena))"
}

if (Test-Path $BatEan) {
    $AccionEan = New-ScheduledTaskAction -Execute $BatEan -Argument $TareaEan.Args -WorkingDirectory $Root
    $TriggerEan = New-ScheduledTaskTrigger -Daily -At $TareaEan.Hora
    # Ventana mas larga: el backfill de Jumbo grindea contra su cuota.
    $SettingsEan = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -StartWhenAvailable `
        -WakeToRun `
        -ExecutionTimeLimit (New-TimeSpan -Hours 5)

    Register-ScheduledTask `
        -TaskName $TareaEan.Nombre `
        -Action $AccionEan `
        -Trigger $TriggerEan `
        -Settings $SettingsEan `
        -Description "Puebla la cache de EAN (incremental) y publica a la base. Diario $($TareaEan.Hora)." `
        -Force | Out-Null

    Write-Host "Tarea ACTIVADA: $($TareaEan.Nombre)  ->  $($TareaEan.Hora)  (backfill $($TareaEan.Args) + publicar)"
}

# La tarea unica anterior ya no aplica: se elimina para que no corra en paralelo.
$vieja = Get-ScheduledTask -TaskName "AhorraGo - Actualizar productos" -ErrorAction SilentlyContinue
if ($vieja) {
    Unregister-ScheduledTask -TaskName "AhorraGo - Actualizar productos" -Confirm:$false
    Write-Host "Tarea antigua unificada eliminada (quedaba duplicando el trabajo)."
}

Write-Host ""
Write-Host "Para pausar todas: .\pausar-actualizacion-productos.ps1"
Write-Host "Para probar una a mano: .\actualizar-productos.bat --solo unimarc"
