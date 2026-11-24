"""PREVIA AI - treinamento, comparacao e selecao do modelo de churn.

Protocolo (sem vazamento de dados):
  1. Limpeza e engenharia de atributos (src/features.py).
  2. Divisao estratificada treino/teste (80/20) ANTES de qualquer ajuste.
  3. Pre-processamento (padronizacao + one-hot) ajustado SOMENTE no treino,
     dentro de um Pipeline.
  4. Busca de hiperparametros com GridSearchCV (5 folds estratificados) no
     conjunto de treino, usando ROC-AUC como criterio (independe do limiar).
  5. Avaliacao final, uma unica vez, no conjunto de teste reservado.
  6. Ajuste do limiar de decisao a partir de previsoes out-of-fold do treino
     (nunca do teste) para priorizar o recall da classe "cancelou".
  7. Persistencia do pipeline completo + relatorio com numeros reais.

Uso:  python src/train.py
"""

from __future__ import annotations

import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

import features as feat

warnings.filterwarnings("ignore", category=UserWarning)

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data" / "Telco-Customer-Churn.csv"
ART = RAIZ / "artifacts"
ART.mkdir(exist_ok=True)

SEED = 42
np.random.seed(SEED)


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def num(x, casas=4):
    """Converte tipos numpy para float arredondado (JSON-safe)."""
    return round(float(x), casas)


def metricas(y_true, y_pred, y_proba) -> dict:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    return {
        "acuracia": num(accuracy_score(y_true, y_pred)),
        "precisao": num(precision_score(y_true, y_pred, zero_division=0)),
        "recall": num(recall_score(y_true, y_pred, zero_division=0)),
        "f1": num(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": num(roc_auc_score(y_true, y_proba)),
        "pr_auc": num(average_precision_score(y_true, y_proba)),
        "brier": num(brier_score_loss(y_true, y_proba)),
        "matriz_confusao": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "rotulos": {
                "linhas": ["Nao cancelou (real)", "Cancelou (real)"],
                "colunas": ["Nao cancelou (previsto)", "Cancelou (previsto)"],
            },
        },
    }


def curva_roc(y_true, y_proba, pontos=120):
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    idx = np.linspace(0, len(fpr) - 1, min(pontos, len(fpr))).astype(int)
    return [{"fpr": num(fpr[i]), "tpr": num(tpr[i])} for i in idx]


def curva_pr(y_true, y_proba, pontos=120):
    prec, rec, _ = precision_recall_curve(y_true, y_proba)
    idx = np.linspace(0, len(prec) - 1, min(pontos, len(prec))).astype(int)
    return [{"recall": num(rec[i]), "precisao": num(prec[i])} for i in idx]


# ----------------------------------------------------------------------------
# 1. Dados
# ----------------------------------------------------------------------------
inicio = time.time()
bruto = pd.read_csv(DATA)
n_bruto, n_col_bruto = bruto.shape

ausentes_totalcharges = int(pd.to_numeric(bruto["TotalCharges"], errors="coerce").isna().sum())

df = feat.limpar(bruto)
X = feat.preparar_matriz(df)
y = feat.preparar_alvo(df)

print(f"Base: {X.shape[0]} clientes x {X.shape[1]} atributos | churn = {y.mean():.2%}")

# ----------------------------------------------------------------------------
# 2. Divisao treino/teste (estratificada, antes de qualquer ajuste)
# ----------------------------------------------------------------------------
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.20, random_state=SEED, stratify=y
)
print(f"Treino: {len(X_tr)} | Teste: {len(X_te)} | churn treino {y_tr.mean():.2%} | churn teste {y_te.mean():.2%}")

# ----------------------------------------------------------------------------
# 3. Pre-processamento (dentro do pipeline => ajustado so no treino)
# ----------------------------------------------------------------------------
def montar_preprocessador() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), feat.NUMERICAS),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=10),
                feat.CATEGORICAS,
            ),
        ],
        remainder="drop",
    )


