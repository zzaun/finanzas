"""Colores, hoja de estilo y ayudas para armar tablas."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem


class Estilos:
    COLOR_ANTERIOR = "#c62828"   # movimientos de un periodo anterior
    COLOR_PENDIENTE = "#1565c0"  # movimientos pendientes
    COLOR_POSITIVO = "#2e7d32"
    COLOR_NEGATIVO = "#c62828"

    HOJA = """
    QPushButton { padding: 6px 14px; }
    QLabel#titulo { font-size: 16pt; font-weight: 600; }
    QLabel#cifra { font-size: 15pt; font-weight: 600; }
    QLabel#etiqueta { color: palette(mid); }
    QFrame#tarjeta { border: 1px solid palette(mid); border-radius: 6px; }
    QHeaderView::section { padding: 4px 6px; }
    """

    @classmethod
    def aplicar(cls, qt) -> None:
        qt.setStyle("Fusion")
        qt.setStyleSheet(cls.HOJA)


def celda(texto: str, derecha: bool = False, color: str | None = None, negrita: bool = False) -> QTableWidgetItem:
    """Celda de solo lectura con alineación, color y negrita opcionales."""
    item = QTableWidgetItem(texto)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    if derecha:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if color:
        item.setForeground(QBrush(QColor(color)))
    if negrita:
        fuente = item.font()
        fuente.setBold(True)
        item.setFont(fuente)
    return item


def crear_tabla(columnas: list[str]) -> QTableWidget:
    """Tabla de solo lectura, con filas completas seleccionables."""
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tabla.setAlternatingRowColors(True)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return tabla
