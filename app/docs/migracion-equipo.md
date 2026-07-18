# Migrar AhorraGo a otro equipo

> Guía para pasar el pipeline a la máquina que va a quedar siempre encendida.
> Verificá al final con `python -m app.doctor`, que chequea todo esto solo.

## ⚠️ Lo que NO viaja por git

El repo trae el código, la caché de EAN y los docs. **Estos dos hay que copiarlos a mano**:

| Archivo | Por qué importa | Si no lo copiás |
|---|---|---|
| **`supercheck.db`** (~26 MB) | Contiene el **historial de precios**, que es la única tabla que acumula | **Se pierde la serie histórica para siempre.** Los precios se re-scrapean, la historia no se recupera |
| **`.env`** | Tiene `JUMBO_API_KEY` | El scraper de Jumbo falla en la primera corrida |

Los CSV de `data/*_real.csv` sí se pueden dejar: se regeneran en la primera corrida
(~1.5 h). Copiarlos igual ahorra esa espera.

## Pasos

```powershell
# 1. Traer el codigo
git clone https://github.com/alarcongonzalo18-web/ahorrago
cd ahorrago

# 2. Entorno
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 3. Copiar del equipo viejo (lo que no viaja por git)
#    - .env                -> raiz del proyecto
#    - supercheck.db       -> raiz del proyecto   <-- EL HISTORIAL
#    - data\*_real.csv     -> opcional, ahorra la primera corrida

# 4. Verificar que este equipo puede correr todo
.venv\Scripts\python -m app.doctor

# 5. Programar las tareas nocturnas
.\programar-actualizacion-productos.ps1
```

**Chrome** tiene que estar instalado (el scraper de Unimarc usa Selenium; el driver lo baja
Selenium Manager solo).

## Requisitos del equipo

- **IP residencial**: es lo crítico. Los retailers bloquean IPs de datacenter — por eso el
  pipeline **no** puede vivir en un VPS. Ver [camino-a-produccion.md](camino-a-produccion.md).
- **Siempre encendido** (o al menos suspendido, con *temporizadores de reactivación*
  habilitados en Opciones de energía, porque las tareas usan `WakeToRun`).
- Windows con Programador de tareas. En Linux el pipeline corre igual, pero hay que rehacer
  la programación con `cron` en vez de los `.ps1`.

## Después de migrar

1. `python -m app.doctor` → tiene que decir **"Todo en orden"**. Chequea dependencias,
   `.env`, caché de EAN, base, **historial** y los contratos reales de las 4 cadenas
   (incluida la auth de Jumbo).
2. Probar una corrida corta a mano: `.\actualizar-productos.bat --solo tottus`
   (Tottus es la más rápida).
3. A la mañana siguiente: `python -m app.estado_pipeline` → tiene que mostrar las tareas en OK.
4. **Apagar las tareas en el equipo viejo** con `.\pausar-actualizacion-productos.ps1`, o los
   dos equipos van a scrapear en paralelo contra los mismos retailers (más riesgo de bloqueo).

## Trabajar en un equipo y actualizar en otro

Es el esquema recomendado (y el mismo que hará falta al desplegar): **este PC para
desarrollar, el otro sólo para correr el pipeline**.

### Regla de oro: el actualizador es el dueño de los datos

| | Equipo de trabajo | Equipo actualizador |
|---|---|---|
| Código | se edita acá | llega por `git pull` |
| Tareas programadas | **pausadas** | activas |
| `supercheck.db` | copia para probar, **descartable** | **la buena** (acumula el historial) |
| `data/ean_cache.json` | vía git | vía git |

El **historial de precios sólo acumula donde corre el pipeline**. Por eso la base del
actualizador es la autoritativa y la de acá es una foto para desarrollar.

### ⚠️ La dirección de la copia importa

Copiar la base **actualizador → trabajo**: bien, cuando quieras probar con datos frescos.

Copiar **trabajo → actualizador**: **NUNCA**. Pisarías la base buena con una vieja y
**borrarías los días de historial** acumulados. La historia no se puede re-scrapear.

### Flujo del día a día

```powershell
# Acá (trabajo): programar como siempre
git add . ; git commit ; git push
.\pausar-actualizacion-productos.ps1     # una sola vez, para no scrapear en paralelo

# En el actualizador: tomar los cambios de codigo
git pull

# Cuando quieras probar acá con datos frescos: traer la base del actualizador
#   copiar supercheck.db  (actualizador -> este equipo)
```

**No corras el pipeline en los dos equipos**: golpearían a los mismos retailers en paralelo,
duplicando el riesgo de bloqueo justo cuando Jumbo ya nos throttlea.

Para desarrollar no hacen falta datos frescos: una base de hace días alcanza. Traé la del
actualizador sólo cuando quieras ver precios reales del día.

## Chequeo de que no se perdió nada

```powershell
.venv\Scripts\python -m app.doctor
```

Que el historial figure con **puntos y días > 0**. Si dice "vacío", la base que copiaste no era
la correcta: volvé a traer `supercheck.db` del equipo viejo antes de correr el pipeline (la
primera corrida no borra el historial, pero tampoco lo recupera).
