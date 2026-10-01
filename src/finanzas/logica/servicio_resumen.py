"""Cálculos de reportes: semana, mes, año y planeado contra real."""
from __future__ import annotations

from datetime import date

from finanzas.datos.repo_configuracion import RepositorioConfiguracion
from finanzas.datos.repo_movimientos import RepositorioMovimientos
from finanzas.datos.repo_presupuesto import RepositorioPresupuesto
from finanzas.excepciones import ErrorValidacion
from finanzas.logica.modelos import (
    ComparativoMes,
    FilaCategoria,
    LineaComparativo,
    Movimiento,
    Periodo,
    PresupuestoMes,
    ResumenPeriodo,
    TipoPeriodo,
)
from finanzas.logica.periodos import DIAS, CalculadoraPeriodos


class ServicioResumen:
    def __init__(
        self,
        repo_movimientos: RepositorioMovimientos,
        repo_presupuesto: RepositorioPresupuesto,
        repo_configuracion: RepositorioConfiguracion,
    ) -> None:
        self.repo_movimientos = repo_movimientos
        self.repo_presupuesto = repo_presupuesto
        self.repo_configuracion = repo_configuracion

    # ---- configuración de semana -------------------------------------
    def inicio_semana_nombre(self) -> str:
        nombre = self.repo_configuracion.obtener("inicio_semana", "lunes")
        return nombre if nombre in DIAS else "lunes"

    def configurar_inicio_semana(self, nombre: str) -> None:
        if nombre not in DIAS:
            raise ErrorValidacion("Día no válido para iniciar la semana.")
        self.repo_configuracion.guardar("inicio_semana", nombre)

    def calculadora(self) -> CalculadoraPeriodos:
        return CalculadoraPeriodos(DIAS.index(self.inicio_semana_nombre()))

    # ---- periodos ----------------------------------------------------
    def periodo(self, tipo: TipoPeriodo | str, referencia: date | None = None) -> Periodo:
        return self.calculadora().obtener(tipo, referencia or date.today())

    def periodo_anterior(self, periodo: Periodo) -> Periodo:
        return self.calculadora().anterior(periodo)

    def periodo_siguiente(self, periodo: Periodo) -> Periodo:
        return self.calculadora().siguiente(periodo)

    # ---- resúmenes ---------------------------------------------------
    def resumen_rango(self, desde: date, hasta: date, periodo: Periodo | None = None) -> ResumenPeriodo:
        totales = self.repo_movimientos.totales_por_tipo(desde, hasta)
        return ResumenPeriodo(
            periodo=periodo,
            ingresos=totales["ingreso"],
            gastos=totales["gasto"],
            ahorro=totales["ahorro"],
            hormiga=self.repo_movimientos.total_hormiga(desde, hasta),
        )

    def resumen_periodo(self, periodo: Periodo) -> ResumenPeriodo:
        return self.resumen_rango(periodo.inicio, periodo.fin, periodo)

    def resumen(self, tipo: TipoPeriodo | str, referencia: date | None = None) -> ResumenPeriodo:
        return self.resumen_periodo(self.periodo(tipo, referencia))

    def desglose_categorias(self, periodo: Periodo, tipo=None) -> list[FilaCategoria]:
        return self.repo_movimientos.totales_por_categoria(periodo.inicio, periodo.fin, tipo)

    def comparativo_mes(self, anio: int, mes: int) -> ComparativoMes:
        """Planeado, real y diferencia (real - planeado) de un mes."""
        periodo = self.periodo(TipoPeriodo.MES, date(anio, mes, 1))
        real = self.resumen_periodo(periodo)
        plan = self.repo_presupuesto.obtener(anio, mes) or PresupuestoMes(anio=anio, mes=mes)
        return ComparativoMes(
            anio=anio,
            mes=mes,
            lineas=[
                LineaComparativo("Ingresos", plan.ingresos_planeados, real.ingresos),
                LineaComparativo("Gastos", plan.gastos_planeados, real.gastos),
                LineaComparativo("Ahorro", plan.ahorro_planeado, real.ahorro),
                LineaComparativo("Disponible", plan.disponible_planeado, real.disponible),
            ],
        )

    def tabla_anual(self, anio: int) -> tuple[list[ResumenPeriodo], ResumenPeriodo]:
        """Un resumen por cada mes del año y el total del año."""
        meses = [self.resumen(TipoPeriodo.MES, date(anio, mes, 1)) for mes in range(1, 13)]
        total = ResumenPeriodo(
            periodo=self.periodo(TipoPeriodo.ANIO, date(anio, 1, 1)),
            ingresos=sum(m.ingresos for m in meses),
            gastos=sum(m.gastos for m in meses),
            ahorro=sum(m.ahorro for m in meses),
            hormiga=sum(m.hormiga for m in meses),
        )
        return meses, total

    # ---- saldo corrido -----------------------------------------------
    def saldo_inicial(self, fecha: date) -> int:
        """Saldo acumulado de todo lo real anterior a ``fecha``."""
        return self.repo_movimientos.saldo_antes_de(fecha)

    @staticmethod
    def con_saldo_corrido(
        movimientos: list[Movimiento], saldo_inicial: int = 0
    ) -> list[tuple[Movimiento, int | None]]:
        """Empareja cada movimiento con el saldo después de aplicarlo.

        Los pendientes no mueven el saldo y llevan ``None``.
        """
        saldo = saldo_inicial
        filas: list[tuple[Movimiento, int | None]] = []
        for movimiento in movimientos:
            saldo += movimiento.efecto
            filas.append((movimiento, saldo if movimiento.efecto else None))
        return filas
