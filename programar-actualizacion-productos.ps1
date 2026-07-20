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
#  - Unimarc y Tottus tienen menos publico -> toleran los horarios mas tempranos.
#  - Tottus va primero ademas porque es el mas rapido (urllib puro, sin navegador).
#  - Cada tarea corre su scraper + combinar + reconstruir, asi la base queda publicada
#    despues de cada cadena (no hay que esperar a que terminen las tres).
#
# El espaciado (1.5 h) es CONSERVADOR hasta tener duraciones reales: el log ahora
# mide cada paso ("-- Scraper X: N min --"). Con esos numeros se puede ajustar.
# Ojo: si una corrida se pasa de su ventana, la siguiente se saltea por el lock
# (MultipleInstances IgnoreNew) y se recupera con StartWhenAvailable.
# Orden y horarios: cada cadena corre sola (lock global -> un scraper a la vez).
# Lider va a la 01:00 (no a las 02:00) para tener ~2.5h de runway antes del EAN
# (03:30) y poder ser paciente con el throttling 429 de super.lider.cl sin
# truncar categorias ni pasarse de su ventana. Jumbo NO se mueve de las 00:00:
# su colchon hasta el backfill EAN (00:00 -> 03:30 = 3.5h) es lo que protege su
# cuota de API (~344 req/ventana); achicarlo reintroduciria el problema de cuota.
$Tareas = @(
    @{ Nombre = "AhorraGo - Actualizar Tottus";  Cadena = "tottus";  Hora = "21:00" }
    @{ Nombre = "AhorraGo - Actualizar Unimarc"; Cadena = "unimarc"; Hora = "22:30" }
    @{ Nombre = "AhorraGo - Actualizar Jumbo";   Cadena = "jumbo";   Hora = "00:00" }
    @{ Nombre = "AhorraGo - Actualizar Lider";   Cadena = "lider";   Hora = "01:00" }
)

# Tarea de EAN, DESPUES de los scrapes (03:00): asi trabaja sobre los CSV recien
# actualizados y tambien captura los productos nuevos de la noche.
# Es incremental: cada noche consulta solo los slugs que falten, drena lo que la
# cuota de Jumbo permita (~344 por ventana) y retoma donde quedo. Con el tiempo el
# backlog se agota solo y despues queda como mantenimiento de productos nuevos.
# Corre backfill + publica a la base (--sin-scrape), sin pedirle nada extra a los
# retailers en el segundo paso.
$BatEan = Join-Path $Root "backfill-ean.bat"
# 03:30 (antes 03:00): media hora mas para que Lider (ahora 01:00) tenga runway
# de sobra sin chocar el lock con el EAN. Mantiene 3.5h de colchon tras Jumbo.
$TareaEan = @{ Nombre = "AhorraGo - EAN"; Args = "all"; Hora = "03:30" }

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

# Vigilante de suspension: arranca ANTES del primer scrape (20:55) y se queda
# esperando a que termine todo el proceso (los 4 scrapes + el EAN) para suspender
# el equipo. Se suspende, no se apaga, para que WakeToRun pueda despertarlo la
# noche siguiente. Ver suspender-tras-scrape.ps1.
$ScriptSuspender = Join-Path $Root "suspender-tras-scrape.ps1"
if (Test-Path $ScriptSuspender) {
    $AccionSuspender = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptSuspender`"" `
        -WorkingDirectory $Root
    $TriggerSuspender = New-ScheduledTaskTrigger -Daily -At "20:55"
    # Ventana larga: tiene que sobrevivir toda la noche hasta que termine el EAN
    # (que topa a las 5 h). WakeToRun para despertar el equipo a las 20:55.
    $SettingsSuspender = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -StartWhenAvailable `
        -WakeToRun `
        -ExecutionTimeLimit (New-TimeSpan -Hours 9)

    Register-ScheduledTask `
        -TaskName "AhorraGo - Suspender" `
        -Action $AccionSuspender `
        -Trigger $TriggerSuspender `
        -Settings $SettingsSuspender `
        -Description "Espera a que termine todo el proceso nocturno y suspende el equipo. Diario 20:55." `
        -Force | Out-Null

    Write-Host "Tarea ACTIVADA: AhorraGo - Suspender  ->  20:55  (suspende al terminar todo el proceso)"
}

# La tarea unica anterior ya no aplica: se elimina para que no corra en paralelo.
foreach ($obsoleta in @("AhorraGo - Actualizar productos", "AhorraGo - EAN (Jumbo y Unimarc)")) {
    if (Get-ScheduledTask -TaskName $obsoleta -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $obsoleta -Confirm:$false
        Write-Host "Tarea obsoleta eliminada: $obsoleta"
    }
}

Write-Host ""
Write-Host "Para pausar todas: .\pausar-actualizacion-productos.ps1"
Write-Host "Para probar una a mano: .\actualizar-productos.bat --solo unimarc"
