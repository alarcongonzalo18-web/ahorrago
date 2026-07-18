import csv
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from filelock import FileLock, Timeout


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BACKUPS = ROOT / "backups"
LOGS = ROOT / "logs"
LOCK = ROOT / "actualizacion_productos.lock"
DB = ROOT / "supercheck.db"
CSV_FINAL = DATA / "productos_supermercados.csv"

RAW_FILES = {
    "Líder": DATA / "lider_real.csv",
    "Jumbo": DATA / "jumbo_real.csv",
    "Unimarc": DATA / "unimarc_real.csv",
}

STEPS = [
    ("Scraper Líder", [sys.executable, "-m", "app.scraper_lider"]),
    ("Scraper Jumbo", [sys.executable, "-m", "app.scraper_jumbo_real"]),
    ("Scraper Unimarc", [sys.executable, "-m", "app.scraper_unimarc"]),
    ("Combinar CSV", [sys.executable, "-m", "app.combinar_supermercados"]),
    ("Reconstruir base", [sys.executable, "-m", "app.reconstruir_base"]),
]


class Logger:
    def __init__(self, path):
        self.file = open(path, "a", encoding="utf-8")

    def write(self, text):
        print(text, flush=True)
        self.file.write(text + "\n")
        self.file.flush()

    def close(self):
        self.file.close()


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def contar_csv(path):
    if not path.exists():
        return 0
    with open(path, newline="", encoding="utf-8-sig") as archivo:
        return sum(1 for _ in csv.DictReader(archivo))


def respaldar_archivo(path, carpeta, logger):
    if not path.exists():
        return None
    destino = carpeta / path.name
    shutil.copy2(path, destino)
    logger.write(f"Backup creado: {destino}")
    return destino


def ejecutar(nombre, comando, logger):
    logger.write("")
    logger.write(f"== {nombre} ==")
    logger.write(" ".join(str(parte) for parte in comando))

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    proceso = subprocess.run(
        comando,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    salida = proceso.stdout.strip()
    if salida:
        logger.write(salida)

    if proceso.returncode != 0:
        raise RuntimeError(f"{nombre} terminó con código {proceso.returncode}")


def validar_raw(logger):
    logger.write("")
    logger.write("== Validación de archivos por supermercado ==")
    for supermercado, path in RAW_FILES.items():
        cantidad = contar_csv(path)
        logger.write(f"{supermercado}: {cantidad} filas")
        if cantidad < 50:
            raise RuntimeError(f"{supermercado} tiene muy pocos productos ({cantidad}). Se detiene la actualización.")


def validar_csv_final(logger):
    logger.write("")
    logger.write("== Validación de CSV final ==")
    cantidad = contar_csv(CSV_FINAL)
    logger.write(f"CSV final: {cantidad} filas")
    if cantidad < 150:
        raise RuntimeError(f"CSV final tiene muy pocos productos ({cantidad}).")

    supermercados = set()
    with open(CSV_FINAL, newline="", encoding="utf-8-sig") as archivo:
        for fila in csv.DictReader(archivo):
            supermercados.add((fila.get("supermercado") or "").strip())

    faltantes = set(RAW_FILES) - supermercados
    if faltantes:
        raise RuntimeError(f"Faltan supermercados en CSV final: {', '.join(sorted(faltantes))}")


def validar_base(logger):
    logger.write("")
    logger.write("== Validación de base ==")
    conn = sqlite3.connect(DB)
    try:
        productos = conn.execute("select count(*) from productos").fetchone()[0]
        precios = conn.execute("select count(*) from precios").fetchone()[0]
    finally:
        conn.close()

    logger.write(f"Productos: {productos}")
    logger.write(f"Precios: {precios}")

    if productos < 50 or precios < 150:
        raise RuntimeError("La base quedó con pocos datos. Se considera actualización fallida.")


def restaurar_db(backup_db, logger):
    if backup_db and backup_db.exists():
        shutil.copy2(backup_db, DB)
        logger.write(f"Base restaurada desde backup: {backup_db}")


def main():
    LOGS.mkdir(exist_ok=True)
    BACKUPS.mkdir(exist_ok=True)
    run_id = timestamp()
    log_path = LOGS / f"actualizacion_productos_{run_id}.log"
    backup_dir = BACKUPS / f"productos_{run_id}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    logger = Logger(log_path)
    backup_db = None
    lock = FileLock(str(LOCK), timeout=0)

    try:
        try:
            lock.acquire()
        except Timeout:
            raise RuntimeError("Ya hay una actualización de productos en curso. Se cancela esta ejecución.")

        logger.write(f"Inicio actualización: {datetime.now().isoformat(timespec='seconds')}")

        backup_db = respaldar_archivo(DB, backup_dir, logger)
        respaldar_archivo(CSV_FINAL, backup_dir, logger)
        for path in RAW_FILES.values():
            respaldar_archivo(path, backup_dir, logger)

        for nombre, comando in STEPS[:3]:
            ejecutar(nombre, comando, logger)

        validar_raw(logger)
        ejecutar(*STEPS[3], logger)
        validar_csv_final(logger)
        ejecutar(*STEPS[4], logger)
        validar_base(logger)

        logger.write("")
        logger.write(f"Actualización completa: {datetime.now().isoformat(timespec='seconds')}")
        logger.write(f"Log: {log_path}")
        return 0
    except Exception as exc:
        logger.write("")
        logger.write(f"ERROR: {exc}")
        restaurar_db(backup_db, logger)
        return 1
    finally:
        if lock.is_locked:
            lock.release()
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
