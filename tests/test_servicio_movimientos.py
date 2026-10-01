from datetime import date

import pytest

from finanzas.excepciones import ErrorNoEncontrado, ErrorValidacion
from finanzas.logica.modelos import EstadoMovimiento


def test_agregar_sin_fecha_usa_hoy(servicios, cats):
    # La categoría debe ser del año de hoy; creamos una para ese año.
    hoy = date.today()
    cat = servicios.categorias.crear(hoy.year, "Prueba hoy", "gasto")
    m = servicios.movimientos.agregar("Café", 4500, cat.id)
    assert m.fecha_movimiento == hoy and m.estado is EstadoMovimiento.REAL


def test_categoria_de_otro_anio_se_rechaza(servicios, cats):
    with pytest.raises(ErrorValidacion):
        servicios.movimientos.agregar("Taxi", 5000, cats["transporte"].id, date(2027, 1, 5))


def test_validaciones_basicas(servicios, cats):
    f = date(2026, 9, 1)
    with pytest.raises(ErrorValidacion):
        servicios.movimientos.agregar("  ", 100, cats["pagos"].id, f)
    with pytest.raises(ErrorValidacion):
        servicios.movimientos.agregar("Algo", 0, cats["pagos"].id, f)
    with pytest.raises(ErrorValidacion):
        servicios.movimientos.agregar("Algo", 100, 9999, f)


def test_categoria_desactivada_no_se_puede_usar(servicios, cats):
    servicios.categorias.cambiar_activa(cats["pagos"].id, False)
    with pytest.raises(ErrorValidacion):
        servicios.movimientos.agregar("Algo", 100, cats["pagos"].id, date(2026, 9, 1))


def test_pendiente_sin_fecha_y_marcar_real(servicios, cats):
    m = servicios.movimientos.agregar(
        "Consola", 50000, cats["pagos"].id, estado="pendiente"
    )
    assert m.fecha_movimiento is None
    assert [x.id for x in servicios.movimientos.pendientes()] == [m.id]
    real = servicios.movimientos.marcar_real(m.id, date(2026, 9, 30))
    assert real.estado is EstadoMovimiento.REAL and real.fecha_movimiento == date(2026, 9, 30)
    assert servicios.movimientos.pendientes() == []


def test_real_sin_fecha_al_editar_falla(servicios, cats):
    m = servicios.movimientos.agregar("Taxi", 5000, cats["transporte"].id, date(2026, 9, 1))
    with pytest.raises(ErrorValidacion):
        servicios.movimientos.editar(m.id, fecha_movimiento=None)


def test_editar_y_eliminar(servicios, cats):
    m = servicios.movimientos.agregar("Taxi", 5000, cats["transporte"].id, date(2026, 9, 1))
    m2 = servicios.movimientos.editar(m.id, monto=7500, notas="  con propina ")
    assert m2.monto == 7500 and m2.notas == "con propina"
    servicios.movimientos.eliminar(m.id)
    with pytest.raises(ErrorNoEncontrado):
        servicios.movimientos.obtener(m.id)
    with pytest.raises(ErrorValidacion):
        servicios.movimientos.editar(m.id, campo_raro=1)


def test_categorias_copiar_y_duplicados(servicios, cats):
    with pytest.raises(ErrorValidacion):
        servicios.categorias.crear(2026, "sueldo", "ingreso")  # mismo nombre, otra mayúscula
    copiadas = servicios.categorias.copiar_anio(2026, 2027)
    assert copiadas == 6
    assert len(servicios.categorias.listar(2027)) == 6
