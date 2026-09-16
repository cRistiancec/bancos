#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico de entorno - Sistema Financiero Privado"""

import streamlit as st
import subprocess
import sys
import importlib

st.title("Diagnostico de Entorno")

# Python version
st.subheader("Python")
st.code(f"Python {sys.version}\nEjecutable: {sys.executable}")

# Check packages
st.subheader("Estado de Paquetes")
packages = ['plotly', 'pandas', 'numpy', 'pyarrow', 'reportlab', 'sklearn', 'statsmodels', 'streamlit']
for pkg in packages:
    try:
        m = importlib.import_module(pkg)
        version = getattr(m, '__version__', 'unknown')
        st.success(f"OK {pkg}: {version}")
    except ImportError as e:
        st.error(f"FALTA {pkg}: {e}")

# pip list
st.subheader("pip list completo")
result = subprocess.run([sys.executable, '-m', 'pip', 'list'], capture_output=True, text=True)
st.code(result.stdout or result.stderr)

# uv list
st.subheader("uv pip list")
result2 = subprocess.run(['uv', 'pip', 'list'], capture_output=True, text=True)
st.code(result2.stdout or result2.stderr or "uv not found")