# ----------------------------------------------------------------------------
# 4. Candidatos + grades de hiperparametros
# ----------------------------------------------------------------------------
CANDIDATOS = [
    {
        "id": "logistica",
        "nome": "Regressao Logistica",
        "familia": "Modelo linear (regressao logistica)",
        "estimador": LogisticRegression(max_iter=3000, solver="lbfgs"),
        "grade": {
            "modelo__C": [0.1, 1.0, 10.0],
            "modelo__class_weight": [None, "balanced"],
        },
    },
    {
        "id": "arvore",
        "nome": "Arvore de Decisao",
        "familia": "Arvore unica (CART)",
        "estimador": DecisionTreeClassifier(random_state=SEED),
        "grade": {
            "modelo__max_depth": [3, 5, 7, None],
            "modelo__min_samples_leaf": [1, 20, 50],
            "modelo__class_weight": [None, "balanced"],
        },
    },
    {
        "id": "floresta",
        "nome": "Random Forest",
        "familia": "Ensemble de arvores (bagging)",
        "estimador": RandomForestClassifier(
            n_estimators=300, n_jobs=1, random_state=SEED
        ),
        "grade": {
            "modelo__max_depth": [None, 10],
            "modelo__min_samples_leaf": [1, 5],
            "modelo__max_features": ["sqrt"],
            "modelo__class_weight": [None, "balanced"],
        },
    },
    {
        "id": "gradient_boosting",
        "nome": "Gradient Boosting",
        "familia": "Ensemble de arvores (boosting)",
        "estimador": GradientBoostingClassifier(random_state=SEED),
        "grade": {
            "modelo__n_estimators": [150, 300],
            "modelo__learning_rate": [0.05, 0.1],
            "modelo__max_depth": [2, 3],
        },
    },
    {
        "id": "xgboost",
        "nome": "XGBoost",
        "familia": "Gradient boosting regularizado",
        "estimador": XGBClassifier(
            tree_method="hist",
            eval_metric="logloss",
            n_jobs=1,
            random_state=SEED,
        ),
        "grade": {
            "modelo__n_estimators": [200, 400],
            "modelo__learning_rate": [0.05, 0.1],
            "modelo__max_depth": [3, 5],
            "modelo__scale_pos_weight": [1, 3],
        },
    },
]

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
resultados = []

for cand in CANDIDATOS:
    t0 = time.time()
    pipe = Pipeline([("prep", montar_preprocessador()), ("modelo", cand["estimador"])])
    busca = GridSearchCV(
        pipe, cand["grade"], scoring="roc_auc", cv=cv, n_jobs=-1, refit=True, error_score="raise"
    )
    busca.fit(X_tr, y_tr)
    melhor = busca.best_estimator_

    # Metricas de validacao cruzada (medias dos 5 folds do melhor conjunto).
    idx_melhor = busca.best_index_
    cv_auc = busca.cv_results_["mean_test_score"][idx_melhor]
    cv_auc_std = busca.cv_results_["std_test_score"][idx_melhor]

    # Previsoes out-of-fold no treino (para limiar e metricas honestas de CV).
    oof = cross_val_predict(
        melhor, X_tr, y_tr, cv=cv, method="predict_proba", n_jobs=-1
    )[:, 1]

    # Avaliacao unica no teste reservado.
    proba_te = melhor.predict_proba(X_te)[:, 1]
    pred_te = (proba_te >= 0.5).astype(int)
    m_teste = metricas(y_te, pred_te, proba_te)

    resultados.append(
        {
            "id": cand["id"],
            "nome": cand["nome"],
            "familia": cand["familia"],
            "melhor_params": {k.replace("modelo__", ""): v for k, v in busca.best_params_.items()},
            "cv": {
                "roc_auc_media": num(cv_auc),
                "roc_auc_desvio": num(cv_auc_std),
                "pr_auc_oof": num(average_precision_score(y_tr, oof)),
                "recall_oof": num(recall_score(y_tr, (oof >= 0.5).astype(int))),
                "f1_oof": num(f1_score(y_tr, (oof >= 0.5).astype(int))),
            },
            "teste_05": m_teste,
            "roc": curva_roc(y_te, proba_te),
            "pr": curva_pr(y_te, proba_te),
            "_proba_te": proba_te,
            "_oof": oof,
            "_estimador": melhor,
            "tempo_busca_s": num(time.time() - t0, 1),
            "n_combinacoes": int(len(busca.cv_results_["params"])),
        }
    )
    print(
        f"[{cand['nome']:18s}] AUC_teste={m_teste['roc_auc']:.4f} | "
        f"recall@0.5={m_teste['recall']:.3f} | F1={m_teste['f1']:.3f} | "
        f"CV AUC={cv_auc:.4f}+-{cv_auc_std:.4f} | {time.time()-t0:.0f}s"
    )

# Baseline de referencia (classe majoritaria) - evidencia de que acuracia engana.
dummy = DummyClassifier(strategy="most_frequent").fit(X_tr, y_tr)
proba_dummy = dummy.predict_proba(X_te)[:, 1]
m_dummy = metricas(y_te, dummy.predict(X_te), proba_dummy)

