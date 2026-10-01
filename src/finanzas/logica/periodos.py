"""Cálculo de semanas, meses y años."""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from finanzas.logica.modelos import Periodo, TipoPeriodo

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def nombre_mes(mes: int) -> str:
    return MESES[mes - 1].capitalize()


class CalculadoraPeriodos:
    """Dada una fecha, devuelve su semana, mes o año (y los vecinos).

    ``inicio_semana``: 0 = lunes ... 6 = domingo (igual que ``date.weekday()``).
    """

    def __init__(self, inicio_semana: int = 0) -> None:
        if not 0 <= inicio_semana <= 6:
            raise ValueError("inicio_semana debe estar entre 0 y 6")
        self.inicio_semana = inicio_semana

    def obtener(self, tipo: TipoPeriodo | str, referencia: date) -> Periodo:
        tipo = TipoPeriodo(tipo)
        if tipo is TipoPeriodo.SEMANA:
            retraso = (referencia.weekday() - self.inicio_semana) % 7
            inicio = referencia - timedelta(days=retraso)
            fin = inicio + timedelta(days=6)
            etiqueta = (
                f"Semana del {inicio.day} {MESES_CORTOS[inicio.month - 1]} "
                f"al {fin.day} {MESES_CORTOS[fin.month - 1]} {fin.year}"
            )
        elif tipo is TipoPeriodo.MES:
            inicio = date(referencia.year, referencia.month, 1)
            fin = date(referencia.year, referencia.month, calendar.monthrange(referencia.year, referencia.month)[1])
            etiqueta = f"{nombre_mes(referencia.month)} {referencia.year}"
        else:
            inicio = date(referencia.year, 1, 1)
            fin = date(referencia.year, 12, 31)
            etiqueta = str(referencia.year)
        return Periodo(tipo=tipo, inicio=inicio, fin=fin, etiqueta=etiqueta)

    def anterior(self, periodo: Periodo) -> Periodo:
        return self.obtener(periodo.tipo, periodo.inicio - timedelta(days=1))

    def siguiente(self, periodo: Periodo) -> Periodo:
        return self.obtener(periodo.tipo, periodo.fin + timedelta(days=1))
