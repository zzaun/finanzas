"""Pestaña con la tabla de movimientos, filtros y botones de captura."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QModelIndex
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from finanzas.contenedor import Servicios
from finanzas.excepciones import ErrorFinanzas
from finanzas.interfaz.dialogo_movimiento import DialogoMovimiento
from finanzas.interfaz.modelo_tabla_movimientos import (
    COL_DESCRIPCION,
    COL_SALDO,
    ModeloTablaMovimientos,
)
from finanzas.logica.dinero import Dinero
from finanzas.logica.modelos import Movimiento, TipoMovimiento


class VistaMovimientos(QWidget):
    def __init__(self, servicios: Servicios, parent=None) -> None:
        super().__init__(parent)
        self.servicios = servicios
        self.modelo = ModeloTablaMovimientos(self)

        hoy = QDate.currentDate()
        primero = QDate(hoy.year(), hoy.month(), 1)
        self.fecha_desde = self._selector_fecha(primero)
        self.fecha_hasta = self._selector_fecha(primero.addMonths(1).addDays(-1))
        self.chk_todo = QCheckBox("Todo el historial")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Todos los tipos", None)
        for tipo in TipoMovimiento:
            self.cmb_tipo.addItem(tipo.value.capitalize(), tipo.value)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por descripción, categoría o nota")
        self.txt_buscar.setClearButtonEnabled(True)

        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("Desde:"))
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(QLabel("Hasta:"))
        filtros.addWidget(self.fecha_hasta)
        filtros.addWidget(self.chk_todo)
        filtros.addWidget(self.cmb_tipo)
        filtros.addWidget(self.txt_buscar, 1)

        self.btn_agregar = QPushButton("Agregar movimiento")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Eliminar")
        botones = QHBoxLayout()
        botones.addWidget(self.btn_agregar)
        botones.addWidget(self.btn_editar)
        botones.addWidget(self.btn_eliminar)
        botones.addStretch(1)

        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        encabezado = self.tabla.horizontalHeader()
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        encabezado.setSectionResizeMode(COL_DESCRIPCION, QHeaderView.ResizeMode.Stretch)

        self.lbl_resumen = QLabel()

        diseno = QVBoxLayout(self)
        diseno.addLayout(filtros)
        diseno.addLayout(botones)
        diseno.addWidget(self.tabla, 1)
        diseno.addWidget(self.lbl_resumen)

        self.fecha_desde.dateChanged.connect(self.refrescar)
        self.fecha_hasta.dateChanged.connect(self.refrescar)
        self.chk_todo.toggled.connect(self._al_cambiar_todo)
        self.cmb_tipo.currentIndexChanged.connect(self.refrescar)
        self.txt_buscar.returnPressed.connect(self.refrescar)
        self.btn_agregar.clicked.connect(self._agregar)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.tabla.doubleClicked.connect(self._editar)
        self.tabla.verticalScrollBar().valueChanged.connect(self._al_desplazar)

        self.refrescar()

    @staticmethod
    def _selector_fecha(fecha: QDate) -> QDateEdit:
        editor = QDateEdit(fecha)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")
        return editor

    def _al_cambiar_todo(self, marcado: bool) -> None:
        self.fecha_desde.setEnabled(not marcado)
        self.fecha_hasta.setEnabled(not marcado)
        self.refrescar()

    def _filtros(self) -> dict:
        desde = hasta = None
        if not self.chk_todo.isChecked():
            desde = self.fecha_desde.date().toPython()
            hasta = self.fecha_hasta.date().toPython()
        return {
            "desde": desde,
            "hasta": hasta,
            "tipo": self.cmb_tipo.currentData(),
            "texto": self.txt_buscar.text().strip() or None,
            "estado": "real",
        }

    def refrescar(self, *_) -> None:
        filtros = self._filtros()
        total = self.servicios.movimientos.contar(**filtros)
        # El saldo corrido solo tiene sentido si no se filtra por tipo ni texto.
        saldo_valido = filtros["tipo"] is None and not filtros["texto"]
        saldo_inicial = 0
        if saldo_valido and filtros["desde"] is not None:
            saldo_inicial = self.servicios.resumen.saldo_inicial(filtros["desde"])

        def cargar(limite: int, desplazamiento: int) -> list[Movimiento]:
            return self.servicios.movimientos.listar(
                limite=limite, desplazamiento=desplazamiento, **filtros
            )

        self.modelo.configurar(total, cargar, saldo_inicial)
        self.tabla.setColumnHidden(COL_SALDO, not saldo_valido)

        desde = filtros["desde"] or date(1900, 1, 1)
        hasta = filtros["hasta"] or date(2999, 12, 31)
        r = self.servicios.resumen.resumen_rango(desde, hasta)
        self.lbl_resumen.setText(
            f"{total} movimientos   |   En el rango:  Ingresos {Dinero.formato(r.ingresos)}   "
            f"Gastos {Dinero.formato(r.gastos)}   Ahorro {Dinero.formato(r.ahorro)}   "
            f"Disponible {Dinero.formato(r.disponible)}"
        )

    def _al_desplazar(self, valor: int) -> None:
        barra = self.tabla.verticalScrollBar()
        if valor >= barra.maximum() - 3 and self.modelo.canFetchMore(QModelIndex()):
            self.modelo.fetchMore(QModelIndex())

    def _seleccionado(self) -> Movimiento | None:
        indice = self.tabla.currentIndex()
        return self.modelo.movimiento_en(indice.row()) if indice.isValid() else None

    def _agregar(self) -> None:
        if DialogoMovimiento(self.servicios, parent=self).exec():
            self.refrescar()

    def _editar(self, *_) -> None:
        movimiento = self._seleccionado()
        if movimiento is None:
            QMessageBox.information(self, "Editar", "Selecciona un movimiento de la tabla.")
            return
        if DialogoMovimiento(self.servicios, movimiento=movimiento, parent=self).exec():
            self.refrescar()

    def _eliminar(self) -> None:
        movimiento = self._seleccionado()
        if movimiento is None:
            QMessageBox.information(self, "Eliminar", "Selecciona un movimiento de la tabla.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar movimiento",
            f"¿Eliminar «{movimiento.descripcion}» por {Dinero.formato(movimiento.monto)}?",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        try:
            self.servicios.movimientos.eliminar(movimiento.id)
        except ErrorFinanzas as error:
            QMessageBox.warning(self, "No se pudo eliminar", str(error))
        self.refrescar()
