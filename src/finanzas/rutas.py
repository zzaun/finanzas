"""Ubicaciones de archivos y carpetas que usa el programa."""
from __future__ import annotations

from pathlib import Path

NOMBRE_APP = "finanzas"


class Rutas:
    """Dice dónde vive todo lo que el programa guarda en disco.

    Por defecto usa la carpeta de datos del usuario (en Linux:
    ``~/.local/share/finanzas``), nunca la carpeta del ejecutable.
    """

    def __init__(self, base: Path | str | None = None) -> None:
        if base is None:
            from platformdirs import user_data_dir

            base = user_data_dir(NOMBRE_APP)
        self.base = Path(base)

    @property
    def base_datos(self) -> Path:
        return self.base / "finanzas.db"

    @property
    def respaldos(self) -> Path:
        return self.base / "respaldos"

    @property
    def exportaciones(self) -> Path:
        return self.base / "exportaciones"

    def crear(self) -> None:
        """Crea las carpetas si todavía no existen."""
        for carpeta in (self.base, self.respaldos, self.exportaciones):
            carpeta.mkdir(parents=True, exist_ok=True)
