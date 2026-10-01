import pytest

from finanzas.app import Aplicacion
from finanzas.rutas import Rutas


@pytest.fixture
def app(tmp_path):
    aplicacion = Aplicacion(Rutas(tmp_path), preparar=False)
    yield aplicacion
    aplicacion.cerrar()


@pytest.fixture
def servicios(app):
    return app.servicios


@pytest.fixture
def cats(servicios):
    """Categorías de 2026 listas para usar en las pruebas."""
    c = servicios.categorias
    return {
        "sueldo": c.crear(2026, "Sueldo", "ingreso"),
        "extras": c.crear(2026, "Extras", "ingreso"),
        "transporte": c.crear(2026, "Transporte", "gasto"),
        "pagos": c.crear(2026, "Pagos", "gasto"),
        "hormiga": c.crear(2026, "Gasto hormiga", "gasto", es_hormiga=True),
        "ahorro": c.crear(2026, "Ahorro", "ahorro"),
    }
