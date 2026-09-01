# -*- coding: utf-8 -*-
"""
Fixtures compartidas. Los tests corren contra los datos REALES en
master_data/ (no se usan mocks ni datos sinteticos) -- consistente con el
principio de la plataforma de no fabricar cifras, incluso en las pruebas.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def df_balance():
    from services.data_service import cargar_balance
    df, _ = cargar_balance()
    return df


@pytest.fixture(scope="session")
def df_camel():
    from services.data_service import cargar_camel
    df, _ = cargar_camel()
    return df


@pytest.fixture(scope="session")
def df_pyg():
    from services.data_service import cargar_pyg
    df, _ = cargar_pyg()
    return df


@pytest.fixture(scope="session")
def fecha_max_camel(df_camel):
    return df_camel['fecha'].max()


@pytest.fixture(scope="session")
def fecha_max_balance(df_balance):
    return df_balance['fecha'].max()
