"""PREVIA AI - preparacao de dados.

Este modulo e a UNICA fonte de verdade para a limpeza e a engenharia de
atributos. Ele e usado tanto pelo treinamento (src/train.py) quanto pela API
de producao (src/api.py), garantindo que o modelo receba exatamente o mesmo
formato de dados em treino e em inferencia (evita train/serve skew).
"""

from __future__ import annotations

import pandas as pd

# Colunas usadas como atributos (features) do modelo.
CATEGORICAS = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]

NUMERICAS = [
    "SeniorCitizen",
    "tenure",
    "MonthlyCharges",
    "TotalCharges",
    "ServicosContratados",
    "CobrancaMedia",
]

ALVO = "Churn"

# Servicos de valor agregado: contamos quantos o cliente possui.
COLUNAS_SERVICO = [
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza basica: tipos, valores ausentes e atributos derivados."""
    df = df.copy()

    # TotalCharges vem como texto e possui 11 celulas em branco (clientes com
    # tenure = 0, ou seja, que ainda nao foram faturados). Convertemos para
    # numero e tratamos esses casos explicitamente.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(0.0)

    # Atributos derivados (deterministicos, calculados a partir da entrada).
    servicos = [c for c in COLUNAS_SERVICO if c in df.columns]
    if servicos:
        df["ServicosContratados"] = (df[servicos] == "Yes").sum(axis=1).astype(int)
    else:
        df["ServicosContratados"] = 0

    # Cobranca media real por mes de casa. Para tenure = 0 usamos a cobranca
    # mensal corrente como proxy (evita divisao por zero).
    tenure = df["tenure"].astype(float)
    df["CobrancaMedia"] = (df["TotalCharges"] / tenure.where(tenure > 0)).fillna(
        df["MonthlyCharges"]
    )

    # Normaliza SeniorCitizen (0/1) para int, caso venha como texto.
    df["SeniorCitizen"] = pd.to_numeric(df["SeniorCitizen"], errors="coerce").fillna(0).astype(int)

    # Garante os tipos esperados nas categorias.
    for col in CATEGORICAS:
        df[col] = df[col].astype(str)

    return df


def preparar_matriz(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna apenas as colunas de atributos, na ordem esperada pelo modelo."""
    return df[CATEGORICAS + NUMERICAS].copy()


def preparar_alvo(df: pd.DataFrame) -> pd.Series:
    """Converte o alvo textual ('Yes'/'No') em 1/0."""
    return (df[ALVO].astype(str).str.strip().str.lower() == "yes").astype(int)
