#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico minimo - Sistema Financiero Privado"""

import streamlit as st
import sys

st.title("Diagnostico de Entorno")

# Python version
st.write(f"Python: {sys.version}")
st.write(f"Ejecutable: {sys.executable}")

# Check packages with importlib
import importlib

packages = [
    'streamlit', 'plotly', 'pandas', 'numpy', 
    'pyarrow', 'reportlab', 'sklearn', 'statsmodels'
]

st.subheader("Estado de Paquetes")
results = []
for pkg in packages:
    try:
        m = importlib.import_module(pkg)
        version = getattr(m, '__version__', 'ok')
        results.append(f"OK  {pkg}: {version}")
    except ImportError as e:
        results.append(f"FALTA {pkg}: {e}")

st.code("\n".join(results))

# pip list via importlib.metadata
st.subheader("Paquetes instalados (importlib.metadata)")
try:
    import importlib.metadata as meta
    pkgs = sorted([(d.name, d.version) for d in meta.distributions()])
    st.code("\n".join(f"{n}: {v}" for n, v in pkgs))
except Exception as e:
    st.error(f"Error: {e}")
