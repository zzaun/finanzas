"""Administración de categorías, que son por año."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from finanzas.contenedor import Servicios
from finanzas.excepciones import ErrorFinanzas
from finanzas.interfaz.estilos import celda, crear_tabla
from finanzas.logica.modelos import TipoMovimiento


class DialogoCategoria(QDialog):
    """Pide nombre, tipo y si es gasto hormiga."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nueva categoría")
        self.txt_nombre = QLineEdit()
        self.cmb_tipo = QComboBox()
        for tipo in TipoMovimiento:
            self.cmb_tipo.addItem(tipo.value.capitalize(), tipo.value)
        self.chk_hormiga = QCheckBox("Es gasto hormiga")
        self.cmb_tipo.currentIndexChanged.connect(self._al_cambiar_tipo)
        self._al_cambiar_tipo()

        formulario = QFormLayout(self)
        formulario.addRow("Nombre:", self.txt_nombre)
        formulario.addRow("Tipo:", self.cmb_tipo)
        formulario.addRow("", self.chk_hormiga)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        formulario.addRow(botones)

    def _al_cambiar_tipo(self, *_) -> None:
        es_gasto = self.cmb_tipo.currentData() == TipoMovimiento.GASTO.value
        self.chk_hormiga.setEnabled(es_gasto)
        if not es_gasto:
            self.chk_hormiga.setChecked(False)


class VistaCategorias(QWidget):
    def __init__(self, servicios: Servicios, parent=None) -> None:
        super().__init__(parent)
        self.servicios = servicios

        self.spn_anio = QSpinBox()
        self.spn_anio.setRange(2000, 2100)
        self.spn_anio.setValue(date.today().year)
        self.btn_agregar = QPushButton("Agregar categoría")
        self.btn_renombrar = QPushButton("Renombrar")
        self.btn_activar = QPushButton("Activar / desactivar")
        self.btn_copiar = QPushButton("Copiar del año anterior")

        barra = QHBoxLayout()
        barra.addWidget(QLabel("Año:"))
        barra.addWidget(self.spn_anio)
        barra.addWidget(self.btn_agregar)
        barra.addWidget(self.btn_renombrar)
        barra.addWidget(self.btn_activar)
        barra.addWidget(self.btn_copiar)
        barra.addStretch(1)

        self.tabla = crear_tabla(["Nombre", "Tipo", "Gasto hormiga", "Activa"])
        diseno = QVBoxLayout(self)
        diseno.addLayout(barra)
        diseno.addWidget(self.tabla, 1)

        self.spn_anio.valueChanged.connect(self.refrescar)
        self.btn_agregar.clicked.connect(self._agregar)
        self.btn_renombrar.clicked.connect(self._renombrar)
        self.btn_activar.clicked.connect(self._cambiar_activa)
        self.btn_copiar.clicked.connect(self._copiar)

    def refrescar(self, *_) -> None:
        categorias = self.servicios.categorias.listar(self.spn_anio.value(), solo_activas=False)
        self.tabla.setRowCount(len(categorias))
        for numero, c in enumerate(categorias):
            nombre = celda(c.nombre)
            nombre.setData(Qt.ItemDataRole.UserRole, c.id)
            self.tabla.setItem(numero, 0, nombre)
            self.tabla.setItem(numero, 1, celda(c.tipo.value.capitalize()))
            self.tabla.setItem(numero, 2, celda("Sí" if c.es_hormiga else ""))
            self.tabla.setItem(numero, 3, celda("Sí" if c.activa else "No"))

    def _id_seleccionado(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Categorías", "Selecciona una categoría de la tabla.")
            return None
        return self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)

    def _intentar(self, accion) -> None:
        try:
            accion()
        except ErrorFinanzas as error:
            QMessageBox.warning(self, "No se pudo completar", str(error))
        self.refrescar()

    def _agregar(self) -> None:
        dialogo = DialogoCategoria(self)
        if not dialogo.exec():
            return
        self._intentar(
            lambda: self.servicios.categorias.crear(
                self.spn_anio.value(),
                dialogo.txt_nombre.text(),
                dialogo.cmb_tipo.currentData(),
                dialogo.chk_hormiga.isChecked(),
            )
        )

    def _renombrar(self) -> None:
        id_ = self._id_seleccionado()
        if id_ is None:
            return
        actual = self.servicios.categorias.obtener(id_).nombre
        nombre, aceptado = QInputDialog.getText(self, "Renombrar categoría", "Nuevo nombre:", text=actual)
        if aceptado:
            self._intentar(lambda: self.servicios.categorias.renombrar(id_, nombre))

    def _cambiar_activa(self) -> None:
        id_ = self._id_seleccionado()
        if id_ is None:
            return
        activa = self.servicios.categorias.obtener(id_).activa
        self._intentar(lambda: self.servicios.categorias.cambiar_activa(id_, not activa))

    def _copiar(self) -> None:
        destino = self.spn_anio.value()
        origen = destino - 1

        def copiar() -> None:
            creadas = self.servicios.categorias.copiar_anio(origen, destino)
            QMessageBox.information(
                self, "Copiar categorías",
                f"Se copiaron {creadas} categorías de {origen} a {destino}."
                if creadas else f"No había categorías nuevas que copiar de {origen}.",
            )

        self._intentar(copiar)
