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

## Chequeo de que no se perdió nada

```powershell
.venv\Scripts\python -m app.doctor
```

Que el historial figure con **puntos y días > 0**. Si dice "vacío", la base que copiaste no era
la correcta: volvé a traer `supercheck.db` del equipo viejo antes de correr el pipeline (la
primera corrida no borra el historial, pero tampoco lo recupera).
