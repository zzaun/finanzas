"""Arma todas las piezas del programa y lo pone en marcha."""
from __future__ import annotations

import sys
from datetime import date

from finanzas.contenedor import Servicios
from finanzas.datos.base_datos import BaseDatos
from finanzas.datos.esquema import Esquema
from finanzas.datos.repo_categorias import RepositorioCategorias
from finanzas.datos.repo_configuracion import RepositorioConfiguracion
from finanzas.datos.repo_movimientos import RepositorioMovimientos
from finanzas.datos.repo_presupuesto import RepositorioPresupuesto
from finanzas.datos.respaldos import GestorRespaldos
from finanzas.logica.servicio_categorias import ServicioCategorias
from finanzas.logica.servicio_exportacion import ServicioExportacion
from finanzas.logica.servicio_movimientos import ServicioMovimientos
from finanzas.logica.servicio_presupuesto import ServicioPresupuesto
from finanzas.logica.servicio_resumen import ServicioResumen
from finanzas.rutas import Rutas


class Aplicacion:
    """Crea la base, los repositorios y los servicios, y se los pasa a la ventana.

    ``preparar=False`` se usa en las pruebas: no crea categorías iniciales ni
    respaldos automáticos.
    """

    def __init__(self, rutas: Rutas | None = None, preparar: bool = True) -> None:
        self.rutas = rutas or Rutas()
        self.rutas.crear()

        self.bd = BaseDatos(self.rutas.base_datos)
        self.bd.conectar()
        Esquema(self.bd).aplicar()

        repo_categorias = RepositorioCategorias(self.bd)
        repo_movimientos = RepositorioMovimientos(self.bd)
        repo_presupuesto = RepositorioPresupuesto(self.bd)
        repo_configuracion = RepositorioConfiguracion(self.bd)

        movimientos = ServicioMovimientos(repo_movimientos, repo_categorias)
        resumen = ServicioResumen(repo_movimientos, repo_presupuesto, repo_configuracion)
        self.servicios = Servicios(
            categorias=ServicioCategorias(repo_categorias),
            movimientos=movimientos,
            presupuesto=ServicioPresupuesto(repo_presupuesto),
            resumen=resumen,
            exportacion=ServicioExportacion(movimientos, resumen),
        )
        self.respaldos = GestorRespaldos(self.bd, self.rutas)

        if preparar:
            self.servicios.categorias.asegurar_anio(date.today().year)
            self.respaldos.respaldo_automatico()

    def ejecutar(self) -> int:
        """Abre la ventana y devuelve el código de salida."""
        from PySide6.QtWidgets import QApplication

        from finanzas.interfaz.estilos import Estilos
        from finanzas.interfaz.ventana_principal import VentanaPrincipal

        qt = QApplication.instance() or QApplication(sys.argv)
        qt.setApplicationName("Finanzas")
        Estilos.aplicar(qt)
        ventana = VentanaPrincipal(self.servicios, self.respaldos, self.rutas)
        ventana.show()
        try:
            return qt.exec()
        finally:
            self.cerrar()

    def cerrar(self) -> None:
        self.bd.cerrar()
