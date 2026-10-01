"""Copias de seguridad de la base de datos."""
from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from pathlib import Path

from finanzas.datos.base_datos import BaseDatos
from finanzas.datos.esquema import Esquema
from finanzas.excepciones import ErrorFinanzas
from finanzas.rutas import Rutas


class GestorRespaldos:
    """Crea, lista y restaura copias de la base usando la API de respaldo de SQLite."""

    PREFIJO = "finanzas_"

    def __init__(self, bd: BaseDatos, rutas: Rutas) -> None:
        self.bd = bd
        self.rutas = rutas

    def crear(self) -> Path:
        self.rutas.respaldos.mkdir(parents=True, exist_ok=True)
        destino = self.rutas.respaldos / f"{self.PREFIJO}{datetime.now():%Y%m%d_%H%M%S}.db"
        copia = sqlite3.connect(destino)
        try:
            self.bd.conexion.backup(copia)
        finally:
            copia.close()
        return destino

    def listar(self) -> list[Path]:
        """Respaldos existentes, del más reciente al más antiguo."""
        if not self.rutas.respaldos.exists():
            return []
        return sorted(self.rutas.respaldos.glob(f"{self.PREFIJO}*.db"), reverse=True)

    def limpiar(self, conservar: int = 15) -> int:
        """Borra los respaldos más viejos y deja los ``conservar`` más recientes."""
        sobrantes = self.listar()[conservar:]
        for ruta in sobrantes:
            ruta.unlink(missing_ok=True)
        return len(sobrantes)

    def respaldo_automatico(self, horas: float = 24, conservar: int = 15) -> Path | None:
        """Crea un respaldo si el último tiene más de ``horas`` de antigüedad."""
        existentes = self.listar()
        if existentes and (time.time() - existentes[0].stat().st_mtime) < horas * 3600:
            return None
        ruta = self.crear()
        self.limpiar(conservar)
        return ruta

    def restaurar(self, ruta: Path | str) -> None:
        """Reemplaza los datos actuales por los de un respaldo (antes guarda una copia)."""
        ruta = Path(ruta)
        if not ruta.is_file():
            raise ErrorFinanzas("El archivo de respaldo no existe.")
        try:
            origen = sqlite3.connect(ruta)
            origen.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        except sqlite3.DatabaseError as error:
            raise ErrorFinanzas("El archivo no es una base de datos válida.") from error
        try:
            self.crear()
            origen.backup(self.bd.conexion)
        finally:
            origen.close()
        Esquema(self.bd).aplicar()
