"""Acceso a la tabla de presupuesto mensual (lo planeado)."""
from __future__ import annotations

from finanzas.datos.base_datos import BaseDatos
from finanzas.logica.modelos import PresupuestoMes


class RepositorioPresupuesto:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    @staticmethod
    def _modelo(fila) -> PresupuestoMes:
        return PresupuestoMes(
            anio=fila["anio"],
            mes=fila["mes"],
            ingresos_planeados=fila["ingresos_planeados"],
            gastos_planeados=fila["gastos_planeados"],
            ahorro_planeado=fila["ahorro_planeado"],
        )

    def obtener(self, anio: int, mes: int) -> PresupuestoMes | None:
        fila = self.bd.consultar_uno(
            "SELECT * FROM presupuesto_mensual WHERE anio = ? AND mes = ?", (anio, mes)
        )
        return self._modelo(fila) if fila else None

    def guardar(self, p: PresupuestoMes) -> None:
        self.bd.ejecutar(
            "INSERT INTO presupuesto_mensual "
            "(anio, mes, ingresos_planeados, gastos_planeados, ahorro_planeado) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(anio, mes) DO UPDATE SET "
            "ingresos_planeados = excluded.ingresos_planeados, "
            "gastos_planeados = excluded.gastos_planeados, "
            "ahorro_planeado = excluded.ahorro_planeado",
            (p.anio, p.mes, p.ingresos_planeados, p.gastos_planeados, p.ahorro_planeado),
        )

    def listar_anio(self, anio: int) -> list[PresupuestoMes]:
        filas = self.bd.consultar(
            "SELECT * FROM presupuesto_mensual WHERE anio = ? ORDER BY mes", (anio,)
        )
        return [self._modelo(f) for f in filas]
