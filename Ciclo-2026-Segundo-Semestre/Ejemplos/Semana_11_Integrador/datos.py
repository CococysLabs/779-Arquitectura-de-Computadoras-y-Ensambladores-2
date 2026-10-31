"""Persistencia SQLite: lecturas únicas, comandos y registro de eventos."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config import DB_PATH, utc_now


@contextmanager
def conexion(db_path=DB_PATH):
    """Abre la base, confirma (commit) o deshace (rollback) y SIEMPRE la cierra.

    Se abre una conexión por operación porque el hilo de MQTT y los hilos de
    Flask acceden a SQLite al mismo tiempo; una conexión compartida no es segura.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path), timeout=10)
    db.row_factory = sqlite3.Row
    try:
        with db:  # commit al terminar, rollback si hubo excepción
            yield db
    finally:
        db.close()


def inicializar(db_path=DB_PATH):
    with conexion(db_path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS lecturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL UNIQUE,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                variable TEXT NOT NULL,
                valor REAL NOT NULL,
                unidad TEXT NOT NULL,
                recibido TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS estados (
                device_id TEXT PRIMARY KEY,
                fan INTEGER NOT NULL,
                modo TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                recibido TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS comandos (
                command_id TEXT PRIMARY KEY,
                modo TEXT NOT NULL,
                fan INTEGER,
                solicitado TEXT NOT NULL,
                confirmado TEXT,
                estado TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tipo TEXT NOT NULL,
                detalle TEXT NOT NULL
            );
        """)


def guardar_lectura(dato, db_path=DB_PATH):
    with conexion(db_path) as db:
        cursor = db.execute("""
            INSERT OR IGNORE INTO lecturas
            (message_id, device_id, timestamp, variable, valor, unidad, recibido)
            VALUES (:message_id, :device_id, :timestamp, :variable, :valor, :unidad, :recibido)
        """, {**dato, "recibido": utc_now()})
        return cursor.rowcount == 1


def guardar_estado(estado, db_path=DB_PATH):
    with conexion(db_path) as db:
        db.execute("""INSERT INTO estados (device_id, fan, modo, timestamp, recibido)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET fan=excluded.fan, modo=excluded.modo,
            timestamp=excluded.timestamp, recibido=excluded.recibido""",
            (estado["device_id"], int(estado["fan"]), estado["modo"], estado["timestamp"], utc_now()))


def guardar_comando(command_id, modo, fan, db_path=DB_PATH):
    with conexion(db_path) as db:
        db.execute("INSERT INTO comandos VALUES (?, ?, ?, ?, NULL, 'pendiente')",
                   (command_id, modo, None if fan is None else int(fan), utc_now()))


def confirmar_comando(command_id, aplicado, db_path=DB_PATH):
    with conexion(db_path) as db:
        cur = db.execute("UPDATE comandos SET estado=?, confirmado=? WHERE command_id=?",
                         ("confirmado" if aplicado else "rechazado", utc_now(), command_id))
        return cur.rowcount == 1


def agregar_evento(tipo, detalle, db_path=DB_PATH):
    with conexion(db_path) as db:
        db.execute("INSERT INTO eventos (timestamp, tipo, detalle) VALUES (?, ?, ?)",
                   (utc_now(), str(tipo)[:60], str(detalle)[:300]))


def filas(sql, args=(), db_path=DB_PATH):
    with conexion(db_path) as db:
        return [dict(r) for r in db.execute(sql, args).fetchall()]


def ultimas_lecturas(limite=50, db_path=DB_PATH):
    r = filas("SELECT * FROM lecturas ORDER BY id DESC LIMIT ?", (limite,), db_path)
    return list(reversed(r))


def ultimo_estado(db_path=DB_PATH):
    r = filas("SELECT * FROM estados ORDER BY recibido DESC LIMIT 1", db_path=db_path)
    if r:
        r[0]["fan"] = bool(r[0]["fan"])
        return r[0]
    return None


def comandos(limite=8, db_path=DB_PATH):
    return filas("SELECT * FROM comandos ORDER BY solicitado DESC LIMIT ?", (limite,), db_path)


def eventos(limite=12, db_path=DB_PATH):
    return filas("SELECT * FROM eventos ORDER BY id DESC LIMIT ?", (limite,), db_path)