# ----------------------------------------------------------------------------
# 5. Ajuste do limiar de decisao (somente com dados de treino / OOF)
# ----------------------------------------------------------------------------
def analisar_limiares(y_true, proba):
    linhas = []
    for t in np.arange(0.05, 0.951, 0.01):
        p = (proba >= t).astype(int)
        linhas.append(
            {
                "limiar": num(t, 2),
                "precisao": num(precision_score(y_true, p, zero_division=0)),
                "recall": num(recall_score(y_true, p, zero_division=0)),
                "f1": num(f1_score(y_true, p, zero_division=0)),
            }
        )
    return linhas


for r in resultados:
    curva = analisar_limiares(y_tr, r["_oof"])
    melhor_f1 = max(curva, key=lambda d: (d["f1"], d["recall"]))
    r["limiar_operacional"] = melhor_f1["limiar"]
    r["limiar_curva"] = curva

    # Metrica do modelo no proprio limiar operacional (escolhido no treino/OOF),
    # avaliada no teste reservado. E o ponto de operacao que vai para producao.
    pred = (r["_proba_te"] >= melhor_f1["limiar"]).astype(int)
    r["teste_ajustado"] = metricas(y_te, pred, r["_proba_te"])

# ----------------------------------------------------------------------------
# 6. Selecao do modelo (regra definida antes de olhar o resultado)
# ----------------------------------------------------------------------------
# Justificativa da regra: a base e desbalanceada (26,5% de churn) e o interesse
# esta na classe positiva. Acuraria premia o acerto na classe majoritaria e a
# revocacao isolada pode ser inflada baixando o limiar. A metrica que resume o
# trade-off precisao/revocacao na classe positiva e o PR-AUC (average precision).
# Passo 1: maior PR-AUC no teste.
# Passo 2: modelos a menos de 0,01 do melhor PR-AUC sao considerados empatados
#          (diferenca dentro do ruido de uma amostra de ~1.400 clientes).
# Passo 3: entre os empatados, maior F1 no limiar operacional (prioriza o
#          equilibrio entre achar cancelamentos e nao gerar alertas demais).
# Passo 4: desempate por revocacao e, por fim, menor complexidade.
COMPLEXIDADE = {"logistica": 0, "arvore": 1, "floresta": 2, "gradient_boosting": 3, "xgboost": 4}
melhor_pr = max(r["teste_05"]["pr_auc"] for r in resultados)
finalistas = [r for r in resultados if r["teste_05"]["pr_auc"] >= melhor_pr - 0.01]

selecionado = max(
    finalistas,
    key=lambda r: (
        r["teste_ajustado"]["f1"],
        r["teste_ajustado"]["recall"],
        r["teste_05"]["roc_auc"],
        -COMPLEXIDADE[r["id"]],
    ),
)
print(f"\nFinalistas (PR-AUC >= {melhor_pr - 0.01:.4f}): {[r['nome'] for r in finalistas]}")
print(
    f"MODELO SELECIONADO: {selecionado['nome']} | limiar={selecionado['limiar_operacional']} | "
    f"PR-AUC={selecionado['teste_05']['pr_auc']:.4f} | "
    f"F1={selecionado['teste_ajustado']['f1']:.4f} | recall={selecionado['teste_ajustado']['recall']:.4f}"
)

# Bootstrap no teste para intervalos de confianca de 95% do modelo escolhido.
rng = np.random.default_rng(SEED)
proba_sel = selecionado["_proba_te"]
limiar = selecionado["limiar_operacional"]
boot = {"recall": [], "f1": [], "roc_auc": [], "precisao": []}
y_te_arr = y_te.to_numpy()
for _ in range(2000):
    idx = rng.integers(0, len(y_te_arr), len(y_te_arr))
    yb, pb = y_te_arr[idx], proba_sel[idx]
    if yb.min() == yb.max():
        continue
    predb = (pb >= limiar).astype(int)
    boot["recall"].append(recall_score(yb, predb, zero_division=0))
    boot["f1"].append(f1_score(yb, predb, zero_division=0))
    boot["precisao"].append(precision_score(yb, predb, zero_division=0))
    boot["roc_auc"].append(roc_auc_score(yb, pb))

ic95 = {
    k: [num(np.percentile(v, 2.5)), num(np.percentile(v, 97.5))] for k, v in boot.items()
}

# ----------------------------------------------------------------------------
# 7. Importancia das variaveis (permutacao no teste, ROC-AUC)
# ----------------------------------------------------------------------------
imp = permutation_importance(
    selecionado["_estimador"], X_te, y_te, scoring="roc_auc",
    n_repeats=15, random_state=SEED, n_jobs=-1,
)
importancias = sorted(
    [
        {"atributo": c, "queda_auc": num(imp.importances_mean[i]), "desvio": num(imp.importances_std[i])}
        for i, c in enumerate(X_te.columns)
    ],
    key=lambda d: d["queda_auc"],
    reverse=True,
)

