"""Ventana principal: pestañas y menús."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTabWidget

from finanzas.contenedor import Servicios
from finanzas.datos.respaldos import GestorRespaldos
from finanzas.excepciones import ErrorFinanzas
from finanzas.interfaz.vista_categorias import VistaCategorias
from finanzas.interfaz.vista_comparativo import VistaComparativo
from finanzas.interfaz.vista_movimientos import VistaMovimientos
from finanzas.interfaz.vista_pendientes import VistaPendientes
from finanzas.interfaz.vista_presupuesto import VistaPresupuesto
from finanzas.interfaz.vista_resumen import VistaResumen
from finanzas.rutas import Rutas

FILTRO_ARCHIVOS = "Excel (*.xlsx);;CSV (*.csv)"


class VentanaPrincipal(QMainWindow):
    def __init__(self, servicios: Servicios, respaldos: GestorRespaldos, rutas: Rutas) -> None:
        super().__init__()
        self.servicios = servicios
        self.respaldos = respaldos
        self.rutas = rutas
        self.setWindowTitle("Finanzas")
        self.resize(1150, 740)

        self.pestanas = QTabWidget()
        for titulo, clase in (
            ("Movimientos", VistaMovimientos),
            ("Resumen", VistaResumen),
            ("Planeado vs real", VistaComparativo),
            ("Presupuesto", VistaPresupuesto),
            ("Categorías", VistaCategorias),
            ("Pendientes", VistaPendientes),
        ):
            self.pestanas.addTab(clase(servicios), titulo)
        self.setCentralWidget(self.pestanas)
        self.pestanas.currentChanged.connect(self._refrescar_actual)

        self._crear_menus()
        self._refrescar_actual()

    # ---- menús --------------------------------------------------------------
    def _accion(self, texto: str, funcion, checkable: bool = False) -> QAction:
        accion = QAction(texto, self)
        accion.setCheckable(checkable)
        accion.triggered.connect(lambda *_: funcion())
        return accion

    def _crear_menus(self) -> None:
        archivo = self.menuBar().addMenu("&Archivo")
        archivo.addAction(self._accion("Exportar movimientos…", self._exportar_movimientos))
        archivo.addAction(self._accion("Exportar resumen del año…", self._exportar_resumen))
        archivo.addSeparator()
        archivo.addAction(self._accion("Crear respaldo ahora", self._crear_respaldo))
        archivo.addAction(self._accion("Restaurar respaldo…", self._restaurar_respaldo))
        archivo.addSeparator()
        archivo.addAction(self._accion("Salir", self.close))

        configuracion = self.menuBar().addMenu("&Configuración")
        grupo = QActionGroup(self)
        grupo.setExclusive(True)
        actual = self.servicios.resumen.inicio_semana_nombre()
        for nombre in ("lunes", "domingo"):
            accion = self._accion(
                f"La semana empieza en {nombre}", lambda n=nombre: self._cambiar_inicio_semana(n), checkable=True
            )
            accion.setChecked(nombre == actual)
            grupo.addAction(accion)
            configuracion.addAction(accion)

    def _refrescar_actual(self, *_) -> None:
        vista = self.pestanas.currentWidget()
        if vista is not None:
            vista.refrescar()

    def _cambiar_inicio_semana(self, nombre: str) -> None:
        self.servicios.resumen.configurar_inicio_semana(nombre)
        self._refrescar_actual()

    # ---- exportación ------------------------------------------------------------
    def _pedir_ruta(self, titulo: str, nombre_sugerido: str) -> Path | None:
        ruta, filtro = QFileDialog.getSaveFileName(
            self, titulo, str(self.rutas.exportaciones / nombre_sugerido), FILTRO_ARCHIVOS
        )
        if not ruta:
            return None
        destino = Path(ruta)
        if destino.suffix.lower() not in (".csv", ".xlsx"):
            destino = destino.with_suffix(".csv" if "csv" in filtro.lower() else ".xlsx")
        return destino

    def _exportar_movimientos(self) -> None:
        destino = self._pedir_ruta("Exportar movimientos", "movimientos.xlsx")
        if destino is None:
            return
        try:
            cantidad = self.servicios.exportacion.exportar_movimientos(destino)
        except (ErrorFinanzas, OSError) as error:
            QMessageBox.warning(self, "No se pudo exportar", str(error))
            return
        QMessageBox.information(self, "Exportación lista", f"Se exportaron {cantidad} movimientos a:\n{destino}")

    def _exportar_resumen(self) -> None:
        anio = date.today().year
        destino = self._pedir_ruta("Exportar resumen del año", f"resumen_{anio}.xlsx")
        if destino is None:
            return
        try:
            self.servicios.exportacion.exportar_resumen_anual(destino, anio)
        except (ErrorFinanzas, OSError) as error:
            QMessageBox.warning(self, "No se pudo exportar", str(error))
            return
        QMessageBox.information(self, "Exportación lista", f"Resumen de {anio} guardado en:\n{destino}")

    # ---- respaldos -----------------------------------------------------------------
    def _crear_respaldo(self) -> None:
        try:
            ruta = self.respaldos.crear()
        except OSError as error:
            QMessageBox.warning(self, "No se pudo crear el respaldo", str(error))
            return
        QMessageBox.information(self, "Respaldo creado", f"Respaldo guardado en:\n{ruta}")

    def _restaurar_respaldo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir respaldo", str(self.rutas.respaldos), "Base de datos (*.db)"
        )
        if not ruta:
            return
        respuesta = QMessageBox.question(
            self, "Restaurar respaldo",
            "Se reemplazarán los datos actuales por los del respaldo.\n"
            "Antes se guardará una copia de lo que tienes ahora. ¿Continuar?",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        try:
            self.respaldos.restaurar(ruta)
        except ErrorFinanzas as error:
            QMessageBox.warning(self, "No se pudo restaurar", str(error))
            return
        self._refrescar_actual()
        QMessageBox.information(self, "Respaldo restaurado", "Los datos se restauraron correctamente.")
