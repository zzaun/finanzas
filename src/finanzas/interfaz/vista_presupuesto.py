"""Captura de lo planeado para cada mes del año."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finanzas.contenedor import Servicios
from finanzas.excepciones import ErrorFinanzas
from finanzas.interfaz.estilos import celda
from finanzas.logica.dinero import Dinero
from finanzas.logica.periodos import nombre_mes

COLUMNAS = ["Mes", "Ingresos planeados", "Gastos planeados", "Ahorro planeado", "Disponible planeado"]


class VistaPresupuesto(QWidget):
    def __init__(self, servicios: Servicios, parent=None) -> None:
        super().__init__(parent)
        self.servicios = servicios
        self._cargando = False

        self.spn_anio = QSpinBox()
        self.spn_anio.setRange(2000, 2100)
        self.spn_anio.setValue(date.today().year)
        self.btn_guardar = QPushButton("Guardar presupuesto")
        self.lbl_estado = QLabel()

        barra = QHBoxLayout()
        barra.addWidget(QLabel("Año:"))
        barra.addWidget(self.spn_anio)
        barra.addWidget(self.btn_guardar)
        barra.addWidget(self.lbl_estado, 1)

        self.tabla = QTableWidget(12, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)

        aviso = QLabel("Escribe los montos en pesos. Disponible planeado = ingresos − gastos − ahorro.")
        aviso.setObjectName("etiqueta")

        diseno = QVBoxLayout(self)
        diseno.addLayout(barra)
        diseno.addWidget(self.tabla, 1)
        diseno.addWidget(aviso)

        self.spn_anio.valueChanged.connect(self.refrescar)
        self.btn_guardar.clicked.connect(self._guardar)
        self.tabla.itemChanged.connect(self._al_cambiar_celda)

    def refrescar(self, *_) -> None:
        self._cargando = True
        try:
            for numero, p in enumerate(self.servicios.presupuesto.listar_anio(self.spn_anio.value())):
                self.tabla.setItem(numero, 0, celda(nombre_mes(p.mes)))
                for columna, valor in ((1, p.ingresos_planeados), (2, p.gastos_planeados), (3, p.ahorro_planeado)):
                    item = QTableWidgetItem(Dinero.como_texto(valor))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.tabla.setItem(numero, columna, item)
                self.tabla.setItem(
                    numero, 4, celda(Dinero.como_texto(p.disponible_planeado), derecha=True)
                )
        finally:
            self._cargando = False
        self.lbl_estado.clear()

    def _leer_fila(self, fila: int) -> tuple[int, int, int]:
        def monto(columna: int) -> int:
            texto = self.tabla.item(fila, columna).text().strip() or "0"
            return Dinero.a_centavos(texto)

        return monto(1), monto(2), monto(3)

    def _al_cambiar_celda(self, item: QTableWidgetItem) -> None:
        if self._cargando or item.column() not in (1, 2, 3):
            return
        fila = item.row()
        self._cargando = True
        try:
            ingresos, gastos, ahorro = self._leer_fila(fila)
            self.tabla.setItem(
                fila, 4, celda(Dinero.como_texto(ingresos - gastos - ahorro), derecha=True)
            )
        except ValueError:
            self.tabla.setItem(fila, 4, celda("—", derecha=True))
        finally:
            self._cargando = False
        self.lbl_estado.clear()

    def _guardar(self) -> None:
        anio = self.spn_anio.value()
        try:
            for fila in range(12):
                try:
                    ingresos, gastos, ahorro = self._leer_fila(fila)
                except ValueError:
                    raise ErrorFinanzas(f"Revisa las cantidades de {nombre_mes(fila + 1)}: no son números válidos.")
                self.servicios.presupuesto.guardar(anio, fila + 1, ingresos, gastos, ahorro)
        except ErrorFinanzas as error:
            QMessageBox.warning(self, "No se pudo guardar", str(error))
            return
        self.lbl_estado.setText(f"Presupuesto de {anio} guardado.")
