"""Acceso a la tabla de configuración."""
from __future__ import annotations

from finanzas.datos.base_datos import BaseDatos


class RepositorioConfiguracion:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def obtener(self, clave: str, defecto: str | None = None) -> str | None:
        fila = self.bd.consultar_uno("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
        return fila["valor"] if fila else defecto

    def guardar(self, clave: str, valor: str) -> None:
        self.bd.ejecutar(
            "INSERT INTO configuracion (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (clave, valor),
        )

    def todas(self) -> dict[str, str]:
        return {f["clave"]: f["valor"] for f in self.bd.consultar("SELECT clave, valor FROM configuracion")}
