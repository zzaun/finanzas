"""Acceso a la tabla de categorías."""
from __future__ import annotations

from finanzas.datos.base_datos import BaseDatos
from finanzas.logica.modelos import Categoria, TipoMovimiento


class RepositorioCategorias:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    @staticmethod
    def _modelo(fila) -> Categoria:
        return Categoria(
            id=fila["id"],
            anio=fila["anio"],
            nombre=fila["nombre"],
            tipo=TipoMovimiento(fila["tipo"]),
            es_hormiga=bool(fila["es_hormiga"]),
            activa=bool(fila["activa"]),
        )

    def agregar(self, c: Categoria) -> int:
        cursor = self.bd.ejecutar(
            "INSERT INTO categorias (anio, nombre, tipo, es_hormiga, activa) VALUES (?, ?, ?, ?, ?)",
            (c.anio, c.nombre, c.tipo.value, int(c.es_hormiga), int(c.activa)),
        )
        return cursor.lastrowid

    def obtener(self, id_: int) -> Categoria | None:
        fila = self.bd.consultar_uno("SELECT * FROM categorias WHERE id = ?", (id_,))
        return self._modelo(fila) if fila else None

    def buscar(self, anio: int, nombre: str, tipo: TipoMovimiento) -> Categoria | None:
        fila = self.bd.consultar_uno(
            "SELECT * FROM categorias WHERE anio = ? AND nombre = ? AND tipo = ?",
            (anio, nombre, tipo.value),
        )
        return self._modelo(fila) if fila else None

    def listar(
        self, anio: int, tipo: TipoMovimiento | None = None, solo_activas: bool = True
    ) -> list[Categoria]:
        sql = "SELECT * FROM categorias WHERE anio = ?"
        parametros: list = [anio]
        if tipo is not None:
            sql += " AND tipo = ?"
            parametros.append(tipo.value)
        if solo_activas:
            sql += " AND activa = 1"
        sql += " ORDER BY tipo, nombre"
        return [self._modelo(f) for f in self.bd.consultar(sql, parametros)]

    def actualizar(self, c: Categoria) -> None:
        self.bd.ejecutar(
            "UPDATE categorias SET nombre = ?, es_hormiga = ?, activa = ? WHERE id = ?",
            (c.nombre, int(c.es_hormiga), int(c.activa), c.id),
        )

    def contar_anio(self, anio: int) -> int:
        return self.bd.consultar_uno(
            "SELECT COUNT(*) AS n FROM categorias WHERE anio = ?", (anio,)
        )["n"]

    def copiar_anio(self, origen: int, destino: int) -> int:
        """Copia las categorías activas de un año a otro; devuelve cuántas creó."""
        cursor = self.bd.ejecutar(
            "INSERT OR IGNORE INTO categorias (anio, nombre, tipo, es_hormiga, activa) "
            "SELECT ?, nombre, tipo, es_hormiga, 1 FROM categorias WHERE anio = ? AND activa = 1",
            (destino, origen),
        )
        return cursor.rowcount
