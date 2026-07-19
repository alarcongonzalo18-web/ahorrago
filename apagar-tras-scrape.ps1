# Vigilante de apagado — 18-07-2026
# Espera a que termine la ultima tarea del scrape nocturno (EAN, 03:00, tope 5 h)
# y apaga el equipo. Pensado para la noche previa a migrar al equipo actualizador.

$log = "E:\ahorrago\logs\apagado_$(Get-Date -Format 'yyyyMMdd').log"
function Anotar($msg) { "$(Get-Date -Format 'HH:mm:ss')  $msg" | Out-File $log -Append -Encoding utf8 }

Anotar "vigilante iniciado"
$inicioEsperado = (Get-Date).Date.AddHours(3)   # el EAN dispara a las 03:00

while ($true) {
    Start-Sleep -Seconds 300

    $tareas = Get-ScheduledTask -TaskName "AhorraGo*" |
        Where-Object { $_.TaskName -notlike "*Apagar*" }
    $corriendo = @($tareas | Where-Object State -eq "Running")

    $ean = Get-ScheduledTaskInfo -TaskName "AhorraGo - EAN"
    $eanYaCorrio = $ean.LastRunTime -ge $inicioEsperado

    if ($corriendo.Count -gt 0) {
        Anotar "corriendo: $($corriendo.TaskName -join ', ')"
        continue
    }
    if (-not $eanYaCorrio) {
        Anotar "esperando a que dispare el EAN de las 03:00"
        continue
    }

    Anotar "todo terminado (EAN resultado $($ean.LastTaskResult)); apagando en 2 min"
    shutdown /s /t 120 /c "AhorraGo: scrape nocturno terminado, apagando el equipo"
    break
}
