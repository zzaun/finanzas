"""Reglas de negocio de los movimientos (ingresos, gastos y ahorro)."""
from __future__ import annotations

from datetime import date

from finanzas.datos.repo_categorias import RepositorioCategorias
from finanzas.datos.repo_movimientos import RepositorioMovimientos
from finanzas.excepciones import ErrorNoEncontrado, ErrorValidacion
from finanzas.logica.modelos import EstadoMovimiento, Movimiento

_CAMPOS_EDITABLES = {
    "descripcion", "monto", "categoria_id", "fecha_movimiento",
    "estado", "es_anterior", "notas",
}


class ServicioMovimientos:
    def __init__(self, repo: RepositorioMovimientos, repo_categorias: RepositorioCategorias) -> None:
        self.repo = repo
        self.repo_categorias = repo_categorias

    # ---- validación -------------------------------------------------
    def _validar(self, m: Movimiento, exigir_activa: bool) -> None:
        m.descripcion = (m.descripcion or "").strip()
        if not m.descripcion:
            raise ErrorValidacion("La descripción no puede estar vacía.")
        if len(m.descripcion) > 200:
            raise ErrorValidacion("La descripción es demasiado larga (máximo 200 caracteres).")
        if not isinstance(m.monto, int) or isinstance(m.monto, bool) or m.monto <= 0:
            raise ErrorValidacion("El monto debe ser mayor a cero.")
        categoria = self.repo_categorias.obtener(m.categoria_id) if m.categoria_id else None
        if categoria is None:
            raise ErrorValidacion("Elige una categoría.")
        if exigir_activa and not categoria.activa:
            raise ErrorValidacion(f"La categoría «{categoria.nombre}» está desactivada.")
        if m.estado is EstadoMovimiento.REAL and m.fecha_movimiento is None:
            raise ErrorValidacion("Un movimiento real necesita fecha.")
        if m.fecha_movimiento is not None and categoria.anio != m.fecha_movimiento.year:
            raise ErrorValidacion(
                f"La categoría «{categoria.nombre}» es de {categoria.anio}, "
                f"pero la fecha es de {m.fecha_movimiento.year}."
            )
        m.notas = (m.notas or "").strip() or None

    # ---- operaciones ------------------------------------------------
    def agregar(
        self,
        descripcion: str,
        monto: int,
        categoria_id: int,
        fecha_movimiento: date | None = None,
        estado: EstadoMovimiento | str = EstadoMovimiento.REAL,
        es_anterior: bool = False,
        notas: str | None = None,
    ) -> Movimiento:
        estado = EstadoMovimiento(estado)
        if fecha_movimiento is None and estado is EstadoMovimiento.REAL:
            fecha_movimiento = date.today()
        movimiento = Movimiento(
            descripcion=descripcion, monto=monto, categoria_id=categoria_id,
            fecha_movimiento=fecha_movimiento, estado=estado,
            es_anterior=bool(es_anterior), notas=notas,
        )
        self._validar(movimiento, exigir_activa=True)
        nuevo_id = self.repo.agregar(movimiento)
        return self.obtener(nuevo_id)

    def obtener(self, id_: int) -> Movimiento:
        movimiento = self.repo.obtener(id_)
        if movimiento is None:
            raise ErrorNoEncontrado("El movimiento no existe.")
        return movimiento

    def editar(self, id_: int, **cambios) -> Movimiento:
        desconocidos = set(cambios) - _CAMPOS_EDITABLES
        if desconocidos:
            raise ErrorValidacion(f"Campos no editables: {', '.join(sorted(desconocidos))}")
        movimiento = self.obtener(id_)
        categoria_anterior = movimiento.categoria_id
        for campo, valor in cambios.items():
            if campo == "estado":
                valor = EstadoMovimiento(valor)
            setattr(movimiento, campo, valor)
        self._validar(movimiento, exigir_activa=movimiento.categoria_id != categoria_anterior)
        self.repo.actualizar(movimiento)
        return self.obtener(id_)

    def marcar_real(self, id_: int, fecha: date | None = None) -> Movimiento:
        """Convierte un pendiente en real (por defecto con la fecha de hoy)."""
        return self.editar(
            id_, estado=EstadoMovimiento.REAL, fecha_movimiento=fecha or date.today()
        )

    def eliminar(self, id_: int) -> None:
        if not self.repo.eliminar(id_):
            raise ErrorNoEncontrado("El movimiento no existe.")

    def listar(self, **filtros) -> list[Movimiento]:
        """Filtros: desde, hasta, categoria_id, tipo, estado, texto, limite,
        desplazamiento, descendente."""
        return self.repo.listar(**filtros)

    def contar(self, **filtros) -> int:
        return self.repo.contar(**filtros)

    def pendientes(self) -> list[Movimiento]:
        return self.repo.listar(estado=EstadoMovimiento.PENDIENTE)
