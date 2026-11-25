"""Dados e utilidades compartilhadas pelo gerador do relatorio PDF."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent.parent
ART = RAIZ / "artifacts"
REL = RAIZ / "relatorio"
FIG = REL / "figuras"
sys.path.insert(0, str(RAIZ / "src"))

import features as feat  # noqa: E402

REL.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

with open(ART / "resultados.json", encoding="utf-8") as f:
    R = json.load(f)

META = R["meta"]
EDA = R["eda"]
SEL = R["selecionado"]
TAB = R["tabela"]
BASE = R["baseline"]
CM = SEL["teste_ajustado"]["matriz_confusao"]
CV = SEL["curva_limiar"]
IC = SEL["ic95"]
PV = pd.read_csv(ART / "previsoes_teste.csv")

TEAL = "#0f766e"
DARK = "#0b3b3a"
AMBER = "#d97706"
RED = "#b3261e"
GREEN = "#15803d"
SLATE = "#64748b"
LIGHT = "#e6f4f1"


def pct(x, casas: int = 1) -> str:
    return f"{x * 100:.{casas}f}%".replace(".", ",")


def f3(x) -> str:
    return f"{x:.3f}".replace(".", ",")


def f2(x) -> str:
    return f"{x:.2f}".replace(".", ",")


def inteiro(x) -> str:
    return f"{int(round(x)):,}".replace(",", ".")


def real(x) -> str:
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# Comparacao ordenada por PR-AUC (criterio pre-registrado)
# ---------------------------------------------------------------------------
COMPARACAO = sorted(TAB, key=lambda m: m["pr_auc"], reverse=True)
SELECIONADO = next(m for m in TAB if m["selecionado"])

# ---------------------------------------------------------------------------
# Tabela de limiares calculada sobre as probabilidades reais do teste
# ---------------------------------------------------------------------------
def matriz_no_limiar(t: float) -> dict:
    y = PV["churn_real"].to_numpy()
    p = PV["prob_churn"].to_numpy()
    pred = (p >= t).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    precisao = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0
    return {
        "limiar": t, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precisao": precisao, "recall": recall, "f1": f1,
        "acionados": tp + fp,
    }


LIMIARES = [matriz_no_limiar(t) for t in (0.20, 0.30, 0.34, 0.50, 0.60)]

# ---------------------------------------------------------------------------
# Exemplo trabalhado: cliente NC-003 do lote de novos perfis
# ---------------------------------------------------------------------------
modelo = joblib.load(ART / "modelo_previa.joblib")
bruto = pd.read_csv(RAIZ / "data" / "Telco-Customer-Churn.csv")
limpo_base = feat.limpar(bruto)
BASELINE_NUM = {c: float(limpo_base[c].median()) for c in feat.NUMERICAS}
BASELINE_CAT = {c: str(limpo_base[c].mode().iloc[0]) for c in feat.CATEGORICAS}

novos = pd.read_csv(RAIZ / "data" / "novos_clientes.csv")
_linha = novos[novos["customerID"] == "NC-003"].iloc[0].to_dict()
_limpo = feat.limpar(pd.DataFrame([_linha])).iloc[0].to_dict()
_cliente = {k: _limpo[k] for k in feat.CATEGORICAS + feat.NUMERICAS}
EXEMPLO = {
    "id": "NC-003",
    "cliente": _cliente,
    "probabilidade": float(modelo.predict_proba(feat.preparar_matriz(pd.DataFrame([_cliente])))[0, 1]),
}
_base_prob = float(modelo.predict_proba(feat.preparar_matriz(pd.DataFrame([{**BASELINE_CAT, **BASELINE_NUM}])))[0, 1])
EXEMPLO["base_probabilidade"] = _base_prob

NOMES = {
    "tenure": "Tempo de casa", "Contract": "Tipo de contrato", "InternetService": "Serviço de internet",
    "OnlineSecurity": "Segurança online", "TechSupport": "Suporte técnico", "PaymentMethod": "Forma de pagamento",
    "TotalCharges": "Total já pago", "PaperlessBilling": "Fatura digital", "MultipleLines": "Múltiplas linhas",
    "SeniorCitizen": "Idoso (60+)", "MonthlyCharges": "Cobrança mensal", "OnlineBackup": "Backup online",
    "Dependents": "Dependentes", "ServicosContratados": "Serviços contratados", "StreamingTV": "Streaming TV",
    "StreamingMovies": "Streaming filmes", "gender": "Gênero", "Partner": "Parceiro(a)",
    "PhoneService": "Serviço de telefone", "DeviceProtection": "Proteção do aparelho",
    "CobrancaMedia": "Cobrança média",
}

_fatores = []
for nome in feat.CATEGORICAS + feat.NUMERICAS:
    alternativo = dict(_cliente)
    alternativo[nome] = BASELINE_CAT.get(nome, BASELINE_NUM.get(nome))
    p_alt = float(modelo.predict_proba(feat.preparar_matriz(pd.DataFrame([alternativo])))[0, 1])
    _fatores.append((nome, EXEMPLO["probabilidade"] - p_alt, _cliente[nome], alternativo[nome]))
EXEMPLO["fatores"] = sorted(_fatores, key=lambda x: abs(x[1]), reverse=True)[:7]

# ---------------------------------------------------------------------------
# Dicionario de variaveis
# ---------------------------------------------------------------------------
DICIONARIO = [
    ("customerID", "Texto", "Identificador", "Código único do cliente; removido antes do treino."),
    ("gender", "Categórica", "Atributo", "Female / Male."),
    ("SeniorCitizen", "Binária (0/1)", "Atributo", "1 se o cliente tem 60 anos ou mais."),
    ("Partner", "Categórica", "Atributo", "Possui parceiro(a): Yes / No."),
    ("Dependents", "Categórica", "Atributo", "Possui dependentes: Yes / No."),
    ("tenure", "Numérica", "Atributo", "Meses como cliente (0 a 72)."),
    ("PhoneService", "Categórica", "Atributo", "Assinatura de telefone: Yes / No."),
    ("MultipleLines", "Categórica", "Atributo", "Linhas múltiplas: Yes / No / No phone service."),
    ("InternetService", "Categórica", "Atributo", "DSL / Fiber optic / No."),
    ("OnlineSecurity", "Categórica", "Atributo", "Segurança online: Yes / No / No internet service."),
    ("OnlineBackup", "Categórica", "Atributo", "Backup online: Yes / No / No internet service."),
    ("DeviceProtection", "Categórica", "Atributo", "Proteção do aparelho: Yes / No / No internet service."),
    ("TechSupport", "Categórica", "Atributo", "Suporte técnico: Yes / No / No internet service."),
    ("StreamingTV", "Categórica", "Atributo", "Streaming de TV: Yes / No / No internet service."),
    ("StreamingMovies", "Categórica", "Atributo", "Streaming de filmes: Yes / No / No internet service."),
    ("Contract", "Categórica", "Atributo", "Month-to-month / One year / Two year."),
    ("PaperlessBilling", "Categórica", "Atributo", "Fatura digital: Yes / No."),
    ("PaymentMethod", "Categórica", "Atributo", "Cheque eletrônico, cheque enviado, transferência ou cartão."),
    ("MonthlyCharges", "Numérica", "Atributo", "Cobrança mensal em unidades monetárias da base."),
    ("TotalCharges", "Numérica", "Atributo", "Total já cobrado; 11 células em branco (tenure = 0) tratadas como 0."),
    ("Churn", "Categórica", "Alvo", "Yes se o cliente cancelou; No caso contrário."),
    ("ServicosContratados", "Numérica", "Derivado", "Quantidade de serviços de valor agregado (0 a 6)."),
    ("CobrancaMedia", "Numérica", "Derivado", "TotalCharges ÷ tenure; para tenure = 0 usa MonthlyCharges."),
]


def tabela(headers, rows, classes: str = "", numerica: bool = False) -> str:
    cls = " ".join(c for c in [classes, "num" if numerica else ""] if c)
    th = "".join(f"<th>{h}</th>" for h in headers)
    corpo = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in rows
    )
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{corpo}</tbody></table>'


def figura(arquivo: str, numero: str, legenda: str) -> str:
    return (
        f'<figure><img src="figuras/{arquivo}.png" alt="{legenda}">'
        f'<figcaption><b>Figura {numero}.</b> {legenda}</figcaption></figure>'
    )


def kpis(itens) -> str:
    blocos = "".join(
        f'<div class="kpi"><div class="k">{k}</div><div class="v">{v}</div><div class="d">{d}</div></div>'
        for k, v, d in itens
    )
    return f'<div class="kpis">{blocos}</div>'


def callout(titulo: str, texto: str, tipo: str = "") -> str:
    return f'<div class="callout {tipo}"><span class="tit">{titulo}</span>{texto}</div>'
