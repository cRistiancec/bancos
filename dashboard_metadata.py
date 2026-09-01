"""Resumen estable de la metadata publicada para la portada."""

from __future__ import annotations

from datetime import datetime
from typing import Any


MESES_LARGOS = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
MESES_CORTOS = (
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
)


def _fecha(valor: Any) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def resumir_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Calcula las cifras visibles sin mantener fechas o bancos hardcodeados."""
    metadata = metadata or {}
    fecha_min = _fecha(metadata.get("fecha_min"))
    fecha_max = _fecha(metadata.get("fecha_max"))

    meses = None
    if fecha_min and fecha_max and fecha_max >= fecha_min:
        meses = (
            (fecha_max.year - fecha_min.year) * 12
            + fecha_max.month
            - fecha_min.month
            + 1
        )

    bancos = metadata.get("total_bancos")
    try:
        bancos = int(bancos)
    except (TypeError, ValueError):
        bancos = None

    registros = metadata.get("total_registros")
    try:
        registros = int(registros)
    except (TypeError, ValueError):
        registros = None

    return {
        "bancos": bancos if bancos is not None else "N/D",
        "meses": meses if meses is not None else "N/D",
        "anos": max(0, (meses - 1) // 12) if meses is not None else "N/D",
        "datos_al": (
            f"{MESES_CORTOS[fecha_max.month - 1]} {fecha_max.year}"
            if fecha_max else "N/D"
        ),
        "periodo": (
            f"{MESES_LARGOS[fecha_min.month - 1]} {fecha_min.year} - "
            f"{MESES_LARGOS[fecha_max.month - 1]} {fecha_max.year}"
            if fecha_min and fecha_max else "N/D"
        ),
        "registros": (
            f"{registros / 1_000_000:.1f}".replace(".", ",") + " millones"
            if registros is not None else "N/D"
        ),
        "completa": bool(
            fecha_min and fecha_max and bancos is not None and meses is not None
        ),
    }
