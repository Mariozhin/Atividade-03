# PREVIA AI — Previsão de Churn

Sistema acadêmico de previsão de cancelamento de clientes (churn) para uma operadora de
telecomunicações. Inclui a análise exploratória, a comparação de cinco algoritmos de
classificação, a seleção justificada do modelo, a integração em uma API de produção e um
painel web interativo.

> **Transparência sobre os dados.** O modelo foi treinado e avaliado sobre a **base pública
> real IBM Telco Customer Churn** (7.043 clientes, 21 colunas, 26,5% de churn). Nenhum
> resultado deste repositório é simulado. Apenas os 12 perfis de `data/novos_clientes.csv`
> usados no simulador são **entradas fictícias** criadas para demonstrar o uso do modelo em
> clientes novos — as probabilidades devolvidas para eles são reais, calculadas pelo modelo
> treinado.

---

## 1. Resultado em uma linha

| Item | Valor |
|---|---|
| Modelo selecionado | **Gradient Boosting** (`learning_rate=0.05`, `max_depth=2`, `n_estimators=150`) |
| Critério de seleção | **PR-AUC (average precision)** no conjunto de teste, definido antes da avaliação |
| PR-AUC (teste) | **0,663** |
| ROC-AUC (teste) | **0,845** (IC 95%: 0,822–0,866) |
| Limiar operacional | **0,34** (escolhido por F1 em previsões out-of-fold do treino) |
| Recall / Precisão / F1 | **72,5%** / **57,1%** / **0,638** |
| Matriz de confusão (teste) | TN 831 · FP 204 · FN 103 · **TP 271 de 374 churners** |

---

## 2. Base de dados

- **Fonte:** IBM Telco Customer Churn (pública, real).
  `https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv`
- **Registros:** 7.043 clientes · **Alvo:** `Churn` (Sim/Não) · **Taxa de churn:** 26,54%
- **Atributos:** 19 atributos originais + 2 derivados (`ServicosContratados`, `CobrancaMedia`)
  = **21 atributos por cliente** (a base bruta tem 21 colunas, incluindo `customerID` e o
  alvo `Churn`); após one-hot encoding, 47 colunas numéricas.
- **Divisão:** 80/20 estratificada → 5.634 treino / 1.409 teste (semente 42).
- **Sem vazamento:** limpeza, engenharia de atributos, `StandardScaler` e `OneHotEncoder`
  (com `min_frequency=10`) vivem dentro de um `Pipeline` ajustado **apenas** no treino.

---

## 3. Comparação dos modelos

Todos avaliados nos **mesmos** conjuntos de treino e teste, com hiperparâmetros ajustados por
`GridSearchCV` (5 folds estratificados, métrica `roc_auc`) somente no treino.

| Modelo | ROC-AUC (CV) | PR-AUC (teste) | F1 no limiar | Recall no limiar | Precisão no limiar |
|---|---|---|---|---|---|
| Regressão Logística | 0,846 ± 0,013 | 0,628 | 0,615 | 71,4% | 54,1% |
| Árvore de Decisão | 0,832 ± 0,014 | 0,628 | 0,625 | 73,5% | 54,4% |
| Random Forest | 0,847 ± 0,009 | 0,652 | 0,627 | 79,4% | 51,7% |
| **Gradient Boosting** | **0,850 ± 0,012** | **0,663** | **0,638** | 72,5% | 57,1% |
| XGBoost | 0,848 ± 0,011 | 0,658 | 0,632 | 75,7% | 54,2% |
| *Baseline (tudo "não cancela")* | — | 0,265 | — | 0% | — |

O baseline ilustra o problema: acertar 73,5% dos casos sem nenhum modelo, mas **sem detectar
um único cancelamento**. Por isso a acurácia não foi usada como critério.

**Por que Gradient Boosting:** maior PR-AUC (métrica adequada a classes desbalanceadas, pois
foca na classe positiva) e maior F1 no limiar operacional. O XGBoost ficou muito próximo
(0,658), mas com F1 menor; o Random Forest tem recall alto porém precisão baixa (mais alarmes
falsos); a Regressão Logística é competitiva e mais simples, porém fica atrás nas duas
métricas principais. Os detalhes completos, incluindo intervalos de confiança por bootstrap e
curvas de calibração, estão em `reports/modelo_card.md`.

