"""Formulario para capturar o editar un movimiento."""
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
)

from finanzas.contenedor import Servicios
from finanzas.excepciones import ErrorFinanzas, ErrorValidacion
from finanzas.logica.dinero import Dinero
from finanzas.logica.modelos import EstadoMovimiento, Movimiento, TipoMovimiento


class DialogoMovimiento(QDialog):
    """Si recibe un ``movimiento`` lo edita; si no, crea uno nuevo.

    ``pendiente=True`` abre el formulario con "Pendiente" ya marcado.
    """

    def __init__(
        self,
        servicios: Servicios,
        movimiento: Movimiento | None = None,
        pendiente: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.servicios = servicios
        self.movimiento = movimiento
        self.setWindowTitle("Editar movimiento" if movimiento else "Nuevo movimiento")
        self.setMinimumWidth(440)

        self.txt_descripcion = QLineEdit()
        self.cmb_tipo = QComboBox()
        for tipo in TipoMovimiento:
            self.cmb_tipo.addItem(tipo.value.capitalize(), tipo.value)
        self.cmb_categoria = QComboBox()
        self.spn_monto = QDoubleSpinBox()
        self.spn_monto.setPrefix("$ ")
        self.spn_monto.setDecimals(2)
        self.spn_monto.setRange(0.01, 999_999_999.99)
        self.spn_monto.setGroupSeparatorShown(True)
        self.fecha = QDateEdit(QDate.currentDate())
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy")
        self.chk_pendiente = QCheckBox("Pendiente (todavía sin fecha)")
        self.chk_anterior = QCheckBox("Es de un periodo anterior")
        self.txt_notas = QPlainTextEdit()
        self.txt_notas.setMaximumHeight(70)

        formulario = QFormLayout(self)
        formulario.addRow("Descripción:", self.txt_descripcion)
        formulario.addRow("Tipo:", self.cmb_tipo)
        formulario.addRow("Categoría:", self.cmb_categoria)
        formulario.addRow("Monto:", self.spn_monto)
        formulario.addRow("Fecha:", self.fecha)
        formulario.addRow("", self.chk_pendiente)
        formulario.addRow("", self.chk_anterior)
        formulario.addRow("Notas:", self.txt_notas)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        formulario.addRow(botones)

        if movimiento is not None:
            self._llenar(movimiento)
        else:
            self.chk_pendiente.setChecked(pendiente)
            self.fecha.setEnabled(not pendiente)
        self._cargar_categorias()

        self.cmb_tipo.currentIndexChanged.connect(self._cargar_categorias)
        self.fecha.dateChanged.connect(self._cargar_categorias)
        self.chk_pendiente.toggled.connect(self._al_cambiar_pendiente)

    # ---- apoyo -------------------------------------------------------
    def _llenar(self, m: Movimiento) -> None:
        self.txt_descripcion.setText(m.descripcion)
        self.cmb_tipo.setCurrentIndex(self.cmb_tipo.findData(m.tipo.value))
        self.spn_monto.setValue(float(Dinero.a_pesos(m.monto)))
        if m.fecha_movimiento:
            self.fecha.setDate(QDate(m.fecha_movimiento.year, m.fecha_movimiento.month, m.fecha_movimiento.day))
        pendiente = m.estado is EstadoMovimiento.PENDIENTE and m.fecha_movimiento is None
        self.chk_pendiente.setChecked(pendiente)
        self.fecha.setEnabled(not pendiente)
        self.chk_anterior.setChecked(m.es_anterior)
        self.txt_notas.setPlainText(m.notas or "")

    def _al_cambiar_pendiente(self, marcado: bool) -> None:
        self.fecha.setEnabled(not marcado)
        self._cargar_categorias()

    def _cargar_categorias(self, *_) -> None:
        """Lista las categorías del año de la fecha y del tipo elegido."""
        anio = QDate.currentDate().year() if self.chk_pendiente.isChecked() else self.fecha.date().year()
        actual = self.cmb_categoria.currentData()
        if actual is None and self.movimiento is not None:
            actual = self.movimiento.categoria_id
        categorias = self.servicios.categorias.listar(
            anio, tipo=self.cmb_tipo.currentData(), solo_activas=False
        )
        self.cmb_categoria.clear()
        for categoria in categorias:
            es_la_actual = self.movimiento is not None and categoria.id == self.movimiento.categoria_id
            if categoria.activa or es_la_actual:
                self.cmb_categoria.addItem(categoria.nombre, categoria.id)
        posicion = self.cmb_categoria.findData(actual)
        if posicion >= 0:
            self.cmb_categoria.setCurrentIndex(posicion)

    # ---- guardar -------------------------------------------------------
    def accept(self) -> None:
        pendiente = self.chk_pendiente.isChecked()
        try:
            if self.cmb_categoria.currentData() is None:
                raise ErrorValidacion(
                    "No hay categorías para ese tipo y año. Créalas primero en la pestaña Categorías."
                )
            datos = dict(
                descripcion=self.txt_descripcion.text(),
                monto=Dinero.a_centavos(self.spn_monto.value()),
                categoria_id=self.cmb_categoria.currentData(),
                estado=EstadoMovimiento.PENDIENTE if pendiente else EstadoMovimiento.REAL,
                fecha_movimiento=None if pendiente else self.fecha.date().toPython(),
                es_anterior=self.chk_anterior.isChecked(),
                notas=self.txt_notas.toPlainText(),
            )
            if self.movimiento is not None:
                self.servicios.movimientos.editar(self.movimiento.id, **datos)
            else:
                self.servicios.movimientos.agregar(**datos)
        except ErrorFinanzas as error:
            QMessageBox.warning(self, "No se pudo guardar", str(error))
            return
        super().accept()
