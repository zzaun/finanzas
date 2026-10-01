"""Clases simples que viajan entre las capas del programa (sin SQL ni ventanas)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class TipoMovimiento(str, Enum):
    INGRESO = "ingreso"
    GASTO = "gasto"
    AHORRO = "ahorro"


class EstadoMovimiento(str, Enum):
    REAL = "real"
    PENDIENTE = "pendiente"


class TipoPeriodo(str, Enum):
    SEMANA = "semana"
    MES = "mes"
    ANIO = "anio"


@dataclass
class Categoria:
    anio: int
    nombre: str
    tipo: TipoMovimiento
    es_hormiga: bool = False
    activa: bool = True
    id: int | None = None


@dataclass
class Movimiento:
    descripcion: str
    monto: int  # centavos, siempre positivo
    categoria_id: int
    fecha_movimiento: date | None = None
    estado: EstadoMovimiento = EstadoMovimiento.REAL
    es_anterior: bool = False
    notas: str | None = None
    id: int | None = None
    fecha_captura: str | None = None
    # Datos que llegan de la categoría cuando se lee de la base:
    categoria: str | None = None
    tipo: TipoMovimiento | None = None
    es_hormiga: bool = False

    @property
    def efecto(self) -> int:
        """Cómo mueve el saldo: + ingresos, - gastos y ahorro, 0 si es pendiente."""
        if self.estado is not EstadoMovimiento.REAL or self.tipo is None:
            return 0
        return self.monto if self.tipo is TipoMovimiento.INGRESO else -self.monto


@dataclass
class PresupuestoMes:
    anio: int
    mes: int
    ingresos_planeados: int = 0
    gastos_planeados: int = 0
    ahorro_planeado: int = 0

    @property
    def disponible_planeado(self) -> int:
        return self.ingresos_planeados - self.gastos_planeados - self.ahorro_planeado


@dataclass(frozen=True)
class Periodo:
    tipo: TipoPeriodo
    inicio: date
    fin: date
    etiqueta: str


@dataclass
class ResumenPeriodo:
    periodo: Periodo | None = None
    ingresos: int = 0
    gastos: int = 0
    ahorro: int = 0
    hormiga: int = 0  # parte de los gastos marcada como gasto hormiga

    @property
    def disponible(self) -> int:
        """Regla única: ingresos - gastos - ahorro."""
        return self.ingresos - self.gastos - self.ahorro


@dataclass
class LineaComparativo:
    concepto: str
    planeado: int
    real: int

    @property
    def diferencia(self) -> int:
        return self.real - self.planeado


@dataclass
class ComparativoMes:
    anio: int
    mes: int
    lineas: list[LineaComparativo] = field(default_factory=list)


@dataclass
class FilaCategoria:
    categoria: str
    tipo: TipoMovimiento
    total: int
    es_hormiga: bool = False
