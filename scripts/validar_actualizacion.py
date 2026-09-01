#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Puerta de calidad previa a publicar los Parquet bancarios."""

from __future__ import annotations

import argparse
import calendar
import json
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).parent))
import config


ROOT_DIR = Path(__file__).parent.parent
MASTER_DATA_DIR = ROOT_DIR / "master_data"
DATASETS = {
    "balance": {
        "archivo": "balance.parquet",
        "columnas": {"banco", "fecha", "codigo", "cuenta", "valor", "nivel"},
        "clave": ["banco", "fecha", "codigo", "cuenta"],
    },
    "pyg": {
        "archivo": "pyg.parquet",
        "columnas": {
            "banco", "fecha", "codigo", "cuenta",
            "valor_acumulado", "valor_mes", "valor_12m",
        },
        "clave": ["banco", "fecha", "codigo"],
    },
    "camel": {
        "archivo": "camel.parquet",
        "columnas": {"banco", "fecha", "codigo", "indicador", "valor", "categoria"},
        "clave": ["banco", "fecha", "codigo"],
    },
}


def fecha_objetivo_config() -> pd.Timestamp:
    ultimo_dia = calendar.monthrange(config.ANO_OBJETIVO, config.MES_OBJETIVO)[1]
    return pd.Timestamp(config.ANO_OBJETIVO, config.MES_OBJETIVO, ultimo_dia)


def _serializar_bancos(valores) -> list[str]:
    return sorted(str(valor) for valor in valores)


def capturar_estado() -> dict:
    """Resume el estado publicado sin cargar columnas de valores pesadas."""
    estado: dict[str, dict] = {}
    for nombre, especificacion in DATASETS.items():
        ruta = MASTER_DATA_DIR / especificacion["archivo"]
        if not ruta.exists():
            raise ValueError(f"No existe {ruta}")
        df = pd.read_parquet(ruta, columns=["banco", "fecha"])
        fechas = pd.to_datetime(df["fecha"])
        if df.empty or fechas.isna().all():
            raise ValueError(f"{nombre} no contiene fechas validas")
        fecha_max = fechas.max()
        meses = sorted(str(periodo) for periodo in fechas.dt.to_period("M").unique())
        estado[nombre] = {
            "filas": int(len(df)),
            "fecha_min": fechas.min().date().isoformat(),
            "fecha_max": fecha_max.date().isoformat(),
            "meses": meses,
            "bancos": _serializar_bancos(df["banco"].dropna().unique()),
            "bancos_ultimo_mes": _serializar_bancos(
                df.loc[fechas == fecha_max, "banco"].dropna().unique()
            ),
        }
    return estado


