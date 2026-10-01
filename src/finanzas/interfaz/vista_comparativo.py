"""Planeado contra real de un mes, y la tabla del año."""
from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from finanzas.contenedor import Servicios
from finanzas.interfaz.estilos import Estilos, celda, crear_tabla
from finanzas.logica.dinero import Dinero
from finanzas.logica.periodos import nombre_mes


class VistaComparativo(QWidget):
    def __init__(self, servicios: Servicios, parent=None) -> None:
        super().__init__(parent)
        self.servicios = servicios
        hoy = date.today()

        self.spn_anio = QSpinBox()
        self.spn_anio.setRange(2000, 2100)
        self.spn_anio.setValue(hoy.year)
        self.cmb_mes = QComboBox()
        for numero in range(1, 13):
            self.cmb_mes.addItem(nombre_mes(numero), numero)
        self.cmb_mes.setCurrentIndex(hoy.month - 1)

        barra = QHBoxLayout()
        barra.addWidget(QLabel("Año:"))
        barra.addWidget(self.spn_anio)
        barra.addWidget(QLabel("Mes:"))
        barra.addWidget(self.cmb_mes)
        barra.addStretch(1)

        self.titulo_mes = QLabel()
        self.titulo_mes.setObjectName("titulo")
        self.tabla_mes = crear_tabla(["Concepto", "Planeado", "Real", "Diferencia"])
        self.titulo_anio = QLabel()
        self.titulo_anio.setObjectName("titulo")
        self.tabla_anio = crear_tabla(["Mes", "Ingresos", "Gastos", "Ahorro", "Disponible"])

        diseno = QVBoxLayout(self)
        diseno.addLayout(barra)
        diseno.addWidget(self.titulo_mes)
        diseno.addWidget(self.tabla_mes, 1)
        diseno.addWidget(self.titulo_anio)
        diseno.addWidget(self.tabla_anio, 3)

        self.spn_anio.valueChanged.connect(self.refrescar)
        self.cmb_mes.currentIndexChanged.connect(self.refrescar)

    def refrescar(self, *_) -> None:
        anio = self.spn_anio.value()
        mes = self.cmb_mes.currentData()
        servicio = self.servicios.resumen

        comparativo = servicio.comparativo_mes(anio, mes)
        self.titulo_mes.setText(f"Planeado contra real: {nombre_mes(mes)} {anio}")
        self.tabla_mes.setRowCount(len(comparativo.lineas))
        for numero, linea in enumerate(comparativo.lineas):
            # Gastar de más es malo; en lo demás, quedarse corto lo es.
            malo = linea.diferencia > 0 if linea.concepto == "Gastos" else linea.diferencia < 0
            color = Estilos.COLOR_NEGATIVO if malo else None
            self.tabla_mes.setItem(numero, 0, celda(linea.concepto))
            self.tabla_mes.setItem(numero, 1, celda(Dinero.formato(linea.planeado), derecha=True))
            self.tabla_mes.setItem(numero, 2, celda(Dinero.formato(linea.real), derecha=True))
            self.tabla_mes.setItem(numero, 3, celda(Dinero.formato(linea.diferencia), derecha=True, color=color))

        meses, total = servicio.tabla_anual(anio)
        self.titulo_anio.setText(f"Resumen de {anio}")
        self.tabla_anio.setRowCount(len(meses) + 1)
        filas = [(nombre_mes(i + 1), r, False) for i, r in enumerate(meses)] + [("Total", total, True)]
        for numero, (nombre, r, negrita) in enumerate(filas):
            color = Estilos.COLOR_NEGATIVO if r.disponible < 0 else None
            self.tabla_anio.setItem(numero, 0, celda(nombre, negrita=negrita))
            self.tabla_anio.setItem(numero, 1, celda(Dinero.formato(r.ingresos), True, negrita=negrita))
            self.tabla_anio.setItem(numero, 2, celda(Dinero.formato(r.gastos), True, negrita=negrita))
            self.tabla_anio.setItem(numero, 3, celda(Dinero.formato(r.ahorro), True, negrita=negrita))
            self.tabla_anio.setItem(numero, 4, celda(Dinero.formato(r.disponible), True, color, negrita))
