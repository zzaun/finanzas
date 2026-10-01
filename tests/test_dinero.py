import pytest

from finanzas.logica.dinero import Dinero


def test_a_centavos_acepta_numeros_y_texto():
    assert Dinero.a_centavos(150.5) == 15050
    assert Dinero.a_centavos("$1,500.50") == 150050
    assert Dinero.a_centavos(20) == 2000


def test_a_centavos_redondea_hacia_arriba_la_mitad():
    assert Dinero.a_centavos("0.005") == 1


def test_a_centavos_rechaza_texto_invalido():
    with pytest.raises(ValueError):
        Dinero.a_centavos("abc")


def test_formato():
    assert Dinero.formato(150000) == "$1,500.00"
    assert Dinero.formato(-8000) == "-$80.00"
    assert Dinero.formato(5) == "$0.05"


def test_como_texto():
    assert Dinero.como_texto(150000) == "1500.00"
