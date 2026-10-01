from datetime import date

from finanzas.logica.modelos import TipoPeriodo


def _cargar(servicios, cats):
    m = servicios.movimientos
    m.agregar("Sueldo", 150000, cats["sueldo"].id, date(2026, 9, 1))
    m.agregar("Sueldo", 50000, cats["sueldo"].id, date(2026, 9, 20))
    m.agregar("Camión", 1700, cats["transporte"].id, date(2026, 9, 21))
    m.agregar("Pago", 35000, cats["pagos"].id, date(2026, 9, 21))
    m.agregar("Pizza", 5000, cats["hormiga"].id, date(2026, 9, 29))
    m.agregar("Ahorro", 27000, cats["ahorro"].id, date(2026, 9, 19))
    m.agregar("Sueldo octubre", 90000, cats["sueldo"].id, date(2026, 10, 1))


def test_resumen_mensual_usa_regla_unica_de_disponible(servicios, cats):
    _cargar(servicios, cats)
    r = servicios.resumen.resumen(TipoPeriodo.MES, date(2026, 9, 15))
    assert r.ingresos == 200000
    assert r.gastos == 41700
    assert r.ahorro == 27000
    assert r.hormiga == 5000
    assert r.disponible == 200000 - 41700 - 27000


def test_resumen_semanal(servicios, cats):
    _cargar(servicios, cats)
    r = servicios.resumen.resumen("semana", date(2026, 9, 23))  # lunes 21 a domingo 27
    assert (r.ingresos, r.gastos, r.ahorro) == (0, 36700, 0)
    servicios.resumen.configurar_inicio_semana("domingo")
    r = servicios.resumen.resumen("semana", date(2026, 9, 20))  # domingo 20 a sábado 26
    assert (r.ingresos, r.gastos) == (50000, 36700)


def test_comparativo_planeado_contra_real(servicios, cats):
    _cargar(servicios, cats)
    servicios.presupuesto.guardar(2026, 9, 250000, 160000, 10000)
    comp = servicios.resumen.comparativo_mes(2026, 9)
    lineas = {l.concepto: l for l in comp.lineas}
    assert lineas["Ingresos"].diferencia == 200000 - 250000
    assert lineas["Gastos"].diferencia == 41700 - 160000
    assert lineas["Disponible"].planeado == 250000 - 160000 - 10000
    assert lineas["Disponible"].real == 200000 - 41700 - 27000


def test_tabla_anual(servicios, cats):
    _cargar(servicios, cats)
    meses, total = servicios.resumen.tabla_anual(2026)
    assert len(meses) == 12
    assert meses[8].ingresos == 200000 and meses[9].ingresos == 90000
    assert total.ingresos == 290000 and total.gastos == 41700


def test_saldo_corrido(servicios, cats):
    _cargar(servicios, cats)
    movs = servicios.movimientos.listar(desde=date(2026, 9, 1), hasta=date(2026, 9, 30))
    filas = servicios.resumen.con_saldo_corrido(movs, servicios.resumen.saldo_inicial(date(2026, 9, 1)))
    assert filas[0][1] == 150000
    assert filas[-1][1] == 200000 - 41700 - 27000


def test_presupuesto_lista_12_meses(servicios):
    lista = servicios.presupuesto.listar_anio(2026)
    assert len(lista) == 12 and all(p.ingresos_planeados == 0 for p in lista)


def test_exportacion_csv_y_xlsx(servicios, cats, tmp_path):
    _cargar(servicios, cats)
    assert servicios.exportacion.exportar_movimientos(tmp_path / "m.csv") == 7
    assert servicios.exportacion.exportar_movimientos(tmp_path / "m.xlsx") == 7
    servicios.exportacion.exportar_resumen_anual(tmp_path / "a.csv", 2026)
    texto = (tmp_path / "a.csv").read_text(encoding="utf-8-sig")
    assert "Septiembre" in texto and "Total" in texto
