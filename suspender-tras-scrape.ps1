# Vigilante de suspension — 19-07-2026
# Espera a que termine TODO el proceso nocturno (los 4 scrapes + el EAN de las
# 03:00) y suspende el equipo. Reemplaza a apagar-tras-scrape.ps1 (que APAGABA y
# tenia ruta fija del equipo viejo): se suspende, no se apaga, para que WakeToRun
# pueda despertar el equipo para el scrape de la noche siguiente. Un apagado total
# rompe esa cadena; la suspension no.
#
# Lo dispara la tarea "AhorraGo - Suspender" (20:55, antes del primer scrape),
# que corre este script y se queda vigilando hasta que todo termina.

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$log = Join-Path $LogDir "suspension_$(Get-Date -Format 'yyyyMMdd').log"
function Anotar($msg) { "$(Get-Date -Format 'HH:mm:ss')  $msg" | Out-File $log -Append -Encoding utf8 }

Anotar "vigilante de suspension iniciado"
# Umbral "ya corrio el ciclo de hoy". Se deja en 03:00 a proposito como cota
# INFERIOR aunque el EAN ahora dispare 03:30: cualquier LastRunTime de hoy (>=03:30)
# lo supera, y evita falsos negativos por jitter del scheduler. No suspende entre
# 03:00 y 03:30 porque el EAN de hoy aun no marco su LastRunTime.
$inicioEsperado = (Get-Date).Date.AddHours(3)

while ($true) {
    Start-Sleep -Seconds 300

    # Todas las tareas del pipeline menos esta misma (para no esperarse a si misma).
    $tareas = Get-ScheduledTask -TaskName "AhorraGo*" |
        Where-Object { $_.TaskName -notlike "*Suspender*" }
    $corriendo = @($tareas | Where-Object State -eq "Running")

    $ean = Get-ScheduledTaskInfo -TaskName "AhorraGo - EAN"
    $eanYaCorrio = $ean.LastRunTime -ge $inicioEsperado

    if ($corriendo.Count -gt 0) {
        Anotar "corriendo: $($corriendo.TaskName -join ', ')"
        continue
    }
    if (-not $eanYaCorrio) {
        Anotar "esperando a que dispare el EAN de las 03:30"
        continue
    }

    Anotar "todo terminado (EAN resultado $($ean.LastTaskResult)); suspendiendo el equipo"
    # SetSuspendState(Hibernate=0, ForceCritical=1, DisableWakeEvent=0):
    #  - Hibernate 0  -> suspender (si el sistema tiene hibernacion activa puede
    #                    hibernar igual; WakeToRun despierta de ambos, S3 e hib.).
    #  - DisableWakeEvent 0 -> deja los temporizadores de reactivacion armados,
    #                    asi las tareas de la noche siguiente pueden despertar el PC.
    rundll32.exe powrprof.dll,SetSuspendState 0,1,0
    break
}