def validar_actualizacion(
    fecha_esperada: pd.Timestamp | None = None,
    estado_anterior: dict | None = None,
    bancos_esperados: int | None = None,
) -> dict:
    """Valida fecha, cobertura, claves e integridad historica de los 3 datasets."""
    if fecha_esperada is None:
        fecha_esperada = fecha_objetivo_config()
    fecha_esperada = pd.Timestamp(fecha_esperada)
    fecha_esperada = fecha_esperada.normalize() + pd.offsets.MonthEnd(0)
    bancos_esperados = bancos_esperados or config.NUMERO_ESPERADO_BANCOS
    errores: list[str] = []
    estado_nuevo: dict[str, dict] = {}

    for nombre, especificacion in DATASETS.items():
        ruta = MASTER_DATA_DIR / especificacion["archivo"]
        if not ruta.exists():
            errores.append(f"{nombre}: no existe {ruta.name}")
            continue

        try:
            columnas_disponibles = set(pq.ParquetFile(ruta).schema.names)
            columnas_lectura = list(dict.fromkeys(especificacion["clave"]))
            df = pd.read_parquet(
                ruta,
                columns=columnas_lectura,
                dtype_backend="pyarrow",
            )
        except Exception as exc:
            errores.append(f"{nombre}: Parquet ilegible: {exc}")
            continue

        faltantes = especificacion["columnas"] - columnas_disponibles
        if faltantes:
            errores.append(f"{nombre}: faltan columnas {sorted(faltantes)}")
            continue
        if df.empty:
            errores.append(f"{nombre}: dataset vacio")
            continue

        fechas = pd.to_datetime(df["fecha"], errors="coerce")
        if fechas.isna().any():
            errores.append(f"{nombre}: contiene {int(fechas.isna().sum())} fechas invalidas")
            continue

        fecha_min = fechas.min()
        fecha_max = fechas.max()
        meses = pd.PeriodIndex(fechas.unique(), freq="M")
        rango = pd.period_range(meses.min(), meses.max(), freq="M")
        meses_faltantes = rango.difference(meses)
        if len(meses_faltantes):
            errores.append(
                f"{nombre}: faltan meses globales {', '.join(map(str, meses_faltantes[:12]))}"
            )
        if fecha_max != fecha_esperada:
            errores.append(
                f"{nombre}: fecha maxima {fecha_max.date()} != {fecha_esperada.date()}"
            )

        bancos_totales = set(str(x) for x in df["banco"].dropna().unique())
        bancos_ultimo = set(str(x) for x in df.loc[fechas == fecha_max, "banco"].dropna().unique())
        if len(bancos_totales) != bancos_esperados:
            errores.append(
                f"{nombre}: contiene {len(bancos_totales)} bancos; se esperaban {bancos_esperados}"
            )
        if len(bancos_ultimo) != bancos_esperados:
            rezagados = sorted(bancos_totales - bancos_ultimo)
            errores.append(
                f"{nombre}: solo {len(bancos_ultimo)} bancos llegan al ultimo mes; "
                f"rezagados={rezagados}"
            )

        duplicados = int(df.duplicated(especificacion["clave"]).sum())
        if duplicados:
            errores.append(
                f"{nombre}: {duplicados} claves duplicadas en {especificacion['clave']}"
            )

        meses_texto = sorted(str(periodo) for periodo in meses.unique())
        estado_nuevo[nombre] = {
            "filas": int(len(df)),
            "fecha_min": fecha_min.date().isoformat(),
            "fecha_max": fecha_max.date().isoformat(),
            "meses": meses_texto,
            "bancos": sorted(bancos_totales),
            "bancos_ultimo_mes": sorted(bancos_ultimo),
        }

        anterior = (estado_anterior or {}).get(nombre)
        if anterior:
            if fecha_min > pd.Timestamp(anterior["fecha_min"]):
                errores.append(
                    f"{nombre}: perdio historia; antes iniciaba {anterior['fecha_min']} "
                    f"y ahora {fecha_min.date()}"
                )
            meses_perdidos = set(anterior.get("meses", [])) - set(meses_texto)
            if meses_perdidos:
                errores.append(
                    f"{nombre}: perdio meses publicados {sorted(meses_perdidos)[:12]}"
                )
            bancos_perdidos = set(anterior.get("bancos", [])) - bancos_totales
            if bancos_perdidos:
                errores.append(f"{nombre}: perdio bancos {sorted(bancos_perdidos)}")

    metadata_path = MASTER_DATA_DIR / "metadata.json"
    if not metadata_path.exists():
        errores.append("metadata: no existe metadata.json")
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            fecha_metadata = pd.Timestamp(metadata.get("fecha_max"))
            if fecha_metadata != fecha_esperada:
                errores.append(
                    f"metadata: fecha_max {fecha_metadata.date()} != {fecha_esperada.date()}"
                )
            if metadata.get("bancos_error"):
                errores.append(f"metadata: bancos con error {metadata['bancos_error']}")
        except Exception as exc:
            errores.append(f"metadata: invalido: {exc}")

    if errores:
        raise ValueError("VALIDACION MENSUAL FALLIDA\n- " + "\n- ".join(errores))
    return estado_nuevo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fecha-esperada", help="Fecha de corte YYYY-MM-DD")
    parser.add_argument("--estado-anterior", type=Path)
    parser.add_argument("--capturar-estado", type=Path)
    args = parser.parse_args()

    if args.capturar_estado:
        args.capturar_estado.write_text(
            json.dumps(capturar_estado(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Estado anterior guardado en {args.capturar_estado}")
        return 0

    anterior = None
    if args.estado_anterior:
        anterior = json.loads(args.estado_anterior.read_text(encoding="utf-8"))
    fecha = pd.Timestamp(args.fecha_esperada) if args.fecha_esperada else None
    estado = validar_actualizacion(fecha, anterior)
    print("VALIDACION MENSUAL OK")
    for nombre, datos in estado.items():
        print(
            f"  {nombre}: {datos['filas']:,} filas, "
            f"{len(datos['bancos_ultimo_mes'])} bancos, fecha_max={datos['fecha_max']}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
