"""Errores propios del programa."""
from __future__ import annotations


class ErrorFinanzas(Exception):
    """Base de todos los errores del programa."""


class ErrorValidacion(ErrorFinanzas):
    """Datos que no cumplen una regla; el mensaje se muestra al usuario."""


class ErrorNoEncontrado(ErrorFinanzas):
    """Se pidió algo que no existe en la base."""
