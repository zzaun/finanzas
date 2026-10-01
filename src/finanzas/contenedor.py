"""Agrupa los servicios para pasarlos a la interfaz como un solo objeto."""
from __future__ import annotations

from dataclasses import dataclass

from finanzas.logica.servicio_categorias import ServicioCategorias
from finanzas.logica.servicio_exportacion import ServicioExportacion
from finanzas.logica.servicio_movimientos import ServicioMovimientos
from finanzas.logica.servicio_presupuesto import ServicioPresupuesto
from finanzas.logica.servicio_resumen import ServicioResumen


@dataclass
class Servicios:
    categorias: ServicioCategorias
    movimientos: ServicioMovimientos
    presupuesto: ServicioPresupuesto
    resumen: ServicioResumen
    exportacion: ServicioExportacion
