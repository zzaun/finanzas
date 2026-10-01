"""Acceso a la tabla de movimientos. Aquí vive todo el SQL de movimientos."""
from __future__ import annotations

from datetime import date

from finanzas.datos.base_datos import BaseDatos
from finanzas.logica.modelos import (
    EstadoMovimiento,
    FilaCategoria,
    Movimiento,
    TipoMovimiento,
)

_COLUMNAS = (
    "id, descripcion, monto, categoria_id, categoria, tipo, es_hormiga, "
    "fecha_movimiento, fecha_captura, estado, es_anterior, notas"
)


def _valor(x):
    """Acepta enumeraciones o texto plano."""
    return getattr(x, "value", x)


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


class RepositorioMovimientos:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    @staticmethod
    def _modelo(fila) -> Movimiento:
        fecha = fila["fecha_movimiento"]
        return Movimiento(
            id=fila["id"],
            descripcion=fila["descripcion"],
            monto=fila["monto"],
            categoria_id=fila["categoria_id"],
            fecha_movimiento=date.fromisoformat(fecha) if fecha else None,
            estado=EstadoMovimiento(fila["estado"]),
            es_anterior=bool(fila["es_anterior"]),
            notas=fila["notas"],
            fecha_captura=fila["fecha_captura"],
            categoria=fila["categoria"],
            tipo=TipoMovimiento(fila["tipo"]),
            es_hormiga=bool(fila["es_hormiga"]),
        )

    # ---- escritura -------------------------------------------------
    def agregar(self, m: Movimiento) -> int:
        cursor = self.bd.ejecutar(
            "INSERT INTO movimientos (descripcion, monto, categoria_id, fecha_movimiento, "
            "estado, es_anterior, notas) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                m.descripcion, m.monto, m.categoria_id, _iso(m.fecha_movimiento),
                m.estado.value, int(m.es_anterior), m.notas,
            ),
        )
        return cursor.lastrowid

    def actualizar(self, m: Movimiento) -> None:
        self.bd.ejecutar(
            "UPDATE movimientos SET descripcion = ?, monto = ?, categoria_id = ?, "
            "fecha_movimiento = ?, estado = ?, es_anterior = ?, notas = ? WHERE id = ?",
            (
                m.descripcion, m.monto, m.categoria_id, _iso(m.fecha_movimiento),
                m.estado.value, int(m.es_anterior), m.notas, m.id,
            ),
        )

    def eliminar(self, id_: int) -> bool:
        return self.bd.ejecutar("DELETE FROM movimientos WHERE id = ?", (id_,)).rowcount > 0

    # ---- lectura ---------------------------------------------------
    def obtener(self, id_: int) -> Movimiento | None:
        fila = self.bd.consultar_uno(
            f"SELECT {_COLUMNAS} FROM v_movimientos_detalle WHERE id = ?", (id_,)
        )
        return self._modelo(fila) if fila else None

    @staticmethod
    def _filtros(desde, hasta, categoria_id, tipo, estado, texto) -> tuple[str, list]:
        condiciones: list[str] = []
        parametros: list = []
        if desde is not None:
            condiciones.append("fecha_movimiento >= ?")
            parametros.append(_iso(desde))
        if hasta is not None:
            condiciones.append("fecha_movimiento <= ?")
            parametros.append(_iso(hasta))
        if categoria_id is not None:
            condiciones.append("categoria_id = ?")
            parametros.append(categoria_id)
        if tipo is not None:
            condiciones.append("tipo = ?")
            parametros.append(_valor(tipo))
        if estado is not None:
            condiciones.append("estado = ?")
            parametros.append(_valor(estado))
        if texto:
            condiciones.append("(descripcion LIKE ? OR categoria LIKE ? OR notas LIKE ?)")
            parametros.extend([f"%{texto}%"] * 3)
        donde = " WHERE " + " AND ".join(condiciones) if condiciones else ""
        return donde, parametros

    def listar(
        self,
        *,
        desde: date | None = None,
        hasta: date | None = None,
        categoria_id: int | None = None,
        tipo=None,
        estado=None,
        texto: str | None = None,
        limite: int | None = None,
        desplazamiento: int = 0,
        descendente: bool = False,
    ) -> list[Movimiento]:
        donde, parametros = self._filtros(desde, hasta, categoria_id, tipo, estado, texto)
        sentido = "DESC" if descendente else "ASC"
        sql = (
            f"SELECT {_COLUMNAS} FROM v_movimientos_detalle{donde} "
            f"ORDER BY fecha_movimiento IS NULL, fecha_movimiento {sentido}, id {sentido} "
            "LIMIT ? OFFSET ?"
        )
        parametros += [limite if limite is not None else -1, desplazamiento]
        return [self._modelo(f) for f in self.bd.consultar(sql, parametros)]

    def contar(
        self, *, desde=None, hasta=None, categoria_id=None, tipo=None, estado=None, texto=None
    ) -> int:
        donde, parametros = self._filtros(desde, hasta, categoria_id, tipo, estado, texto)
        return self.bd.consultar_uno(
            f"SELECT COUNT(*) AS n FROM v_movimientos_detalle{donde}", parametros
        )["n"]

    # ---- totales (solo movimientos reales con fecha) ----------------
    def totales_por_tipo(self, desde: date, hasta: date) -> dict[str, int]:
        filas = self.bd.consultar(
            "SELECT tipo, SUM(monto) AS total FROM v_movimientos_detalle "
            "WHERE estado = 'real' AND fecha_movimiento BETWEEN ? AND ? GROUP BY tipo",
            (_iso(desde), _iso(hasta)),
        )
        totales = {"ingreso": 0, "gasto": 0, "ahorro": 0}
        for f in filas:
            totales[f["tipo"]] = f["total"]
        return totales

    def total_hormiga(self, desde: date, hasta: date) -> int:
        fila = self.bd.consultar_uno(
            "SELECT COALESCE(SUM(monto), 0) AS total FROM v_movimientos_detalle "
            "WHERE estado = 'real' AND tipo = 'gasto' AND es_hormiga = 1 "
            "AND fecha_movimiento BETWEEN ? AND ?",
            (_iso(desde), _iso(hasta)),
        )
        return fila["total"]

    def totales_por_categoria(self, desde: date, hasta: date, tipo=None) -> list[FilaCategoria]:
        sql = (
            "SELECT categoria, tipo, es_hormiga, SUM(monto) AS total FROM v_movimientos_detalle "
            "WHERE estado = 'real' AND fecha_movimiento BETWEEN ? AND ?"
        )
        parametros: list = [_iso(desde), _iso(hasta)]
        if tipo is not None:
            sql += " AND tipo = ?"
            parametros.append(_valor(tipo))
        sql += " GROUP BY categoria_id ORDER BY total DESC"
        return [
            FilaCategoria(
                categoria=f["categoria"],
                tipo=TipoMovimiento(f["tipo"]),
                total=f["total"],
                es_hormiga=bool(f["es_hormiga"]),
            )
            for f in self.bd.consultar(sql, parametros)
        ]

    def saldo_antes_de(self, fecha: date) -> int:
        """Ingresos menos gastos y ahorro de todo lo real anterior a la fecha."""
        fila = self.bd.consultar_uno(
            "SELECT COALESCE(SUM(CASE tipo WHEN 'ingreso' THEN monto ELSE -monto END), 0) AS saldo "
            "FROM v_movimientos_detalle WHERE estado = 'real' AND fecha_movimiento < ?",
            (_iso(fecha),),
        )
        return fila["saldo"]
