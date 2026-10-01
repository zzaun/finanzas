"""Puente entre la lista de movimientos y la tabla de Qt.

Carga los movimientos por páginas mientras la persona se desplaza, así
no hay límite de líneas y la tabla sigue siendo rápida.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from finanzas.interfaz.estilos import Estilos
from finanzas.logica.dinero import Dinero
from finanzas.logica.modelos import EstadoMovimiento, Movimiento, TipoMovimiento

COL_ID, COL_FECHA, COL_DESCRIPCION, COL_CATEGORIA, COL_TIPO, COL_MONTO, COL_SALDO = range(7)
ENCABEZADOS = ["ID", "Fecha", "Descripción", "Categoría", "Tipo", "Monto", "Saldo"]


class ModeloTablaMovimientos(QAbstractTableModel):
    TAMANO_PAGINA = 200

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._filas: list[tuple[Movimiento, int | None]] = []
        self._total = 0
        self._cargar: Callable[[int, int], list[Movimiento]] | None = None
        self._saldo = 0

    # ---- carga -------------------------------------------------------
    def configurar(self, total: int, cargar: Callable[[int, int], list[Movimiento]], saldo_inicial: int = 0) -> None:
        """``cargar(limite, desplazamiento)`` devuelve la página pedida."""
        self.beginResetModel()
        self._filas = []
        self._total = total
        self._cargar = cargar
        self._saldo = saldo_inicial
        self._filas.extend(self._leer_pagina())
        self.endResetModel()

    def _leer_pagina(self) -> list[tuple[Movimiento, int | None]]:
        if self._cargar is None:
            return []
        nuevas = []
        for movimiento in self._cargar(self.TAMANO_PAGINA, len(self._filas)):
            self._saldo += movimiento.efecto
            nuevas.append((movimiento, self._saldo if movimiento.efecto else None))
        return nuevas

    def canFetchMore(self, parent=QModelIndex()) -> bool:
        return not parent.isValid() and len(self._filas) < self._total

    def fetchMore(self, parent=QModelIndex()) -> None:
        if parent.isValid():
            return
        nuevas = self._leer_pagina()
        if not nuevas:
            self._total = len(self._filas)  # los datos cambiaron: no insistir
            return
        inicio = len(self._filas)
        self.beginInsertRows(QModelIndex(), inicio, inicio + len(nuevas) - 1)
        self._filas.extend(nuevas)
        self.endInsertRows()

    def movimiento_en(self, fila: int) -> Movimiento | None:
        return self._filas[fila][0] if 0 <= fila < len(self._filas) else None

    # ---- interfaz del modelo ---------------------------------------------
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._filas)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(ENCABEZADOS)

    def headerData(self, seccion, orientacion, rol=Qt.ItemDataRole.DisplayRole):
        if orientacion == Qt.Orientation.Horizontal and rol == Qt.ItemDataRole.DisplayRole:
            return ENCABEZADOS[seccion]
        return None

    def data(self, indice, rol=Qt.ItemDataRole.DisplayRole):
        if not indice.isValid():
            return None
        movimiento, saldo = self._filas[indice.row()]
        columna = indice.column()

        if rol == Qt.ItemDataRole.DisplayRole:
            if columna == COL_ID:
                return movimiento.id
            if columna == COL_FECHA:
                return movimiento.fecha_movimiento.strftime("%d/%m/%y") if movimiento.fecha_movimiento else "**/**/**"
            if columna == COL_DESCRIPCION:
                return movimiento.descripcion
            if columna == COL_CATEGORIA:
                return movimiento.categoria
            if columna == COL_TIPO:
                return movimiento.tipo.value.capitalize() if movimiento.tipo else ""
            if columna == COL_MONTO:
                return Dinero.formato(movimiento.monto)
            if columna == COL_SALDO:
                return Dinero.formato(saldo) if saldo is not None else ""

        if rol == Qt.ItemDataRole.TextAlignmentRole and columna in (COL_MONTO, COL_SALDO):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        if rol == Qt.ItemDataRole.ForegroundRole:
            if movimiento.es_anterior:
                return QBrush(QColor(Estilos.COLOR_ANTERIOR))
            if movimiento.estado is EstadoMovimiento.PENDIENTE:
                return QBrush(QColor(Estilos.COLOR_PENDIENTE))
            if columna == COL_MONTO and movimiento.tipo is TipoMovimiento.INGRESO:
                return QBrush(QColor(Estilos.COLOR_POSITIVO))

        if rol == Qt.ItemDataRole.UserRole:
            return movimiento.id
        return None
