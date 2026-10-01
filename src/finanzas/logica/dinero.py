"""Un solo lugar para convertir y mostrar dinero (se guarda en centavos)."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


class Dinero:
    @staticmethod
    def a_centavos(pesos) -> int:
        """Convierte pesos (número o texto como "$1,500.50") a centavos enteros."""
        if isinstance(pesos, str):
            limpio = pesos.replace("$", "").replace(",", "").replace(" ", "")
            try:
                valor = Decimal(limpio)
            except InvalidOperation as error:
                raise ValueError(f"Cantidad no válida: {pesos!r}") from error
        else:
            valor = Decimal(str(pesos))
        return int((valor * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def a_pesos(centavos: int) -> Decimal:
        return (Decimal(centavos) / 100).quantize(Decimal("0.01"))

    @staticmethod
    def como_texto(centavos: int) -> str:
        """Texto plano sin símbolo ni comas, ej. "1500.00" (para celdas editables)."""
        return f"{Dinero.a_pesos(centavos):.2f}"

    @staticmethod
    def formato(centavos: int) -> str:
        """Texto para mostrar, ej. "$1,500.00" o "-$80.00"."""
        signo = "-" if centavos < 0 else ""
        pesos, cent = divmod(abs(centavos), 100)
        return f"{signo}${pesos:,}.{cent:02d}"