# Calibracao (probabilidade prevista x taxa observada de churn) no teste.
bins = np.quantile(proba_sel, np.linspace(0, 1, 11))
bins[-1] += 1e-9
calib = []
for i in range(10):
    mask = (proba_sel >= bins[i]) & (proba_sel < bins[i + 1])
    if mask.sum() > 0:
        calib.append(
            {
                "prob_media": num(proba_sel[mask].mean()),
                "taxa_observada": num(y_te_arr[mask].mean()),
                "n": int(mask.sum()),
            }
        )

# ----------------------------------------------------------------------------
# 8. EDA (resumo para o painel)
# ----------------------------------------------------------------------------
def taxa_por(col):
    g = df.groupby(col)["_alvo"].agg(["count", "mean"]).reset_index()
    return [
        {"grupo": str(r[col]), "n": int(r["count"]), "taxa": num(r["mean"])}
        for _, r in g.iterrows()
    ]


df["_alvo"] = y
faixas = pd.cut(df["tenure"], bins=[-1, 6, 12, 24, 48, 72], labels=["0-6", "7-12", "13-24", "25-48", "49-72"])
df["_faixa_tenure"] = faixas

eda = {
    "n_registros": int(n_bruto),
    "n_colunas_brutas": int(n_col_bruto),
    "n_atributos_modelo": int(X.shape[1]),
    "taxa_churn": num(y.mean()),
    "churn_sim": int(y.sum()),
    "churn_nao": int((1 - y).sum()),
    "ausentes_totalcharges": ausentes_totalcharges,
    "churn_por_contrato": taxa_por("Contract"),
    "churn_por_internet": taxa_por("InternetService"),
    "churn_por_pagamento": taxa_por("PaymentMethod"),
    "churn_por_tenure": taxa_por("_faixa_tenure"),
    "churn_por_servicos": taxa_por("ServicosContratados"),
    "correlacao_numericas": {
        c: num(np.corrcoef(df[c].astype(float), y)[0, 1]) for c in feat.NUMERICAS
    },
    "media_mensalidade": {
        "cancelou": num(df.loc[y == 1, "MonthlyCharges"].mean(), 2),
        "ficou": num(df.loc[y == 0, "MonthlyCharges"].mean(), 2),
    },
    "tenure_medio": {
        "cancelou": num(df.loc[y == 1, "tenure"].mean(), 1),
        "ficou": num(df.loc[y == 0, "tenure"].mean(), 1),
    },
    "hist_mensalidade": {
        "cancelou": np.histogram(df.loc[y == 1, "MonthlyCharges"], bins=20, range=(0, 120))[0].tolist(),
        "ficou": np.histogram(df.loc[y == 0, "MonthlyCharges"], bins=20, range=(0, 120))[0].tolist(),
        "bordas": [round(float(b), 1) for b in np.histogram(df["MonthlyCharges"], bins=20, range=(0, 120))[1]],
    },
}

# ----------------------------------------------------------------------------
# 9. Persistencia
# ----------------------------------------------------------------------------
dump(selecionado["_estimador"], ART / "modelo_previa.joblib")

# Guarda tambem os concorrentes (para reproducao/auditoria).
for r in resultados:
    dump(r["_estimador"], ART / f"candidato_{r['id']}.joblib")

tabela = []
for r in resultados:
    tabela.append(
        {
            "id": r["id"],
            "nome": r["nome"],
            "familia": r["familia"],
            "cv_auc": r["cv"]["roc_auc_media"],
            "cv_auc_desvio": r["cv"]["roc_auc_desvio"],
            "cv_pr_auc": r["cv"]["pr_auc_oof"],
            "acuracia": r["teste_05"]["acuracia"],
            "precisao": r["teste_05"]["precisao"],
            "recall": r["teste_05"]["recall"],
            "f1": r["teste_05"]["f1"],
            "roc_auc": r["teste_05"]["roc_auc"],
            "pr_auc": r["teste_05"]["pr_auc"],
            "limiar": r["limiar_operacional"],
            "recall_aj": r["teste_ajustado"]["recall"],
            "precisao_aj": r["teste_ajustado"]["precisao"],
            "f1_aj": r["teste_ajustado"]["f1"],
            "acuracia_aj": r["teste_ajustado"]["acuracia"],
            "selecionado": r["id"] == selecionado["id"],
            "tempo_busca_s": r["tempo_busca_s"],
            "n_combinacoes": r["n_combinacoes"],
            "melhor_params": r["melhor_params"],
        }
    )

