"""Gera o relatorio academico (Markdown) e a tabela comparativa (CSV)
a partir dos resultados reais medidos por src/train.py.

Uso:  python src/gerar_relatorio.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ART = RAIZ / "artifacts"
REL = RAIZ / "reports"
REL.mkdir(exist_ok=True)

with open(ART / "resultados.json", encoding="utf-8") as f:
    R = json.load(f)

meta, eda, sel, tab = R["meta"], R["eda"], R["selecionado"], R["tabela"]
cm = sel["teste_ajustado"]["matriz_confusao"]
pct = lambda x: f"{x * 100:.1f}%".replace(".", ",")
f3 = lambda x: f"{x:.3f}".replace(".", ",")

# --------------------------------------------------------------------------
# CSV comparativo
# --------------------------------------------------------------------------
campos = [
    ("Modelo", "nome"),
    ("ROC-AUC (CV 5 folds)", "cv_auc"),
    ("Desvio ROC-AUC (CV)", "cv_auc_desvio"),
    ("PR-AUC (teste)", "pr_auc"),
    ("Acuracia (0,50)", "acuracia"),
    ("Precisao (0,50)", "precisao"),
    ("Recall (0,50)", "recall"),
    ("F1 (0,50)", "f1"),
    ("ROC-AUC (teste)", "roc_auc"),
    ("Limiar operacional", "limiar"),
    ("Recall (limiar)", "recall_aj"),
    ("Precisao (limiar)", "precisao_aj"),
    ("F1 (limiar)", "f1_aj"),
    ("Selecionado", "selecionado"),
]
with open(REL / "comparacao_modelos.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow([c[0] for c in campos])
    for m in tab:
        w.writerow([m[k] for _, k in campos])

# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------
L = []
a = L.append

a("# PREVIA AI — Ficha do modelo de previsão de churn\n")
a(f"Gerado em **{meta['gerado_em']}** a partir de `artifacts/resultados.json`.\n")
a("## 1. Problema e dados\n")
a(f"- **Tarefa:** classificação binária supervisionada (prever `Churn = Yes`).")
a(f"- **Base:** {meta['dataset']} — {meta['origem_dados']}.")
a(f"- **Fonte:** <{meta['fonte']}>")
a(f"- **Registros:** {meta['n_registros']:,} clientes; {eda['n_colunas_brutas']} colunas originais.")
a(f"- **Atributos usados:** {eda['n_atributos_modelo']} (19 originais + 2 derivados: serviços contratados e cobrança média).")
a(f"- **Distribuição do alvo:** {eda['churn_sim']:,} cancelaram ({pct(meta['taxa_churn'])}) e {eda['churn_nao']:,} permaneceram.")
a(f"- **Qualidade:** {eda['ausentes_totalcharges']} valores em branco em `TotalCharges` (tenure = 0), preenchidos com 0; `customerID` removido.\n")
a("## 2. Protocolo experimental\n")
a(f"1. Divisão estratificada **{meta['proporcao_treino_teste']}** antes de qualquer ajuste: {meta['n_treino']:,} treino / {meta['n_teste']:,} teste.")
a("2. Padronização e one-hot encoding dentro de um `Pipeline`, ajustados **somente no treino**.")
a("3. `GridSearchCV` com 5 folds estratificados no treino, otimizando ROC-AUC.")
a("4. Limiar de decisão escolhido por F1 com previsões **out-of-fold do treino**.")
a("5. Avaliação final única no teste reservado.")
a("6. Intervalos de confiança de 95% por bootstrap (2.000 reamostragens) e importância por permutação.\n")
a("## 3. Algoritmos testados\n")
a("| Algoritmo | Família | Grade de hiperparâmetros | Combinações | Tempo |")
a("|---|---|---|---:|---:|")
for m in tab:
    grade = ", ".join(f"`{k}`" for k in m["melhor_params"])
    a(f"| {m['nome']} | {m['familia']} | {grade} | {m['n_combinacoes']} | {m['tempo_busca_s']}s |")
a("")
a("## 4. Comparação dos resultados (conjunto de teste)\n")
a("| Modelo | ROC-AUC CV | PR-AUC | Acurácia | Precisão | Recall | F1 | ROC-AUC | Limiar | Recall@lim | Precisão@lim | F1@lim |")
a("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for m in tab:
    marca = " **(selecionado)**" if m["selecionado"] else ""
    a(
        f"| {m['nome']}{marca} | {f3(m['cv_auc'])} ± {f3(m['cv_auc_desvio'])} | **{f3(m['pr_auc'])}** | "
        f"{pct(m['acuracia'])} | {pct(m['precisao'])} | {pct(m['recall'])} | {f3(m['f1'])} | {f3(m['roc_auc'])} | "
        f"{m['limiar']:.2f} | {pct(m['recall_aj'])} | {pct(m['precisao_aj'])} | {f3(m['f1_aj'])} |"
    )
b = R["baseline"]
a(
    f"| {b['nome']} | — | {f3(meta['taxa_churn'])}* | {pct(b['acuracia'])} | {pct(b['precisao'])} | "
    f"{pct(b['recall'])} | {f3(b['f1'])} | {f3(b['roc_auc'])} | — | {pct(b['recall'])} | {pct(b['precisao'])} | {f3(b['f1'])} |"
)
a("\n*PR-AUC de um classificador aleatório equivale à prevalência da classe positiva.*\n")
a("## 5. Modelo selecionado\n")
a(f"**{sel['nome']}** — {sel['familia']}.\n")
a(sel["justificativa"] + "\n")
a("### Hiperparâmetros\n")
for k, v in sel["melhor_params"].items():
    a(f"- `{k}` = {v}")
a("\n### Desempenho no teste (limiar operacional)\n")
m = sel["teste_ajustado"]
a(f"| Métrica | Valor | IC 95% |")
a("|---|---:|---|")
a(f"| Acurácia | {pct(m['acuracia'])} | — |")
a(f"| Precisão | {pct(m['precisao'])} | {pct(sel['ic95']['precisao'][0])} – {pct(sel['ic95']['precisao'][1])} |")
a(f"| Recall (classe cancelou) | {pct(m['recall'])} | {pct(sel['ic95']['recall'][0])} – {pct(sel['ic95']['recall'][1])} |")
a(f"| F1-score | {f3(m['f1'])} | {f3(sel['ic95']['f1'][0])} – {f3(sel['ic95']['f1'][1])} |")
a(f"| ROC-AUC | {f3(m['roc_auc'])} | {f3(sel['ic95']['roc_auc'][0])} – {f3(sel['ic95']['roc_auc'][1])} |")
a(f"| PR-AUC | {f3(m['pr_auc'])} | — |")
a(f"| Brier score | {f3(m['brier'])} | — |")
a("")
a("### Matriz de confusão\n")
a("| | Previsto: não | Previsto: sim |")
a("|---|---:|---:|")
a(f"| **Real: não** | {cm['tn']} (VN) | {cm['fp']} (FP) |")
a(f"| **Real: sim** | {cm['fn']} (FN) | {cm['tp']} (VP) |")
a(f"\nDos {cm['tp'] + cm['fn']} clientes que cancelaram no teste, **{cm['tp']} foram sinalizados** ({pct(m['recall'])}).\n")
a("## 6. Importância das variáveis (permutação, queda de ROC-AUC)\n")
a("| Atributo | Queda de ROC-AUC | Desvio |")
a("|---|---:|---:|")
for i in sel["importancia"]:
    a(f"| {i['atributo']} | {f3(i['queda_auc'])} | {f3(i['desvio'])} |")
a("")
a("## 7. Como o Gradient Boosting funciona\n")
a("O modelo é um ensemble aditivo de árvores rasas. Cada árvore é ajustada aos resíduos (gradiente negativo da")
a("entropia cruzada) do conjunto anterior e somada com um fator de aprendizado `ν`:\n")
a("```")
a("F0(x) = log(p / (1 - p))")
a("r_i  = y_i - sigmoid(F_{m-1}(x_i))")
a("F_m(x) = F_{m-1}(x) + ν · h_m(x)")
a("P(churn) = sigmoid(F_M(x))")
a("```\n")
a("Árvores rasas capturam interações simples (por exemplo, contrato mensal **e** pouco tempo de casa) sem decorar o treino.")
a("O número de árvores, a profundidade e a taxa de aprendizado foram escolhidos por validação cruzada.\n")
a("## 8. Limitações\n")
a("- Correlação não implica causalidade: o modelo não prova que alterar um atributo muda o cancelamento.")
a("- Validação aleatória, não temporal: recomenda-se acompanhar drift e retreinar periodicamente.")
a("- Base de uma única operadora de telecomunicações; recalibrar antes de aplicar a outro contexto.")
a("- Probabilidades são estimativas: o intervalo de confiança do recall é amplo.")
a("- Atributos sensíveis (gênero, faixa etária) exigem auditoria de equidade antes de orientar ofertas.\n")
a("## 9. Reprodutibilidade\n")
a("```bash")
a("python src/train.py            # treina, compara e grava os artefatos")
a("python src/gerar_relatorio.py  # regenera esta ficha")
a("python src/api.py              # sobe o painel e a API em http://127.0.0.1:8000")
a("```\n")
a(f"Semente fixa ({meta['seed']}); tempo total de treinamento: {meta['duracao_total_s']}s.")
a("Os resultados acima foram medidos no conjunto de teste e não são ilustrativos.\n")

(REL / "modelo_card.md").write_text("\n".join(L), encoding="utf-8")
print(f"Relatorio salvo em {REL / 'modelo_card.md'}")
print(f"Tabela salva em {REL / 'comparacao_modelos.csv'}")
