from datetime import date

from finanzas.logica.periodos import CalculadoraPeriodos


def test_semana_inicia_en_lunes():
    p = CalculadoraPeriodos(0).obtener("semana", date(2026, 9, 30))  # miércoles
    assert (p.inicio, p.fin) == (date(2026, 9, 28), date(2026, 10, 4))


def test_semana_inicia_en_domingo():
    p = CalculadoraPeriodos(6).obtener("semana", date(2026, 9, 30))
    assert (p.inicio, p.fin) == (date(2026, 9, 27), date(2026, 10, 3))


def test_mes_y_anio():
    calc = CalculadoraPeriodos()
    mes = calc.obtener("mes", date(2026, 2, 10))
    assert (mes.inicio, mes.fin) == (date(2026, 2, 1), date(2026, 2, 28))
    assert mes.etiqueta == "Febrero 2026"
    anio = calc.obtener("anio", date(2026, 7, 4))
    assert (anio.inicio, anio.fin) == (date(2026, 1, 1), date(2026, 12, 31))


def test_anterior_y_siguiente():
    calc = CalculadoraPeriodos()
    mes = calc.obtener("mes", date(2026, 1, 15))
    assert calc.anterior(mes).inicio == date(2025, 12, 1)
    assert calc.siguiente(mes).inicio == date(2026, 2, 1)
    semana = calc.obtener("semana", date(2026, 9, 30))
    assert calc.siguiente(semana).inicio == date(2026, 10, 5)
    assert calc.anterior(semana).inicio == date(2026, 9, 21)