---

## 4. Estrutura do projeto

```
.
├── data/
│   ├── Telco-Customer-Churn.csv   # base real (IBM)
│   └── novos_clientes.csv         # 12 perfis fictícios para o simulador
├── src/
│   ├── features.py                # limpeza + engenharia de atributos (fonte única)
│   ├── train.py                   # treino, comparação, seleção e artefatos
│   ├── gerar_relatorio.py         # gera o model card e a tabela CSV
│   └── api.py                     # FastAPI: serve o painel e as previsões
├── web/
│   ├── index.html                 # SPA com 6 seções
│   ├── styles.css
│   └── app.js                     # gráficos SVG, simulador, explicações SHAP
├── artifacts/
│   ├── modelo_previa.joblib       # modelo selecionado + pipeline completo
│   ├── candidato_*.joblib         # os 5 modelos treinados
│   ├── resultados.json            # todas as métricas medidas
│   └── previsoes_teste.csv        # previsões no conjunto de teste
└── reports/
    ├── modelo_card.md             # documentação acadêmica do modelo
    └── comparacao_modelos.csv
```

---

## 5. Como executar

Requisitos: Python 3.11+ com `pandas`, `numpy`, `scikit-learn`, `xgboost`, `shap`,
`fastapi`, `uvicorn`, `joblib`, `matplotlib`.

```bash
pip install pandas numpy scikit-learn xgboost shap fastapi uvicorn joblib matplotlib
```

```bash
# 1) Treinar, comparar, selecionar e gravar os artefatos (~40 s)
python src/train.py

# 2) Gerar o model card e a tabela comparativa
python src/gerar_relatorio.py

# 3) Subir a API + painel
python src/api.py
# abra http://127.0.0.1:8000
```

> O treino é determinístico (semente 42). Se retreinar, **reinicie a API**, pois ela mantém
> `resultados.json` em cache.

---

## 6. API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/saude` | Status do serviço e do modelo |
| GET | `/api/modelo-info` | Metadados do modelo em produção |
| GET | `/api/resultados` | Métricas completas (consumidas pelo painel) |
| GET | `/api/novos-clientes` | Previsões em lote para `data/novos_clientes.csv` |
| GET | `/api/amostra-teste` | Amostra do conjunto de teste |
| POST | `/api/prever` | Probabilidade de churn para um cliente + explicação SHAP |
| POST | `/api/prever-lote` | Probabilidade para uma lista de clientes |

Exemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/prever \
  -H "Content-Type: application/json" \
  -d '{"gender":"Female","SeniorCitizen":0,"Partner":"No","Dependents":"No",
       "tenure":2,"PhoneService":"Yes","MultipleLines":"No",
       "InternetService":"Fiber optic","OnlineSecurity":"No","OnlineBackup":"No",
       "DeviceProtection":"No","TechSupport":"No","StreamingTV":"No",
       "StreamingMovies":"No","Contract":"Month-to-month","PaperlessBilling":"Yes",
       "PaymentMethod":"Electronic check","MonthlyCharges":95.5,"TotalCharges":190.0}'
```

A resposta inclui a probabilidade, a faixa de risco (`critico`/`alto`/`moderado`/`baixo`)
e as contribuições SHAP convertidas em pontos percentuais.

---

## 7. Painel web

Seis seções: **Visão geral**, **Base de dados**, **Análise exploratória**, **Modelo de
Machine Learning** (algoritmos testados, comparação, métricas, matriz de confusão, curva de
limiar, importância de atributos, explicação didática e ficha técnica), **Simulador de
risco** (formulário + medidor + SHAP) e **Clientes em risco** (ranking da base).

---

## 8. Limitações

- Correlação não é causalidade: o modelo identifica associação estatística, não o motivo do
  cancelamento.
- A validação é aleatória, não temporal; em produção recomenda-se validar em um período
  futuro para medir deriva (drift).
- Base de uma única operadora: padrões podem não se transferir para outro mercado.
- Probabilidade ≠ certeza: o IC 95% do recall vai de 67,7% a 76,9%; decisões individuais
  devem combinar o score com julgamento humano.
- Atributos sensíveis (gênero, faixa etária) entram como variáveis; o uso em ofertas deve
  passar por auditoria de equidade antes de virar política comercial.
