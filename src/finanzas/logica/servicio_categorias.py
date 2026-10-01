"""Reglas para crear y administrar categorías (que son por año)."""
from __future__ import annotations

from finanzas.datos.repo_categorias import RepositorioCategorias
from finanzas.excepciones import ErrorNoEncontrado, ErrorValidacion
from finanzas.logica.modelos import Categoria, TipoMovimiento

# (nombre, tipo, es_hormiga) — categorías iniciales, editables después.
CATEGORIAS_BASE = [
    ("Sueldo", "ingreso", False),
    ("Extras", "ingreso", False),
    ("Transporte", "gasto", False),
    ("Entretenimiento", "gasto", False),
    ("Pagos", "gasto", False),
    ("Gastos generales", "gasto", False),
    ("Gasto hormiga", "gasto", True),
    ("Ahorro", "ahorro", False),
]


class ServicioCategorias:
    def __init__(self, repo: RepositorioCategorias) -> None:
        self.repo = repo

    @staticmethod
    def _tipo(tipo) -> TipoMovimiento:
        try:
            return TipoMovimiento(tipo)
        except ValueError as error:
            raise ErrorValidacion("El tipo debe ser ingreso, gasto o ahorro.") from error

    @staticmethod
    def _anio(anio: int) -> int:
        if not 2000 <= int(anio) <= 2100:
            raise ErrorValidacion("El año debe estar entre 2000 y 2100.")
        return int(anio)

    @staticmethod
    def _nombre(nombre: str) -> str:
        nombre = (nombre or "").strip()
        if not nombre:
            raise ErrorValidacion("El nombre de la categoría no puede estar vacío.")
        if len(nombre) > 60:
            raise ErrorValidacion("El nombre es demasiado largo (máximo 60 caracteres).")
        return nombre

    def crear(self, anio: int, nombre: str, tipo, es_hormiga: bool = False) -> Categoria:
        anio, nombre, tipo = self._anio(anio), self._nombre(nombre), self._tipo(tipo)
        if self.repo.buscar(anio, nombre, tipo):
            raise ErrorValidacion(f"Ya existe «{nombre}» como {tipo.value} en {anio}.")
        categoria = Categoria(
            anio=anio, nombre=nombre, tipo=tipo,
            es_hormiga=bool(es_hormiga) and tipo is TipoMovimiento.GASTO,
        )
        categoria.id = self.repo.agregar(categoria)
        return categoria

    def obtener(self, id_: int) -> Categoria:
        categoria = self.repo.obtener(id_)
        if categoria is None:
            raise ErrorNoEncontrado("La categoría no existe.")
        return categoria

    def renombrar(self, id_: int, nombre: str) -> Categoria:
        categoria = self.obtener(id_)
        nombre = self._nombre(nombre)
        otra = self.repo.buscar(categoria.anio, nombre, categoria.tipo)
        if otra and otra.id != categoria.id:
            raise ErrorValidacion(f"Ya existe «{nombre}» como {categoria.tipo.value} en {categoria.anio}.")
        categoria.nombre = nombre
        self.repo.actualizar(categoria)
        return categoria

    def cambiar_activa(self, id_: int, activa: bool) -> Categoria:
        categoria = self.obtener(id_)
        categoria.activa = bool(activa)
        self.repo.actualizar(categoria)
        return categoria

    def listar(self, anio: int, tipo=None, solo_activas: bool = True) -> list[Categoria]:
        return self.repo.listar(anio, self._tipo(tipo) if tipo else None, solo_activas)

    def copiar_anio(self, origen: int, destino: int) -> int:
        origen, destino = self._anio(origen), self._anio(destino)
        if origen == destino:
            raise ErrorValidacion("El año de origen y el de destino son el mismo.")
        return self.repo.copiar_anio(origen, destino)

    def crear_basicas(self, anio: int) -> None:
        for nombre, tipo, hormiga in CATEGORIAS_BASE:
            self.crear(anio, nombre, tipo, hormiga)

    def asegurar_anio(self, anio: int) -> None:
        """Si el año no tiene categorías, copia las del año anterior o crea las básicas."""
        if self.repo.contar_anio(anio) > 0:
            return
        if self.repo.contar_anio(anio - 1) > 0:
            self.repo.copiar_anio(anio - 1, anio)
        else:
            self.crear_basicas(anio)
