# PREVIA AI — Ficha do modelo de previsão de churn

Gerado em **2026-11-24T14:00:40+00:00** a partir de `artifacts/resultados.json`.

## 1. Problema e dados

- **Tarefa:** classificação binária supervisionada (prever `Churn = Yes`).
- **Base:** IBM Telco Customer Churn — real.
- **Fonte:** <https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv>
- **Registros:** 7,043 clientes; 21 colunas originais.
- **Atributos usados:** 21 (19 originais + 2 derivados: serviços contratados e cobrança média).
- **Distribuição do alvo:** 1,869 cancelaram (26,5%) e 5,174 permaneceram.
- **Qualidade:** 11 valores em branco em `TotalCharges` (tenure = 0), preenchidos com 0; `customerID` removido.

## 2. Protocolo experimental

1. Divisão estratificada **80/20 estratificado** antes de qualquer ajuste: 5,634 treino / 1,409 teste.
2. Padronização e one-hot encoding dentro de um `Pipeline`, ajustados **somente no treino**.
3. `GridSearchCV` com 5 folds estratificados no treino, otimizando ROC-AUC.
4. Limiar de decisão escolhido por F1 com previsões **out-of-fold do treino**.
5. Avaliação final única no teste reservado.
6. Intervalos de confiança de 95% por bootstrap (2.000 reamostragens) e importância por permutação.

## 3. Algoritmos testados

| Algoritmo | Família | Grade de hiperparâmetros | Combinações | Tempo |
|---|---|---|---:|---:|
| Regressao Logistica | Modelo linear (regressao logistica) | `C`, `class_weight` | 6 | 4.3s |
| Arvore de Decisao | Arvore unica (CART) | `class_weight`, `max_depth`, `min_samples_leaf` | 24 | 1.5s |
| Random Forest | Ensemble de arvores (bagging) | `class_weight`, `max_depth`, `max_features`, `min_samples_leaf` | 8 | 7.4s |
| Gradient Boosting | Ensemble de arvores (boosting) | `learning_rate`, `max_depth`, `n_estimators` | 8 | 9.2s |
| XGBoost | Gradient boosting regularizado | `learning_rate`, `max_depth`, `n_estimators`, `scale_pos_weight` | 16 | 6.6s |

## 4. Comparação dos resultados (conjunto de teste)

| Modelo | ROC-AUC CV | PR-AUC | Acurácia | Precisão | Recall | F1 | ROC-AUC | Limiar | Recall@lim | Precisão@lim | F1@lim |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Regressao Logistica | 0,846 ± 0,013 | **0,628** | 80,4% | 65,3% | 55,9% | 0,602 | 0,841 | 0.34 | 71,4% | 54,0% | 0,615 |
| Arvore de Decisao | 0,832 ± 0,014 | **0,628** | 75,4% | 52,6% | 75,9% | 0,621 | 0,836 | 0.59 | 73,5% | 54,4% | 0,625 |
| Random Forest | 0,847 ± 0,009 | **0,652** | 75,2% | 52,1% | 77,8% | 0,625 | 0,841 | 0.48 | 79,4% | 51,7% | 0,627 |
| Gradient Boosting **(selecionado)** | 0,850 ± 0,012 | **0,663** | 79,7% | 65,3% | 50,3% | 0,568 | 0,845 | 0.34 | 72,5% | 57,0% | 0,638 |
| XGBoost | 0,848 ± 0,011 | **0,658** | 80,5% | 66,5% | 53,5% | 0,593 | 0,844 | 0.32 | 75,7% | 54,2% | 0,632 |
| Baseline (classe majoritaria) | — | 0,265* | 73,5% | 0,0% | 0,0% | 0,000 | 0,500 | — | 0,0% | 0,0% | 0,000 |

*PR-AUC de um classificador aleatório equivale à prevalência da classe positiva.*

## 5. Modelo selecionado

**Gradient Boosting** — Ensemble de arvores (boosting).

