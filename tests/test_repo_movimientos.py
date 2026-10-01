from datetime import date

from finanzas.logica.modelos import EstadoMovimiento, Movimiento


def _agregar(repo, cat, monto, dia, desc="x", estado=EstadoMovimiento.REAL):
    return repo.agregar(
        Movimiento(
            descripcion=desc, monto=monto, categoria_id=cat.id,
            fecha_movimiento=date(2026, 9, dia) if dia else None, estado=estado,
        )
    )


def test_agregar_obtener_y_orden(servicios, cats):
    repo = servicios.movimientos.repo
    _agregar(repo, cats["pagos"], 1000, 20, "b")
    _agregar(repo, cats["sueldo"], 5000, 1, "a")
    lista = repo.listar()
    assert [m.descripcion for m in lista] == ["a", "b"]
    assert lista[0].tipo.value == "ingreso" and lista[0].categoria == "Sueldo"
    assert lista[0].fecha_captura  # se pone sola


def test_filtros_conteo_y_paginacion(servicios, cats):
    repo = servicios.movimientos.repo
    for dia in range(1, 11):
        _agregar(repo, cats["pagos"], 100 * dia, dia, f"pago {dia}")
    _agregar(repo, cats["sueldo"], 9000, 5, "sueldo")
    assert repo.contar() == 11
    assert repo.contar(tipo="gasto") == 10
    assert repo.contar(desde=date(2026, 9, 6)) == 5
    assert repo.contar(texto="sueldo") == 1
    pagina = repo.listar(limite=4, desplazamiento=4)
    assert len(pagina) == 4
    assert len(repo.listar()) == 11  # sin límite


def test_totales_ignoran_pendientes(servicios, cats):
    repo = servicios.movimientos.repo
    _agregar(repo, cats["sueldo"], 500000, 1)
    _agregar(repo, cats["pagos"], 150000, 2)
    _agregar(repo, cats["hormiga"], 3000, 3)
    _agregar(repo, cats["ahorro"], 27000, 4)
    _agregar(repo, cats["pagos"], 50000, None, "pendiente", EstadoMovimiento.PENDIENTE)
    totales = repo.totales_por_tipo(date(2026, 9, 1), date(2026, 9, 30))
    assert totales == {"ingreso": 500000, "gasto": 153000, "ahorro": 27000}
    assert repo.total_hormiga(date(2026, 9, 1), date(2026, 9, 30)) == 3000
    assert repo.saldo_antes_de(date(2026, 9, 3)) == 500000 - 150000
    assert repo.contar(estado="pendiente") == 1
