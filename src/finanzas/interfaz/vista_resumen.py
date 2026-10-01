"""Resumen por semana, mes o año, con desglose por categoría."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finanzas.contenedor import Servicios
from finanzas.interfaz.estilos import Estilos, celda, crear_tabla
from finanzas.interfaz.grafica_resumen import GraficaResumen
from finanzas.logica.dinero import Dinero
from finanzas.logica.modelos import TipoMovimiento, TipoPeriodo


class VistaResumen(QWidget):
    def __init__(self, servicios: Servicios, parent=None) -> None:
        super().__init__(parent)
        self.servicios = servicios
        self._periodo = servicios.resumen.periodo(TipoPeriodo.MES)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Semana", TipoPeriodo.SEMANA.value)
        self.cmb_tipo.addItem("Mes", TipoPeriodo.MES.value)
        self.cmb_tipo.addItem("Año", TipoPeriodo.ANIO.value)
        self.cmb_tipo.setCurrentIndex(1)
        self.btn_anterior = QPushButton("◀")
        self.btn_siguiente = QPushButton("▶")
        self.btn_hoy = QPushButton("Hoy")
        self.lbl_periodo = QLabel()
        self.lbl_periodo.setObjectName("titulo")

        barra = QHBoxLayout()
        barra.addWidget(self.cmb_tipo)
        barra.addWidget(self.btn_anterior)
        barra.addWidget(self.lbl_periodo, 1)
        barra.addWidget(self.btn_siguiente)
        barra.addWidget(self.btn_hoy)

        tarjeta_ingresos, self.cifra_ingresos = self._tarjeta("Ingresos")
        tarjeta_gastos, self.cifra_gastos = self._tarjeta("Gastos")
        tarjeta_ahorro, self.cifra_ahorro = self._tarjeta("Ahorro")
        tarjeta_disponible, self.cifra_disponible = self._tarjeta("Disponible")
        tarjeta_hormiga, self.cifra_hormiga = self._tarjeta("De gasto hormiga")
        tarjetas = QHBoxLayout()
        for tarjeta in (tarjeta_ingresos, tarjeta_gastos, tarjeta_ahorro, tarjeta_disponible, tarjeta_hormiga):
            tarjetas.addWidget(tarjeta)

        self.tabla = crear_tabla(["Categoría", "Tipo", "Total"])
        self.grafica = GraficaResumen()
        detalle = QHBoxLayout()
        detalle.addWidget(self.tabla, 1)
        detalle.addWidget(self.grafica, 1)

        diseno = QVBoxLayout(self)
        diseno.addLayout(barra)
        diseno.addLayout(tarjetas)
        diseno.addLayout(detalle, 1)

        self.cmb_tipo.currentIndexChanged.connect(self._al_cambiar_tipo)
        self.btn_anterior.clicked.connect(self._ir_anterior)
        self.btn_siguiente.clicked.connect(self._ir_siguiente)
        self.btn_hoy.clicked.connect(self._ir_hoy)

    @staticmethod
    def _tarjeta(titulo: str) -> tuple[QFrame, QLabel]:
        marco = QFrame()
        marco.setObjectName("tarjeta")
        caja = QVBoxLayout(marco)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("etiqueta")
        cifra = QLabel("$0.00")
        cifra.setObjectName("cifra")
        caja.addWidget(etiqueta)
        caja.addWidget(cifra)
        return marco, cifra

    # ---- navegación -----------------------------------------------------
    def _al_cambiar_tipo(self) -> None:
        self._periodo = self.servicios.resumen.periodo(self.cmb_tipo.currentData(), self._periodo.inicio)
        self.refrescar()

    def _ir_anterior(self) -> None:
        self._periodo = self.servicios.resumen.periodo_anterior(self._periodo)
        self.refrescar()

    def _ir_siguiente(self) -> None:
        self._periodo = self.servicios.resumen.periodo_siguiente(self._periodo)
        self.refrescar()

    def _ir_hoy(self) -> None:
        self._periodo = self.servicios.resumen.periodo(self.cmb_tipo.currentData())
        self.refrescar()

    # ---- contenido --------------------------------------------------------
    def refrescar(self) -> None:
        servicio = self.servicios.resumen
        # Se recalcula por si cambió el día en que empieza la semana.
        self._periodo = servicio.periodo(self._periodo.tipo, self._periodo.inicio)
        self.lbl_periodo.setText(self._periodo.etiqueta)

        r = servicio.resumen_periodo(self._periodo)
        self.cifra_ingresos.setText(Dinero.formato(r.ingresos))
        self.cifra_gastos.setText(Dinero.formato(r.gastos))
        self.cifra_ahorro.setText(Dinero.formato(r.ahorro))
        self.cifra_disponible.setText(Dinero.formato(r.disponible))
        color = Estilos.COLOR_NEGATIVO if r.disponible < 0 else Estilos.COLOR_POSITIVO
        self.cifra_disponible.setStyleSheet(f"color: {color};")
        self.cifra_hormiga.setText(Dinero.formato(r.hormiga))

        filas = servicio.desglose_categorias(self._periodo)
        self.tabla.setRowCount(len(filas))
        for numero, fila in enumerate(filas):
            self.tabla.setItem(numero, 0, celda(fila.categoria))
            self.tabla.setItem(numero, 1, celda(fila.tipo.value.capitalize()))
            self.tabla.setItem(numero, 2, celda(Dinero.formato(fila.total), derecha=True))
        gastos = [f for f in filas if f.tipo is TipoMovimiento.GASTO]
        self.grafica.mostrar(gastos, "Gastos por categoría")
