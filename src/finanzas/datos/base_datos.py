"""Conexión a SQLite y manejo de transacciones."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence


class BaseDatos:
    """Abre el archivo SQLite y ofrece lo básico para consultarlo.

    Es la única clase que conoce el módulo ``sqlite3`` de cerca; los
    repositorios le piden consultas y ella se encarga del resto.
    """

    def __init__(self, ruta: Path | str = ":memory:") -> None:
        self.ruta = str(ruta)
        self._con: sqlite3.Connection | None = None
        self._nivel = 0  # profundidad de transacciones anidadas

    def conectar(self) -> sqlite3.Connection:
        if self._con is None:
            con = sqlite3.connect(self.ruta)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys = ON")
            if self.ruta != ":memory:":
                con.execute("PRAGMA journal_mode = WAL")
            self._con = con
        return self._con

    @property
    def conexion(self) -> sqlite3.Connection:
        return self.conectar()

    @contextmanager
    def transaccion(self) -> Iterator[sqlite3.Connection]:
        """Agrupa varias operaciones: o se guardan todas o ninguna."""
        con = self.conexion
        self._nivel += 1
        try:
            yield con
        except BaseException:
            self._nivel -= 1
            if self._nivel == 0:
                con.rollback()
            raise
        else:
            self._nivel -= 1
            if self._nivel == 0:
                con.commit()

    def ejecutar(self, sql: str, parametros: Sequence[Any] = ()) -> sqlite3.Cursor:
        """Ejecuta una instrucción; guarda al terminar si no hay transacción."""
        con = self.conexion
        try:
            cursor = con.execute(sql, parametros)
        except BaseException:
            if self._nivel == 0:
                con.rollback()
            raise
        if self._nivel == 0:
            con.commit()
        return cursor

    def consultar(self, sql: str, parametros: Sequence[Any] = ()) -> list[sqlite3.Row]:
        return self.conexion.execute(sql, parametros).fetchall()

    def consultar_uno(self, sql: str, parametros: Sequence[Any] = ()) -> sqlite3.Row | None:
        return self.conexion.execute(sql, parametros).fetchone()

    def cerrar(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None
