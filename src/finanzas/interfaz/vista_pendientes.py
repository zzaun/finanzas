"""Movimientos pendientes: los que todavía no tienen fecha."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finanzas.contenedor import Servicios
from finanzas.excepciones import ErrorFinanzas
from finanzas.interfaz.dialogo_movimiento import DialogoMovimiento
from finanzas.interfaz.estilos import Estilos, celda, crear_tabla
from finanzas.logica.dinero import Dinero
from finanzas.logica.modelos import TipoMovimiento


def pedir_fecha(parent) -> date | None:
    """Pregunta con qué fecha se registra un pendiente; ``None`` si se cancela."""
    dialogo = QDialog(parent)
    dialogo.setWindowTitle("Marcar como real")
    editor = QDateEdit(QDate.currentDate())
    editor.setCalendarPopup(True)
    editor.setDisplayFormat("dd/MM/yyyy")
    botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    botones.accepted.connect(dialogo.accept)
    botones.rejected.connect(dialogo.reject)
    formulario = QFormLayout(dialogo)
    formulario.addRow("Fecha del movimiento:", editor)
    formulario.addRow(botones)
    return editor.date().toPython() if dialogo.exec() else None


class VistaPendientes(QWidget):
    def __init__(self, servicios: Servicios, parent=None) -> None:
        super().__init__(parent)
        self.servicios = servicios

        self.btn_agregar = QPushButton("Agregar pendiente")
        self.btn_editar = QPushButton("Editar")
        self.btn_real = QPushButton("Marcar como real")
        self.btn_eliminar = QPushButton("Eliminar")
        botones = QHBoxLayout()
        for boton in (self.btn_agregar, self.btn_editar, self.btn_real, self.btn_eliminar):
            botones.addWidget(boton)
        botones.addStretch(1)

        self.tabla = crear_tabla(["Descripción", "Categoría", "Tipo", "Monto", "Notas"])
        self.lbl_total = QLabel()

        diseno = QVBoxLayout(self)
        diseno.addLayout(botones)
        diseno.addWidget(self.tabla, 1)
        diseno.addWidget(self.lbl_total)

        self.btn_agregar.clicked.connect(self._agregar)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_real.clicked.connect(self._marcar_real)
        self.btn_eliminar.clicked.connect(self._eliminar)

    def refrescar(self) -> None:
        pendientes = self.servicios.movimientos.pendientes()
        self.tabla.setRowCount(len(pendientes))
        por_pagar = por_cobrar = 0
        for numero, m in enumerate(pendientes):
            descripcion = celda(m.descripcion, color=Estilos.COLOR_PENDIENTE)
            descripcion.setData(Qt.ItemDataRole.UserRole, m.id)
            self.tabla.setItem(numero, 0, descripcion)
            self.tabla.setItem(numero, 1, celda(m.categoria or ""))
            self.tabla.setItem(numero, 2, celda(m.tipo.value.capitalize() if m.tipo else ""))
            self.tabla.setItem(numero, 3, celda(Dinero.formato(m.monto), derecha=True))
            self.tabla.setItem(numero, 4, celda(m.notas or ""))
            if m.tipo is TipoMovimiento.INGRESO:
                por_cobrar += m.monto
            else:
                por_pagar += m.monto
        self.lbl_total.setText(
            f"{len(pendientes)} pendientes   |   Por pagar o apartar: {Dinero.formato(por_pagar)}   "
            f"Por recibir: {Dinero.formato(por_cobrar)}"
        )

    def _id_seleccionado(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Pendientes", "Selecciona un pendiente de la tabla.")
            return None
        return self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)

    def _agregar(self) -> None:
        if DialogoMovimiento(self.servicios, pendiente=True, parent=self).exec():
            self.refrescar()

    def _editar(self) -> None:
        id_ = self._id_seleccionado()
        if id_ is None:
            return
        movimiento = self.servicios.movimientos.obtener(id_)
        if DialogoMovimiento(self.servicios, movimiento=movimiento, parent=self).exec():
            self.refrescar()

    def _marcar_real(self) -> None:
        id_ = self._id_seleccionado()
        if id_ is None:
            return
        fecha = pedir_fecha(self)
        if fecha is None:
            return
        try:
            self.servicios.movimientos.marcar_real(id_, fecha)
        except ErrorFinanzas as error:
            QMessageBox.warning(self, "No se pudo marcar como real", str(error))
        self.refrescar()

    def _eliminar(self) -> None:
        id_ = self._id_seleccionado()
        if id_ is None:
            return
        if QMessageBox.question(self, "Eliminar pendiente", "¿Eliminar este pendiente?") != QMessageBox.StandardButton.Yes:
            return
        try:
            self.servicios.movimientos.eliminar(id_)
        except ErrorFinanzas as error:
            QMessageBox.warning(self, "No se pudo eliminar", str(error))
        self.refrescar()
