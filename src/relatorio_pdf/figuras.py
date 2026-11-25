"""Figuras do relatorio, desenhadas a partir dos artefatos reais."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .base import (
    AMBER, BASE, CM, CV, EDA, FIG, GREEN, LIGHT, RED, R, SEL, SLATE, TAB, TEAL, inteiro, pct,
)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 8.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "axes.edgecolor": "#cfd6df",
    "axes.labelcolor": "#344054",
    "text.color": "#1f2937",
    "xtick.color": "#475467",
    "ytick.color": "#475467",
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.06,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e5e9ef",
    "grid.linewidth": 0.7,
    "axes.axisbelow": True,
})


def salvar(fig, nome: str) -> str:
    caminho = FIG / f"{nome}.png"
    fig.savefig(caminho, facecolor="white")
    plt.close(fig)
    return str(caminho)


def barras_h(grupos, valores, nome, xlabel, cor=TEAL, largura=6.4, altura=2.5,
             fmt=pct, xmax=None, titulo=None):
    fig, ax = plt.subplots(figsize=(largura, altura))
    y = np.arange(len(grupos))[::-1]
    ax.barh(y, valores, color=cor, height=0.62, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(grupos)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(xlabel)
    if titulo:
        ax.set_title(titulo, loc="left")
    limite = xmax if xmax is not None else max(valores) * 1.22
    ax.set_xlim(0, limite)
    for yi, v in zip(y, valores):
        ax.text(v + limite * 0.015, yi, fmt(v), va="center", fontsize=8, color="#344054")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    return salvar(fig, nome)


def fig_contrato():
    dados = EDA["churn_por_contrato"]
    grupos = ["Mensal", "1 ano", "2 anos"]
    return barras_h(grupos, [d["taxa"] for d in dados], "churn_contrato",
                    "% de clientes que cancelaram", titulo="Churn por tipo de contrato")


def fig_tenure():
    dados = EDA["churn_por_tenure"]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    x = np.arange(len(dados))
    ax.bar(x, [d["taxa"] for d in dados], color=TEAL, width=0.6, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d['grupo']} meses" for d in dados])
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    ax.set_ylim(0, 0.62)
    ax.grid(axis="x", visible=False)
    for xi, d in zip(x, dados):
        ax.text(xi, d["taxa"] + 0.012, pct(d["taxa"]), ha="center", fontsize=8, color="#344054")
    ax.set_title("Churn por tempo de casa", loc="left")
    return salvar(fig, "churn_tenure")


def fig_internet_pagamento():
    fig, eixos = plt.subplots(1, 2, figsize=(7.2, 2.7))
    dados = EDA["churn_por_internet"]
    rotulos = {"DSL": "DSL", "Fiber optic": "Fibra óptica", "No": "Sem internet"}
    ax = eixos[0]
    y = np.arange(len(dados))[::-1]
    ax.barh(y, [d["taxa"] for d in dados], color=TEAL, height=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([rotulos[d["grupo"]] for d in dados])
    ax.set_xlim(0, 1.22 * max(d["taxa"] for d in dados))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    ax.grid(axis="y", visible=False)
    for yi, d in zip(y, dados):
        ax.text(d["taxa"] + 0.008, yi, pct(d["taxa"]), va="center", fontsize=8)
    ax.set_title("Por serviço de internet", loc="left")

    dados = EDA["churn_por_pagamento"]
    rotulos = {
        "Bank transfer (automatic)": "Transf. automática",
        "Credit card (automatic)": "Cartão automático",
        "Electronic check": "Cheque eletrônico",
        "Mailed check": "Cheque enviado",
    }
    ax = eixos[1]
    y = np.arange(len(dados))[::-1]
    ax.barh(y, [d["taxa"] for d in dados], color=AMBER, height=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([rotulos[d["grupo"]] for d in dados])
    ax.set_xlim(0, 1.22 * max(d["taxa"] for d in dados))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    ax.grid(axis="y", visible=False)
    for yi, d in zip(y, dados):
        ax.text(d["taxa"] + 0.008, yi, pct(d["taxa"]), va="center", fontsize=8)
    ax.set_title("Por forma de pagamento", loc="left")
    return salvar(fig, "internet_pagamento")


def fig_servicos():
    dados = EDA["churn_por_servicos"]
    fig, ax = plt.subplots(figsize=(6.4, 2.4))
    x = np.arange(len(dados))
    ax.bar(x, [d["taxa"] for d in dados], color=SLATE, width=0.6, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(float(d['grupo']))}" for d in dados])
    ax.set_xlabel("Quantidade de serviços de valor agregado contratados")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    ax.grid(axis="x", visible=False)
    for xi, d in zip(x, dados):
        ax.text(xi, d["taxa"] + 0.012, pct(d["taxa"]), ha="center", fontsize=7.5)
    ax.set_title("Churn por quantidade de serviços contratados", loc="left")
    return salvar(fig, "servicos")


def fig_hist():
    h = EDA["hist_mensalidade"]
    bordas = h["bordas"]
    cancelou = np.array(h["cancelou"], dtype=float)
    ficou = np.array(h["ficou"], dtype=float)
    # densidade dentro de cada classe (as classes têm tamanhos diferentes)
    cancelou = cancelou / cancelou.sum() * 100
    ficou = ficou / ficou.sum() * 100
    centros = [(bordas[i] + bordas[i + 1]) / 2 for i in range(len(bordas) - 1)]
    fig, ax = plt.subplots(figsize=(6.4, 2.7))
    ax.plot(centros, ficou, marker="o", ms=3, lw=1.6, color=SLATE, label="Permaneceu")
    ax.plot(centros, cancelou, marker="o", ms=3, lw=1.6, color=RED, label="Cancelou")
    ax.axvline(EDA["media_mensalidade"]["ficou"], color=SLATE, ls="--", lw=0.9, alpha=0.7)
    ax.axvline(EDA["media_mensalidade"]["cancelou"], color=RED, ls="--", lw=0.9, alpha=0.7)
    ax.text(EDA["media_mensalidade"]["ficou"] - 2, ax.get_ylim()[1] * 0.92,
            f"média {EDA['media_mensalidade']['ficou']:.1f}".replace(".", ","),
            ha="right", fontsize=7, color=SLATE)
    ax.text(EDA["media_mensalidade"]["cancelou"] + 2, ax.get_ylim()[1] * 0.82,
            f"média {EDA['media_mensalidade']['cancelou']:.1f}".replace(".", ","),
            fontsize=7, color=RED)
    ax.set_xlabel("Cobrança mensal")
    ax.set_ylabel("% de clientes da classe")
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("Distribuição da cobrança mensal por desfecho", loc="left")
    return salvar(fig, "hist_mensalidade")


def fig_correlacao():
    dados = EDA["correlacao_numericas"]
    nomes = {
        "SeniorCitizen": "Idoso", "tenure": "Tempo de casa", "MonthlyCharges": "Cobrança mensal",
        "TotalCharges": "Total pago", "ServicosContratados": "Serviços contratados",
        "CobrancaMedia": "Cobrança média",
    }
    itens = sorted(dados.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(6.4, 2.5))
    y = np.arange(len(itens))
    valores = [v for _, v in itens]
    cores = [GREEN if v < 0 else RED for v in valores]
    ax.barh(y, valores, color=cores, height=0.6, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([nomes.get(k, k) for k, _ in itens])
    ax.axvline(0, color="#98a2b3", lw=0.8)
    ax.set_xlim(-0.45, 0.30)
    ax.grid(axis="y", visible=False)
    for yi, v in zip(y, valores):
        ax.text(v + (0.012 if v >= 0 else -0.012), yi, f"{v:+.3f}".replace(".", ","),
                va="center", ha="left" if v >= 0 else "right", fontsize=7.5)
    ax.set_title("Correlação de Pearson com o churn", loc="left")
    return salvar(fig, "correlacao")


def fig_roc():
    cores = {
        "logistica": "#64748b", "arvore": "#a16207", "floresta": "#0e7490",
        "gradient_boosting": TEAL, "xgboost": "#7c3aed",
    }
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    ax.plot([0, 1], [0, 1], ls="--", lw=0.9, color="#b8c0cc", label="Aleatório (0,500)")
    for chave, item in R["comparacao_roc"].items():
        pontos = item["roc"]
        fpr = [p["fpr"] for p in pontos]
        tpr = [p["tpr"] for p in pontos]
        ax.plot(fpr, tpr, lw=1.7 if chave == "gradient_boosting" else 1.1,
                color=cores.get(chave, SLATE), label=f"{item['nome']} ({item['auc']:.3f})".replace(".", ","))
    ax.set_xlabel("Taxa de falsos positivos")
    ax.set_ylabel("Taxa de verdadeiros positivos")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.legend(frameon=False, loc="lower right", fontsize=6.8)
    ax.set_title("Curvas ROC no conjunto de teste", loc="left")
    return salvar(fig, "roc")


def fig_pr():
    pontos = SEL["pr"]
    rec = [p["recall"] for p in pontos]
    prec = [p["precisao"] for p in pontos]
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.plot(rec, prec, lw=1.8, color=TEAL, label=f"Gradient Boosting (PR-AUC {SEL['teste_05']['pr_auc']:.3f})".replace(".", ","))
    ax.axhline(BASE and EDA["taxa_churn"], color=AMBER, ls="--", lw=1,
               label=f"Baseline aleatório ({EDA['taxa_churn']:.3f})".replace(".", ","))
    ax.set_xlabel("Recall (classe cancelou)")
    ax.set_ylabel("Precisão")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.legend(frameon=False, loc="upper right", fontsize=6.8)
    ax.set_title("Curva Precisão × Recall do modelo selecionado", loc="left")
    return salvar(fig, "pr")


def fig_matriz():
    tn, fp, fn, tp = CM["tn"], CM["fp"], CM["fn"], CM["tp"]
    fig, ax = plt.subplots(figsize=(4.1, 3.2))
    matriz = np.array([[tn, fp], [fn, tp]])
    ax.imshow(matriz, cmap="BuGn", alpha=0.82)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Previsto: não", "Previsto: sim"])
    ax.set_yticklabels(["Real: não", "Real: sim"])
    ax.grid(False)
    for i in range(2):
        for j in range(2):
            valor = matriz[i, j]
            cor = "white" if valor > matriz.max() * 0.55 else "#1f2937"
            ax.text(j, i, inteiro(valor), ha="center", va="center", fontsize=15, fontweight="bold", color=cor)
    ax.set_title("Matriz de confusão no teste (limiar 0,34)", loc="left")
    return salvar(fig, "matriz")


def fig_calibracao():
    dados = SEL["calibracao"]
    x = [d["prob_media"] for d in dados]
    y = [d["taxa_observada"] for d in dados]
    fig, ax = plt.subplots(figsize=(4.4, 3.3))
    ax.plot([0, 0.8], [0, 0.8], ls="--", lw=0.9, color="#b8c0cc", label="Calibração perfeita")
    ax.plot(x, y, marker="o", ms=4, lw=1.6, color=TEAL, label="Modelo")
    ax.set_xlabel("Probabilidade média prevista")
    ax.set_ylabel("Frequência observada de churn")
    ax.set_xlim(0, 0.82)
    ax.set_ylim(0, 0.82)
    ax.legend(frameon=False, loc="upper left", fontsize=7)
    ax.set_title("Curva de calibração (10 faixas)", loc="left")
    return salvar(fig, "calibracao")


def fig_limiar():
    lim = [d["limiar"] for d in CV]
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    ax.plot(lim, [d["precisao"] for d in CV], lw=1.5, color=AMBER, label="Precisão")
    ax.plot(lim, [d["recall"] for d in CV], lw=1.5, color=TEAL, label="Recall")
    ax.plot(lim, [d["f1"] for d in CV], lw=1.5, color=SLATE, ls="--", label="F1")
    ax.axvline(SEL["limiar"], color=RED, lw=1, ls=":", label="Limiar operacional 0,34")
    ax.set_xlabel("Limiar de decisão")
    ax.set_ylabel("Valor da métrica")
    ax.set_xlim(0.05, 0.9)
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, loc="lower left", ncol=2, fontsize=7)
    ax.set_title("Precisão, recall e F1 ao longo do limiar (teste)", loc="left")
    return salvar(fig, "limiar")


def fig_importancia():
    dados = SEL["importancia"][:12]
    nomes = {
        "tenure": "Tempo de casa", "Contract": "Contrato", "InternetService": "Internet",
        "OnlineSecurity": "Segurança online", "TechSupport": "Suporte", "PaymentMethod": "Pagamento",
        "TotalCharges": "Total pago", "PaperlessBilling": "Fatura digital",
        "MultipleLines": "Múltiplas linhas", "SeniorCitizen": "Idoso",
        "MonthlyCharges": "Cobrança mensal", "OnlineBackup": "Backup online",
        "Dependents": "Dependentes", "ServicosContratados": "Serviços",
        "StreamingTV": "Streaming TV",
    }
    dados = sorted(dados, key=lambda d: d["queda_auc"])
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    y = np.arange(len(dados))
    ax.barh(y, [d["queda_auc"] for d in dados], xerr=[d["desvio"] for d in dados],
            color=TEAL, height=0.62, error_kw={"ecolor": "#98a2b3", "lw": 0.8}, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([nomes.get(d["atributo"], d["atributo"]) for d in dados])
    ax.set_xlabel("Queda de ROC-AUC ao embaralhar o atributo")
    ax.grid(axis="y", visible=False)
    for yi, d in zip(y, dados):
        ax.text(d["queda_auc"] + d["desvio"] + 0.0008, yi, f"{d['queda_auc']:.3f}".replace(".", ","),
                va="center", fontsize=7.5)
    ax.set_title("Importância por permutação no teste (média ± desvio)", loc="left")
    return salvar(fig, "importancia")


def fig_comparacao():
    nomes = [m["nome"] for m in TAB]
    cores = {"gradient_boosting": TEAL, "xgboost": "#7c3aed", "floresta": "#0e7490",
             "arvore": "#a16207", "logistica": "#94a3b8"}
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    x = np.arange(len(TAB))
    larg = 0.36
    ax.bar(x - larg / 2, [m["pr_auc"] for m in TAB], larg, color=[cores[m["id"]] for m in TAB],
           label="PR-AUC", zorder=3)
    ax.bar(x + larg / 2, [m["f1_aj"] for m in TAB], larg, color="#cbd5e1", label="F1 no limiar", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("Regressao Logistica", "Reg. logística") for n in nomes], fontsize=7.5)
    ax.set_ylim(0, 0.8)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, ncol=2, loc="upper right", fontsize=7)
    for xi, m in zip(x, TAB):
        ax.text(xi - larg / 2, m["pr_auc"] + 0.012, f"{m['pr_auc']:.3f}".replace(".", ","), ha="center", fontsize=6.5)
        ax.text(xi + larg / 2, m["f1_aj"] + 0.012, f"{m['f1_aj']:.3f}".replace(".", ","), ha="center", fontsize=6.5)
    ax.set_title("PR-AUC e F1 por algoritmo (conjunto de teste)", loc="left")
    return salvar(fig, "comparacao")


def gerar_todas() -> None:
    fig_contrato()
    fig_tenure()
    fig_internet_pagamento()
    fig_servicos()
    fig_hist()
    fig_correlacao()
    fig_roc()
    fig_pr()
    fig_matriz()
    fig_calibracao()
    fig_limiar()
    fig_importancia()
    fig_comparacao()
