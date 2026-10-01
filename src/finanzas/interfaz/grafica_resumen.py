"""Gráfica de pastel con el gasto por categoría."""
from __future__ import annotations

from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

from finanzas.logica.dinero import Dinero
from finanzas.logica.modelos import FilaCategoria


class GraficaResumen(QChartView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(260)

    def mostrar(self, filas: list[FilaCategoria], titulo: str) -> None:
        grafica = QChart()
        filas = [f for f in filas if f.total > 0]
        if filas:
            serie = QPieSeries()
            for fila in filas:
                serie.append(f"{fila.categoria} ({Dinero.formato(fila.total)})", fila.total / 100)
            grafica.addSeries(serie)
            grafica.setTitle(titulo)
            grafica.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            grafica.setTitle(f"{titulo}: sin datos en este periodo")
            grafica.legend().hide()
        self.setChart(grafica)
