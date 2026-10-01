"""Exportación de datos a CSV o Excel (como respaldo legible)."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from finanzas.excepciones import ErrorValidacion
from finanzas.logica.dinero import Dinero
from finanzas.logica.periodos import nombre_mes
from finanzas.logica.servicio_movimientos import ServicioMovimientos
from finanzas.logica.servicio_resumen import ServicioResumen


class ServicioExportacion:
    def __init__(self, movimientos: ServicioMovimientos, resumen: ServicioResumen) -> None:
        self.movimientos = movimientos
        self.resumen = resumen

    def exportar_movimientos(
        self, ruta: Path | str, desde: date | None = None, hasta: date | None = None
    ) -> int:
        """Escribe los movimientos a ``.csv`` o ``.xlsx`` (según la extensión).

        Devuelve cuántos movimientos exportó.
        """
        movimientos = self.movimientos.listar(desde=desde, hasta=hasta)
        encabezados = [
            "ID", "Fecha", "Descripción", "Categoría", "Tipo", "Monto",
            "Estado", "Anterior", "Notas", "Fecha de captura",
        ]
        filas = [
            [
                m.id,
                m.fecha_movimiento.isoformat() if m.fecha_movimiento else "",
                m.descripcion,
                m.categoria,
                m.tipo.value if m.tipo else "",
                Dinero.a_pesos(m.monto),
                m.estado.value,
                "sí" if m.es_anterior else "no",
                m.notas or "",
                m.fecha_captura or "",
            ]
            for m in movimientos
        ]
        self._escribir(Path(ruta), "Movimientos", encabezados, filas)
        return len(filas)

    def exportar_resumen_anual(self, ruta: Path | str, anio: int) -> None:
        meses, total = self.resumen.tabla_anual(anio)
        filas = [
            [nombre_mes(i + 1), Dinero.a_pesos(r.ingresos), Dinero.a_pesos(r.gastos),
             Dinero.a_pesos(r.ahorro), Dinero.a_pesos(r.disponible)]
            for i, r in enumerate(meses)
        ]
        filas.append(
            ["Total", Dinero.a_pesos(total.ingresos), Dinero.a_pesos(total.gastos),
             Dinero.a_pesos(total.ahorro), Dinero.a_pesos(total.disponible)]
        )
        self._escribir(Path(ruta), f"Resumen {anio}", ["Mes", "Ingresos", "Gastos", "Ahorro", "Disponible"], filas)

    @staticmethod
    def _escribir(ruta: Path, hoja: str, encabezados: list[str], filas: list[list]) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        extension = ruta.suffix.lower()
        if extension == ".csv":
            # utf-8-sig para que Excel/LibreOffice lean bien los acentos
            with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(encabezados)
                escritor.writerows(filas)
        elif extension == ".xlsx":
            from openpyxl import Workbook
            from openpyxl.styles import Font

            libro = Workbook()
            hoja_activa = libro.active
            hoja_activa.title = hoja
            hoja_activa.append(encabezados)
            for celda in hoja_activa[1]:
                celda.font = Font(bold=True)
            for fila in filas:
                hoja_activa.append([float(v) if hasattr(v, "as_tuple") else v for v in fila])
            libro.save(ruta)
        else:
            raise ErrorValidacion("Formato no soportado: usa .csv o .xlsx")