Foram avaliados 5 algoritmos nos mesmos conjuntos de treino (5634 clientes) e teste (1409 clientes), com hiperparâmetros ajustados por validação cruzada de 5 folds apenas no treino. Como a base é desbalanceada (26,5% de churn) e o custo de perder um cancelamento é alto, o critério principal foi o PR-AUC (average precision), que resume o trade-off precisão/revocação na classe 'cancelou'. Gradient Boosting obteve o maior PR-AUC (0.663) e o melhor F1 no limiar operacional (0.638 contra 0.632 do XGBoost). No limiar de decisão 0.34 (escolhido por F1 com previsões out-of-fold do treino), o modelo identifica 271 dos 374 clientes que efetivamente cancelaram no teste (72.5% de revocação), com precisão de 57.0% e ROC-AUC de 0.845. O limiar nunca foi ajustado no teste: o teste foi usado uma única vez, ao final, para medir o desempenho.

### Hiperparâmetros

- `learning_rate` = 0.05
- `max_depth` = 2
- `n_estimators` = 150

### Desempenho no teste (limiar operacional)

| Métrica | Valor | IC 95% |
|---|---:|---|
| Acurácia | 78,2% | — |
| Precisão | 57,0% | 52,4% – 61,4% |
| Recall (classe cancelou) | 72,5% | 67,7% – 76,9% |
| F1-score | 0,638 | 0,598 – 0,676 |
| ROC-AUC | 0,845 | 0,822 – 0,866 |
| PR-AUC | 0,663 | — |
| Brier score | 0,136 | — |

### Matriz de confusão

| | Previsto: não | Previsto: sim |
|---|---:|---:|
| **Real: não** | 831 (VN) | 204 (FP) |
| **Real: sim** | 103 (FN) | 271 (VP) |

Dos 374 clientes que cancelaram no teste, **271 foram sinalizados** (72,5%).

## 6. Importância das variáveis (permutação, queda de ROC-AUC)

| Atributo | Queda de ROC-AUC | Desvio |
|---|---:|---:|
| tenure | 0,061 | 0,005 |
| Contract | 0,052 | 0,006 |
| InternetService | 0,013 | 0,004 |
| OnlineSecurity | 0,005 | 0,002 |
| TechSupport | 0,004 | 0,002 |
| PaymentMethod | 0,003 | 0,001 |
| TotalCharges | 0,003 | 0,001 |
| PaperlessBilling | 0,003 | 0,001 |
| MultipleLines | 0,002 | 0,001 |
| SeniorCitizen | 0,001 | 0,001 |
| MonthlyCharges | 0,001 | 0,001 |
| OnlineBackup | 0,000 | 0,001 |
| Dependents | 0,000 | 0,000 |
| ServicosContratados | 0,000 | 0,000 |
| StreamingTV | 0,000 | 0,000 |

## 7. Como o Gradient Boosting funciona

O modelo é um ensemble aditivo de árvores rasas. Cada árvore é ajustada aos resíduos (gradiente negativo da
entropia cruzada) do conjunto anterior e somada com um fator de aprendizado `ν`:

```
F0(x) = log(p / (1 - p))
r_i  = y_i - sigmoid(F_{m-1}(x_i))
F_m(x) = F_{m-1}(x) + ν · h_m(x)
P(churn) = sigmoid(F_M(x))
```

Árvores rasas capturam interações simples (por exemplo, contrato mensal **e** pouco tempo de casa) sem decorar o treino.
O número de árvores, a profundidade e a taxa de aprendizado foram escolhidos por validação cruzada.

## 8. Limitações

- Correlação não implica causalidade: o modelo não prova que alterar um atributo muda o cancelamento.
- Validação aleatória, não temporal: recomenda-se acompanhar drift e retreinar periodicamente.
- Base de uma única operadora de telecomunicações; recalibrar antes de aplicar a outro contexto.
- Probabilidades são estimativas: o intervalo de confiança do recall é amplo.
- Atributos sensíveis (gênero, faixa etária) exigem auditoria de equidade antes de orientar ofertas.

## 9. Reprodutibilidade

```bash
python src/train.py            # treina, compara e grava os artefatos
python src/gerar_relatorio.py  # regenera esta ficha
python src/api.py              # sobe o painel e a API em http://127.0.0.1:8000
```

Semente fixa (42); tempo total de treinamento: 41.3s.
Os resultados acima foram medidos no conjunto de teste e não são ilustrativos.
