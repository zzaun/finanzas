"""Lo planeado de cada mes (ingresos, gastos y ahorro)."""
from __future__ import annotations

from finanzas.datos.repo_presupuesto import RepositorioPresupuesto
from finanzas.excepciones import ErrorValidacion
from finanzas.logica.modelos import PresupuestoMes


class ServicioPresupuesto:
    def __init__(self, repo: RepositorioPresupuesto) -> None:
        self.repo = repo

    @staticmethod
    def _validar_mes(mes: int) -> None:
        if not 1 <= int(mes) <= 12:
            raise ErrorValidacion("El mes debe estar entre 1 y 12.")

    def obtener(self, anio: int, mes: int) -> PresupuestoMes:
        """Devuelve el presupuesto del mes (en ceros si todavía no se captura)."""
        self._validar_mes(mes)
        return self.repo.obtener(anio, mes) or PresupuestoMes(anio=anio, mes=mes)

    def guardar(self, anio: int, mes: int, ingresos: int, gastos: int, ahorro: int) -> PresupuestoMes:
        """Los montos van en centavos y no pueden ser negativos."""
        self._validar_mes(mes)
        if min(ingresos, gastos, ahorro) < 0:
            raise ErrorValidacion("Los montos planeados no pueden ser negativos.")
        presupuesto = PresupuestoMes(anio, mes, ingresos, gastos, ahorro)
        self.repo.guardar(presupuesto)
        return presupuesto

    def listar_anio(self, anio: int) -> list[PresupuestoMes]:
        """Los 12 meses del año, con ceros en los que no se han capturado."""
        guardados = {p.mes: p for p in self.repo.listar_anio(anio)}
        return [guardados.get(mes) or PresupuestoMes(anio=anio, mes=mes) for mes in range(1, 13)]

    def copiar_mes(self, origen: tuple[int, int], destino: tuple[int, int]) -> PresupuestoMes:
        base = self.obtener(*origen)
        return self.guardar(
            destino[0], destino[1],
            base.ingresos_planeados, base.gastos_planeados, base.ahorro_planeado,
        )