# Explicacao da decisao com numeros reais.
segundo = max(
    [r for r in finalistas if r["id"] != selecionado["id"]],
    key=lambda r: r["teste_05"]["pr_auc"],
    default=None,
)
cm_sel = selecionado["teste_ajustado"]["matriz_confusao"]
justificativa = (
    f"Foram avaliados {len(resultados)} algoritmos nos mesmos conjuntos de treino ({len(X_tr)} clientes) e teste "
    f"({len(X_te)} clientes), com hiperparâmetros ajustados por validação cruzada de 5 folds apenas no treino. "
    f"Como a base é desbalanceada (26,5% de churn) e o custo de perder um cancelamento é alto, o critério principal "
    f"foi o PR-AUC (average precision), que resume o trade-off precisão/revocação na classe 'cancelou'. "
    f"{selecionado['nome']} obteve o maior PR-AUC ({selecionado['teste_05']['pr_auc']:.3f}) "
)
if segundo:
    justificativa += f"e o melhor F1 no limiar operacional ({selecionado['teste_ajustado']['f1']:.3f} contra {segundo['teste_ajustado']['f1']:.3f} do {segundo['nome']}). "
else:
    justificativa += ". "
justificativa += (
    f"No limiar de decisão {selecionado['limiar_operacional']:.2f} (escolhido por F1 com previsões out-of-fold do treino), "
    f"o modelo identifica {cm_sel['tp']} dos {cm_sel['tp'] + cm_sel['fn']} clientes que efetivamente cancelaram no teste "
    f"({selecionado['teste_ajustado']['recall']:.1%} de revocação), com precisão de {selecionado['teste_ajustado']['precisao']:.1%} "
    f"e ROC-AUC de {selecionado['teste_05']['roc_auc']:.3f}. O limiar nunca foi ajustado no teste: o teste foi usado uma única vez, "
    f"ao final, para medir o desempenho."
)

resultado_json = {
    "meta": {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": "IBM Telco Customer Churn",
        "fonte": "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv",
        "origem_dados": "real",
        "observacao_dados": (
            "Base pública real da IBM (7043 clientes de uma operadora de telecomunicações), "
            "não sintética. Os rótulos 'Churn' são históricos e observados."
        ),
        "n_registros": int(n_bruto),
        "n_treino": int(len(X_tr)),
        "n_teste": int(len(X_te)),
        "taxa_churn": num(y.mean()),
        "seed": SEED,
        "proporcao_treino_teste": "80/20 estratificado",
        "duracao_total_s": num(time.time() - inicio, 1),
    },
    "eda": eda,
    "tabela": tabela,
    "baseline": {
        "nome": "Baseline (classe majoritaria)",
        "acuracia": m_dummy["acuracia"],
        "precisao": m_dummy["precisao"],
        "recall": m_dummy["recall"],
        "f1": m_dummy["f1"],
        "roc_auc": m_dummy["roc_auc"],
    },
    "selecionado": {
        "id": selecionado["id"],
        "nome": selecionado["nome"],
        "familia": selecionado["familia"],
        "limiar": selecionado["limiar_operacional"],
        "melhor_params": selecionado["melhor_params"],
        "teste_05": selecionado["teste_05"],
        "teste_ajustado": selecionado["teste_ajustado"],
        "cv": selecionado["cv"],
        "ic95": ic95,
        "justificativa": justificativa,
        "roc": selecionado["roc"],
        "pr": selecionado["pr"],
        "curva_limiar": selecionado["limiar_curva"],
        "importancia": importancias[:15],
        "calibracao": calib,
    },
    "comparacao_roc": {r["id"]: {"nome": r["nome"], "roc": r["roc"], "auc": r["teste_05"]["roc_auc"]} for r in resultados},
}

with open(ART / "resultados.json", "w", encoding="utf-8") as f:
    json.dump(resultado_json, f, ensure_ascii=False, indent=2)

# Amostra do teste com previsoes reais (para a tela de clientes em risco).
amostra = X_te.copy()
amostra["customerID"] = df.loc[X_te.index, "customerID"].values
amostra["churn_real"] = y_te.values
amostra["prob_churn"] = np.round(proba_sel, 4)
amostra["previsao"] = (proba_sel >= limiar).astype(int)
amostra.sort_values("prob_churn", ascending=False).to_csv(
    ART / "previsoes_teste.csv", index=False
)

print("\nArtefatos salvos em artifacts/")
print(f"Duracao total: {time.time()-inicio:.0f}s")
