"""PREVIA AI - API de inferencia.

Serve o painel web e expoe o modelo treinado (Gradient Boosting) para
previsoes em tempo real. Nenhum numero e simulado: toda probabilidade
retornada vem do pipeline persistido em artifacts/modelo_previa.joblib.

Executar:  python src/api.py      (http://127.0.0.1:8000)
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from joblib import load
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as feat  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ART = RAIZ / "artifacts"
WEB = RAIZ / "web"

app = FastAPI(title="PREVIA AI", version="1.0.0", description="Previsao de churn com modelo treinado")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# ----------------------------------------------------------------------------
# Carregamento de artefatos
# ----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def carregar_modelo():
    caminho = ART / "modelo_previa.joblib"
    if not caminho.exists():
        raise RuntimeError("Modelo ausente. Rode 'python src/train.py' primeiro.")
    return load(caminho)


@lru_cache(maxsize=1)
def carregar_resultados() -> dict:
    with open(ART / "resultados.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def carregar_amostra() -> pd.DataFrame:
    return pd.read_csv(ART / "previsoes_teste.csv")


@lru_cache(maxsize=1)
def mapa_atributos() -> dict:
    """Mapeia cada coluna transformada (one-hot) para o atributo original."""
    modelo = carregar_modelo()
    prep = modelo.named_steps["prep"]
    nomes = list(prep.get_feature_names_out())
    cat_cols = sorted(feat.CATEGORICAS, key=len, reverse=True)
    mapa = {}
    for nome in nomes:
        base = nome.split("__", 1)[1] if "__" in nome else nome
        if nome.startswith("num__"):
            mapa[nome] = base
        else:
            alvo = next((c for c in cat_cols if base.startswith(c + "_")), base)
            mapa[nome] = alvo
    return mapa


@lru_cache(maxsize=1)
def explicador():
    import shap

    return shap.TreeExplainer(carregar_modelo().named_steps["modelo"])


# ----------------------------------------------------------------------------
# Esquema de entrada
# ----------------------------------------------------------------------------
SimNao = Literal["Yes", "No"]

class Cliente(BaseModel):
    gender: Literal["Male", "Female"] = "Female"
    SeniorCitizen: int = Field(0, ge=0, le=1)
    Partner: SimNao = "No"
    Dependents: SimNao = "No"
    tenure: int = Field(12, ge=0, le=100, description="Meses de casa")
    PhoneService: SimNao = "Yes"
    MultipleLines: Literal["Yes", "No", "No phone service"] = "No"
    InternetService: Literal["DSL", "Fiber optic", "No internet service"] = "DSL"
    OnlineSecurity: Literal["Yes", "No", "No internet service"] = "No"
    OnlineBackup: Literal["Yes", "No", "No internet service"] = "No"
    DeviceProtection: Literal["Yes", "No", "No internet service"] = "No"
    TechSupport: Literal["Yes", "No", "No internet service"] = "No"
    StreamingTV: Literal["Yes", "No", "No internet service"] = "No"
    StreamingMovies: Literal["Yes", "No", "No internet service"] = "No"
    Contract: Literal["Month-to-month", "One year", "Two year"] = "Month-to-month"
    PaperlessBilling: SimNao = "Yes"
    PaymentMethod: Literal[
        "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
    ] = "Electronic check"
    MonthlyCharges: float = Field(70.0, ge=0, le=500)
    TotalCharges: float = Field(840.0, ge=0, le=100000)


class Lote(BaseModel):
    clientes: list[Cliente]
    limiar: float | None = None


# ----------------------------------------------------------------------------
# Inferencia
# ----------------------------------------------------------------------------
def faixa_risco(p: float, limiar: float) -> dict:
    if p >= 0.60:
        return {"rotulo": "Crítico", "cor": "#b3261e", "acao": "Contato imediato do time de retenção"}
    if p >= limiar:
        return {"rotulo": "Alto", "cor": "#d97706", "acao": "Incluir na fila de retenção da semana"}
    if p >= 0.20:
        return {"rotulo": "Moderado", "cor": "#0e7490", "acao": "Monitorar e enviar oferta preventiva"}
    return {"rotulo": "Baixo", "cor": "#15803d", "acao": "Manter acompanhamento de rotina"}


def prever_um(cliente: Cliente, limiar: float, com_explicacao: bool = True) -> dict:
    modelo = carregar_modelo()
    dados = cliente.model_dump()
    df = pd.DataFrame([dados])
    df["customerID"] = "NOVO"
    df["Churn"] = "No"
    limpo = feat.limpar(df)
    X = feat.preparar_matriz(limpo)

    proba = float(modelo.predict_proba(X)[0, 1])
    resposta = {
        "probabilidade": round(proba, 4),
        "percentual": round(proba * 100, 1),
        "limiar": limiar,
        "previsao": int(proba >= limiar),
        "faixa": faixa_risco(proba, limiar),
        "cliente": dados,
    }

    if com_explicacao:
        prep = modelo.named_steps["prep"]
        Xt = prep.transform(X)
        sv = explicador().shap_values(Xt)
        if isinstance(sv, list):
            sv = sv[-1]
        sv = np.asarray(sv)
        if sv.ndim == 3:
            sv = sv[0]
        contrib = np.ravel(sv[0])
        base = explicador().expected_value
        base = float(np.ravel(base)[0]) if np.ndim(base) else float(base)
        margem = base + contrib.sum()
        sig = lambda z: 1.0 / (1.0 + np.exp(-z))
        p_final = sig(margem)
        nomes = list(prep.get_feature_names_out())
        mapa = mapa_atributos()

        # Agrega contribuicoes por atributo original (soma dos one-hot).
        agregado: dict[str, float] = {}
        for nome, c in zip(nomes, contrib):
            agregado[mapa.get(nome, nome)] = agregado.get(mapa.get(nome, nome), 0.0) + float(c)

        # Impacto em probabilidade: quanto a probabilidade cai se o atributo
        # voltasse ao valor medio da base (contribuicao zerada).
        itens = []
        for atributo, c in agregado.items():
            delta = p_final - sig(margem - c)
            itens.append(
                {
                    "atributo": atributo,
                    "impacto_pp": round(float(delta) * 100, 2),
                    "direcao": "aumenta" if delta > 0 else "reduz",
                }
            )
        itens.sort(key=lambda d: abs(d["impacto_pp"]), reverse=True)
        resposta["contribuicoes"] = itens[:7]
        resposta["base_probabilidade"] = round(float(sig(base)), 4)

    return resposta


# ----------------------------------------------------------------------------
# Rotas
# ----------------------------------------------------------------------------
@app.get("/api/saude")
def saude():
    r = carregar_resultados()
    return {
        "status": "ok",
        "modelo": r["selecionado"]["nome"],
        "limiar": r["selecionado"]["limiar"],
        "treinado_em": r["meta"]["gerado_em"],
        "roc_auc": r["selecionado"]["teste_05"]["roc_auc"],
    }


@app.get("/api/resultados")
def resultados():
    r = carregar_resultados()
    return JSONResponse(r)


@app.get("/api/amostra-teste")
def amostra_teste(limite: int = 2000):
    df = carregar_amostra().sort_values("prob_churn", ascending=False).head(limite)
    colunas = [
        "customerID", "tenure", "Contract", "InternetService", "PaymentMethod",
        "MonthlyCharges", "prob_churn", "churn_real", "previsao",
    ]
    return {
        "total": int(len(carregar_amostra())),
        "registros": df[colunas].to_dict(orient="records"),
    }


@app.post("/api/prever")
def prever(cliente: Cliente, limiar: float | None = None):
    r = carregar_resultados()
    lim = limiar if limiar is not None else r["selecionado"]["limiar"]
    return prever_um(cliente, lim)


@app.post("/api/prever-lote")
def prever_lote(lote: Lote):
    r = carregar_resultados()
    lim = lote.limiar if lote.limiar is not None else r["selecionado"]["limiar"]
    if len(lote.clientes) > 500:
        raise HTTPException(400, "Maximo de 500 clientes por lote.")
    return {"limiar": lim, "previsoes": [prever_um(c, lim, com_explicacao=False) for c in lote.clientes]}


@app.get("/api/novos-clientes")
def novos_clientes():
    caminho = RAIZ / "data" / "novos_clientes.csv"
    if not caminho.exists():
        raise HTTPException(404, "Arquivo de novos clientes ausente.")
    df = pd.read_csv(caminho)
    r = carregar_resultados()
    lim = r["selecionado"]["limiar"]
    saida = []
    for _, linha in df.iterrows():
        dados = {k: (v.item() if hasattr(v, "item") else v) for k, v in linha.items()}
        cliente = Cliente(
            **{
                k: dados[k]
                for k in Cliente.model_fields
                if k in dados and pd.notna(dados[k])
            }
        )
        p = prever_um(cliente, lim, com_explicacao=False)
        p["customerID"] = dados["customerID"]
        saida.append(p)
    return {"limiar": lim, "total": len(saida), "clientes": saida}


@app.get("/api/modelo-info")
def modelo_info():
    import sklearn
    import xgboost

    r = carregar_resultados()
    modelo = carregar_modelo()
    prep = modelo.named_steps["prep"]
    return {
        "algoritmo": r["selecionado"]["nome"],
        "familia": r["selecionado"]["familia"],
        "hiperparametros": r["selecionado"]["melhor_params"],
        "limiar": r["selecionado"]["limiar"],
        "n_atributos_originais": len(feat.CATEGORICAS) + len(feat.NUMERICAS),
        "n_atributos_transformados": int(len(prep.get_feature_names_out())),
        "categoricas": feat.CATEGORICAS,
        "numericas": feat.NUMERICAS,
        "artefato": "artifacts/modelo_previa.joblib",
        "bibliotecas": {
            "scikit-learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }


@app.get("/")
def raiz():
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=str(WEB)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
