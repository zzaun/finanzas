"""Creación de tablas y migraciones de la base de datos."""
from __future__ import annotations

from finanzas.datos.base_datos import BaseDatos
from finanzas.excepciones import ErrorFinanzas

ESQUEMA_V1 = """
CREATE TABLE categorias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    anio        INTEGER NOT NULL,
    nombre      TEXT    NOT NULL COLLATE NOCASE,
    tipo        TEXT    NOT NULL CHECK (tipo IN ('ingreso', 'gasto', 'ahorro')),
    es_hormiga  INTEGER NOT NULL DEFAULT 0 CHECK (es_hormiga IN (0, 1)),
    activa      INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0, 1)),
    UNIQUE (anio, nombre, tipo)
);

CREATE TABLE movimientos (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion       TEXT    NOT NULL,
    monto             INTEGER NOT NULL CHECK (monto > 0),
    categoria_id      INTEGER NOT NULL REFERENCES categorias (id),
    fecha_movimiento  TEXT,
    fecha_captura     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    estado            TEXT    NOT NULL DEFAULT 'real' CHECK (estado IN ('real', 'pendiente')),
    es_anterior       INTEGER NOT NULL DEFAULT 0 CHECK (es_anterior IN (0, 1)),
    notas             TEXT,
    CHECK (estado = 'pendiente' OR fecha_movimiento IS NOT NULL)
);
CREATE INDEX idx_mov_fecha     ON movimientos (fecha_movimiento);
CREATE INDEX idx_mov_categoria ON movimientos (categoria_id);
CREATE INDEX idx_mov_estado    ON movimientos (estado);

CREATE TABLE presupuesto_mensual (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    anio                INTEGER NOT NULL,
    mes                 INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    ingresos_planeados  INTEGER NOT NULL DEFAULT 0,
    gastos_planeados    INTEGER NOT NULL DEFAULT 0,
    ahorro_planeado     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (anio, mes)
);

CREATE TABLE configuracion (
    clave  TEXT PRIMARY KEY,
    valor  TEXT NOT NULL
);

CREATE VIEW v_movimientos_detalle AS
SELECT m.id, m.descripcion, m.monto, m.categoria_id,
       c.nombre AS categoria, c.tipo AS tipo, c.es_hormiga AS es_hormiga,
       c.anio AS anio_categoria,
       m.fecha_movimiento, m.fecha_captura, m.estado, m.es_anterior, m.notas
FROM movimientos m
JOIN categorias c ON c.id = m.categoria_id;

CREATE VIEW v_resumen_mensual AS
SELECT substr(fecha_movimiento, 1, 4)                   AS anio,
       CAST(substr(fecha_movimiento, 6, 2) AS INTEGER)  AS mes,
       SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS ingresos,
       SUM(CASE WHEN tipo = 'gasto'   THEN monto ELSE 0 END) AS gastos,
       SUM(CASE WHEN tipo = 'ahorro'  THEN monto ELSE 0 END) AS ahorro
FROM v_movimientos_detalle
WHERE estado = 'real' AND fecha_movimiento IS NOT NULL
GROUP BY 1, 2;
"""

CONFIGURACION_INICIAL = {"inicio_semana": "lunes", "moneda": "MXN"}


class Esquema:
    """Crea la base la primera vez y la actualiza cuando cambia el diseño."""

    VERSION_ACTUAL = 1
    # Para agregar cambios futuros: subir VERSION_ACTUAL y añadir aquí el
    # script, por ejemplo  {2: "ALTER TABLE movimientos ADD COLUMN etiqueta TEXT;"}
    MIGRACIONES: dict[int, str] = {}

    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def version(self) -> int:
        return self.bd.conexion.execute("PRAGMA user_version").fetchone()[0]

    def _fijar_version(self, version: int) -> None:
        self.bd.conexion.execute(f"PRAGMA user_version = {int(version)}")

    def aplicar(self) -> None:
        actual = self.version()
        if actual > self.VERSION_ACTUAL:
            raise ErrorFinanzas(
                "La base de datos es de una versión más nueva que este programa."
            )
        if actual == 0:
            self.bd.conexion.executescript(ESQUEMA_V1)
            self._fijar_version(1)
            actual = 1
        for destino in range(actual + 1, self.VERSION_ACTUAL + 1):
            self.bd.conexion.executescript(self.MIGRACIONES[destino])
            self._fijar_version(destino)
        for clave, valor in CONFIGURACION_INICIAL.items():
            self.bd.ejecutar(
                "INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)",
                (clave, valor),
            )
