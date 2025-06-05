import types
import sys

import pandas as pd


class DummyStreamlit(types.SimpleNamespace):
    def cache_data(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def warning(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


sys.modules.setdefault("streamlit", DummyStreamlit())

from processar_planilha_google_sheets import (
    converter_margem_para_numero_final,
    atualizar_margem_sem_reprocessamento,
)


def test_converter_margem_para_numero_final():
    assert converter_margem_para_numero_final(0.25) == 25.0
    assert converter_margem_para_numero_final("30%") == 30.0
    assert converter_margem_para_numero_final("0,45") == 45.0
    assert converter_margem_para_numero_final(25) == 25.0
    assert converter_margem_para_numero_final(None) == 0.0


def _sample_df():
    return pd.DataFrame(
        {
            "SKU PRODUTOS": ["A", "A"],
            "DIA DE VENDA": ["2024-01-01", "2024-01-01"],
            "PREÇO UND": [100, 50],
            "QUANTIDADE": [1, 1],
            "Valor de ADS": [10, 5],
            "Liquido_Estrategico_Num": [60, 30],
            "Liquido_Real_Num": [50, 20],
            "Margem_Estrategica_Num": [30, 20],
            "Margem_Estrategica_Original": ["30%", "20%"],
            "Margem_Real_Num": [25, 15],
            "Margem_Real_Original": ["25%", "15%"],
        }
    )


def test_main_margin_computation():
    df = _sample_df()
    result = atualizar_margem_sem_reprocessamento(df, "Margem Estratégica (L)")
    assert result["Margem_Num"].tolist() == [30, 20]
    assert result["Margem_Liquida"].iloc[0] == 50.0


def test_update_switch_to_real():
    df = _sample_df()
    result = atualizar_margem_sem_reprocessamento(df, "Margem Real (M)")
    assert result["Margem_Num"].tolist() == [25, 15]
    assert round(result["Margem_Liquida"].iloc[0], 2) == 36.67
