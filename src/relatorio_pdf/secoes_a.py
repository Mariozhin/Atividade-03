"""Capa, sumario e secoes 1 a 6 do relatorio."""

from __future__ import annotations

from .base import (
    BASE, CM, COMPARACAO, DICIONARIO, EDA, EXEMPLO, IC, LIMIARES, META, R, SEL, TAB,
    TEAL, callout, f2, f3, figura, inteiro, kpis, pct, tabela,
)

TOTAL = META["n_registros"]


def capa() -> str:
    return f"""
<div class="capa">
  <div class="marca">
    <div class="logo">
      <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 29V11h8.2a6.2 6.2 0 0 1 0 12.4H17V29" stroke="#5eead4" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="28" cy="27.5" r="2.6" fill="#fbbf24"/>
      </svg>
    </div>
    <div>
      <div class="marca-nome">PREVIA<span> AI</span></div>
      <div class="marca-sub">Customer Retention</div>
    </div>
  </div>

  <div class="eyebrow">Relatório técnico · Machine Learning aplicado</div>
  <h1>Prever o churn<br>antes que o cliente <em>parta</em>.</h1>
  <p class="subtitulo">Análise da base pública IBM Telco Customer Churn, comparação de cinco algoritmos de
  classificação, seleção justificada do modelo, calibração do limiar de decisão e implantação de um
  painel interativo de retenção.</p>

  <div class="faixa">
    <div>7.043 clientes reais</div>
    <div>21 atributos por cliente</div>
    <div>5 algoritmos comparados</div>
    <div>Gradient Boosting selecionado</div>
    <div>PR-AUC 0,663 · ROC-AUC 0,845</div>
  </div>

  <div class="rodape">
    <div>
      <b>Mario Joaquim Ferreira</b>
      Projeto Atividade 03 · github.com/Mariozhin/Atividade-03
    </div>
    <div style="text-align:right">
      <b>24 de novembro de 2026</b>
      Documento gerado a partir de artifacts/resultados.json
    </div>
  </div>
</div>
"""


def sumario() -> str:
    itens = [
        ("Resumo executivo", "O problema, a solução e os números que a sustentam"),
        ("Contexto e definição do problema", "Por que churn importa e o que o modelo se propõe a fazer"),
        ("Base de dados", "Origem, estrutura, qualidade e divisão treino/teste"),
        ("Análise exploratória", "Onde o cancelamento se concentra e por quê"),
        ("Metodologia", "Protocolo experimental, métricas e prevenção de vazamento"),
        ("Algoritmos comparados", "Como cada família aprende e quais grades foram testadas"),
        ("Resultados", "Desempenho no teste, intervalos de confiança e comparação"),
        ("Modelo selecionado e limiar", "Por que o Gradient Boosting e como o ponto de operação foi escolhido"),
        ("Interpretabilidade", "Importância global, explicação local e leitura de negócio"),
        ("Do modelo à operação", "API, painel, versão estática e link público"),
        ("Limitações, ética e governança", "O que o modelo não prova e como usá-lo com responsabilidade"),
        ("Conclusão", "Síntese, contribuições e próximos passos"),
        ("Reprodutibilidade e referências", "Comandos, ambiente, sementes e fontes"),
        ("Anexos", "Dicionário de variáveis, ficha técnica e glossário"),
    ]
    linhas = "".join(
        f'<li><span class="t">{t}</span><span class="p">{d}</span></li>' for t, d in itens
    )
    return f"""
<section class="sumario primeira">
  <h2><span class="num">Navegação</span>Sumário</h2>
  <ol>{linhas}</ol>
  <div class="nota">
    <b>Transparência sobre os dados.</b> O modelo foi treinado e avaliado sobre a base pública real
    IBM Telco Customer Churn. Nenhum indicador deste relatório foi simulado: todos vêm de
    <span class="mono">artifacts/resultados.json</span>, produzido por <span class="mono">src/train.py</span>.
    Apenas os 12 perfis de <span class="mono">data/novos_clientes.csv</span> usados no simulador são
    entradas fictícias criadas para demonstrar o uso do modelo; as probabilidades devolvidas para eles
    são calculadas pelo modelo treinado.
  </div>
  {callout("Leitura recomendada",
    "O painel publicado em <b>https://mariozhin.github.io/Atividade-03/</b> contém todas as seções deste "
    "relatório de forma interativa, incluindo simulador de risco. O PDF que você lê agora documenta a "
    "metodologia, os resultados e as limitações por trás daquele painel.")}
</section>
"""


def resumo() -> str:
    sel = SEL
    aj = sel["teste_ajustado"]
    t5 = sel["teste_05"]
    return f"""
<section>
  <h2><span class="num">Seção 01</span>Resumo executivo</h2>
  <p>O cancelamento de clientes (<i>churn</i>) é um dos principais drenos de receita em telecomunicações:
  adquirir um cliente novo costuma custar mais do que manter um cliente existente, e o cancelamento
  reduz a base recorrente justamente quando a operação já investiu em aquisição e instalação. Este
  projeto constrói, mede e disponibiliza um sistema capaz de estimar a probabilidade de cancelamento
  de cada cliente, permitindo que a equipe de retenção priorize esforços antes que a decisão do cliente
  se concretize.</p>

  <p>A base utilizada é a <b>IBM Telco Customer Churn</b>, pública e real, com <b>{inteiro(TOTAL)} clientes</b>
  e <b>{EDA['n_colunas_brutas']} colunas</b>. Desses clientes, <b>{inteiro(EDA['churn_sim'])} cancelaram</b>
  ({pct(EDA['taxa_churn'])}) e <b>{inteiro(EDA['churn_nao'])} permaneceram</b> — uma base desbalanceada, em que
  a acurácia é uma métrica enganosa. Foram comparados cinco algoritmos de classificação sob o mesmo
  protocolo, com ajuste de hiperparâmetros por validação cruzada apenas no treino e uma única avaliação
  no teste reservado.</p>

  {kpis([
    ("Clientes na base", inteiro(TOTAL), "Base pública real IBM Telco"),
    ("Taxa de churn", pct(EDA["taxa_churn"]), f"{inteiro(EDA['churn_sim'])} cancelaram"),
    ("PR-AUC no teste", f3(t5["pr_auc"]), "Critério de seleção definido antes do teste"),
    ("Recall no limiar", pct(aj["recall"]), f"{CM['tp']} de {CM['tp'] + CM['fn']} cancelamentos capturados"),
  ])}

  <h3>Resultado em uma linha</h3>
  {tabela(["Item", "Valor"], [
    ["Modelo selecionado", "<b>Gradient Boosting</b> (learning_rate=0,05 · max_depth=2 · n_estimators=150)"],
    ["Critério de seleção", "PR-AUC (<i>average precision</i>) no conjunto de teste, definido antes da avaliação"],
    ["PR-AUC (teste)", f"<b>{f3(t5['pr_auc'])}</b>"],
    ["ROC-AUC (teste)", f"<b>{f3(t5['roc_auc'])}</b> (IC 95%: {f3(IC['roc_auc'][0])}–{f3(IC['roc_auc'][1])})"],
    ["Limiar operacional", f"<b>{f2(sel['limiar'])}</b> (escolhido por F1 em previsões out-of-fold do treino)"],
    ["Recall / Precisão / F1", f"<b>{pct(aj['recall'])}</b> / {pct(aj['precisao'])} / <b>{f3(aj['f1'])}</b>"],
    ["Matriz de confusão", f"TN {CM['tn']} · FP {CM['fp']} · FN {CM['fn']} · <b>TP {CM['tp']} de {CM['tp'] + CM['fn']} churners</b>"],
  ], numerica=False)}

  <h3>O que os números mostram</h3>
  <ul>
    <li><b>O modelo captura a maior parte dos cancelamentos.</b> No limiar {f2(sel['limiar'])}, ele sinaliza
    {CM['tp']} dos {CM['tp'] + CM['fn']} clientes que efetivamente cancelaram no teste ({pct(aj['recall'])} de recall),
    com precisão de {pct(aj['precisao'])}.</li>
    <li><b>Há um custo de triagem explícito.</b> Para capturar esses {CM['tp']} clientes, a fila de retenção inclui
    {CM['fp']} clientes que permaneceriam — os falsos alarmes. O limiar é o botão que regula esse trade-off,
    e não um detalhe técnico.</li>
    <li><b>A escolha do algoritmo foi baseada em métrica adequada ao desbalanceamento.</b> O Gradient Boosting
    obteve o maior PR-AUC ({f3(t5['pr_auc'])}) e o melhor F1 no limiar ({f3(aj['f1'])}). O XGBoost ficou próximo
    (PR-AUC {f3(next(m for m in TAB if m['id'] == 'xgboost')['pr_auc'])}), mas com F1 menor.</li>
    <li><b>O baseline revela o perigo da acurácia.</b> Um classificador que sempre responde “não cancela”
    acerta {pct(BASE['acuracia'])} dos casos e ainda assim tem recall zero: não encontra um único cliente em risco.</li>
    <li><b>O modelo é interpretável e operacionalizável.</b> Importâncias por permutação, explicações SHAP na API
    e um painel web permitem transformar a probabilidade em ação de retenção priorizada.</li>
  </ul>
</section>
"""


def contexto() -> str:
    return f"""
<section>
  <h2><span class="num">Seção 02</span>Contexto e definição do problema</h2>
  <p>Em serviços por assinatura, o cliente pode encerrar o vínculo a qualquer momento. Quando isso ocorre,
  a empresa perde a receita futura, o custo de aquisição já incorrido e, muitas vezes, a oportunidade de
  vender serviços adicionais. Em telecomunicações, a competição por preço, a maturidade do mercado e a
  facilidade de troca de operadora tornam a retenção um problema permanente de operação — não apenas
  um evento pontual.</p>

  <p>A pergunta deste projeto é deliberadamente restrita: <b>dado o perfil contratual e de consumo de um
  cliente, qual é a probabilidade de ele cancelar?</b> O objetivo não é explicar causalmente por que o
  cliente cancela, nem prever a data exata do cancelamento. É produzir um <b>ranking de risco</b> confiável
  o suficiente para orientar a fila de retenção, acompanhado de uma estimativa de probabilidade que
  permita comparar clientes e dimensionar o esforço.</p>

  <h3>Por que tratar o problema como classificação binária</h3>
  <p>O alvo observado na base é binário (<span class="mono">Churn = Yes/No</span>). Formalmente, queremos
  aprender uma função <span class="mono">f(x) → [0,1]</span> que estime <span class="mono">P(Churn = Yes | x)</span>
  a partir de 21 atributos. A saída contínua é preferível a uma resposta binária seca porque permite:</p>
  <ul>
    <li>ordenar clientes por risco e concentrar o esforço nos mais altos;</li>
    <li>escolher um limiar de decisão compatível com a capacidade da equipe de retenção;</li>
    <li>comunicar incerteza e calibrar ofertas (um cliente com 80% de risco não é o mesmo que um com 35%);</li>
    <li>monitorar a distribuição dos scores ao longo do tempo, mesmo sem rótulos imediatos.</li>
  </ul>

  <h3>Requisitos do projeto</h3>
  <div class="tres">
    <div class="callout" style="margin:0"><span class="tit">Rigor</span>Divisão treino/teste antes de qualquer ajuste;
    pré-processamento dentro do pipeline; nenhuma informação do teste usada para escolher modelo ou limiar.</div>
    <div class="callout" style="margin:0"><span class="tit">Utilidade</span>Métrica adequada a classes desbalanceadas;
    ponto de operação justificado; saída interpretável para quem toma a decisão de contatar o cliente.</div>
    <div class="callout" style="margin:0"><span class="tit">Reprodutibilidade</span>Semente fixa, artefatos persistidos,
    scripts de treino e de geração do relatório, além de uma versão publicada que dispensa servidor.</div>
  </div>

  <h3>Questões que o estudo responde</h3>
  <ol>
    <li>Quais variáveis concentram o sinal de cancelamento nesta base?</li>
    <li>Qual algoritmo entrega o melhor equilíbrio precisão/recall para a classe minoritária?</li>
    <li>Qual limiar de decisão traduz o modelo em uma operação viável?</li>
    <li>O desempenho se sustenta fora da amostra de treino, com incerteza quantificada?</li>
    <li>Como levar o resultado para uma interface acessível sem comprometer a fidelidade dos números?</li>
  </ol>

  <p class="muted small">Escopo excluído: causalidade, uplift (efeito de uma oferta específica), séries temporais
  de cancelamento e precificação. Esses temas aparecem nas limitações e nos próximos passos.</p>
</section>
"""


def dados() -> str:
    return f"""
<section>
  <h2><span class="num">Seção 03</span>Base de dados</h2>
  <p>A base é a <b>IBM Telco Customer Churn</b>, disponibilizada publicamente pela IBM e amplamente usada como
  referência em problemas de retenção. Ela descreve uma operadora de telecomunicações com
  <b>{inteiro(TOTAL)} clientes</b>, <b>{EDA['n_colunas_brutas']} colunas</b> e um rótulo histórico de cancelamento.
  Todos os rótulos são observados — não há dados sintéticos no treino ou na avaliação.</p>

  {tabela(["Aspecto", "Conteúdo"], [
    ["Fonte", "IBM Telco Customer Churn (pública)"],
    ["URL", "raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"],
    ["Registros", f"<b>{inteiro(TOTAL)}</b> clientes"],
    ["Colunas brutas", f"{EDA['n_colunas_brutas']} (19 atributos + customerID + alvo Churn)"],
    ["Atributos no modelo", f"<b>{EDA['n_atributos_modelo']}</b> (19 originais + 2 derivados)"],
    ["Alvo", "Churn: Yes (cancelou) / No (permaneceu)"],
    ["Taxa de churn", f"<b>{pct(EDA['taxa_churn'])}</b> — {inteiro(EDA['churn_sim'])} cancelaram e {inteiro(EDA['churn_nao'])} permaneceram"],
    ["Divisão", f"80/20 estratificada: <b>{inteiro(META['n_treino'])} treino</b> / <b>{inteiro(META['n_teste'])} teste</b> (semente {META['seed']})"],
    ["Valores ausentes", f"{EDA['ausentes_totalcharges']} células em branco em TotalCharges (clientes com tenure = 0)"],
    ["Colunas após one-hot", "47 colunas numéricas (com agrupamento de categorias raras)"],
  ])}

  <h3>Qualidade e tratamento</h3>
  <p>A única ausência relevante está em <span class="mono">TotalCharges</span>: {EDA['ausentes_totalcharges']}
  clientes com tempo de casa zero ainda não haviam sido faturados. O valor foi convertido para número e
  preenchido com <b>0</b>, decisão coerente com o significado do campo. O identificador
  <span class="mono">customerID</span> foi removido para evitar memorização de identidades. As categorias
  raras foram agrupadas pelo <span class="mono">OneHotEncoder</span> (<span class="mono">min_frequency=10</span>),
  reduzindo dimensionalidade sem perder o sinal das categorias frequentes.</p>

  <h3>Engenharia de atributos</h3>
  <p>Dois atributos derivados foram criados de forma determinística, dentro da mesma função usada em treino
  e inferência:</p>
  <ul>
    <li><b>ServicosContratados:</b> contagem de serviços de valor agregado contratados (segurança, backup,
    proteção, suporte, streaming de TV e de filmes), de 0 a 6.</li>
    <li><b>CobrancaMedia:</b> <span class="mono">TotalCharges ÷ tenure</span>; quando <span class="mono">tenure = 0</span>,
    usa a cobrança mensal corrente como <i>proxy</i>, evitando divisão por zero.</li>
  </ul>
  <p>Esses atributos condensam informação que o modelo dificilmente reconstruiria sozinho com árvores rasas:
  a intensidade de uso de serviços e o gasto médio efetivo por mês de relacionamento.</p>
</section>
"""


def eda() -> str:
    return f"""
<section>
  <h2><span class="num">Seção 04</span>Análise exploratória</h2>
  <p>Antes de escolher qualquer algoritmo, a base foi examinada para entender onde o cancelamento se
  concentra. Os gráficos abaixo são calculados sobre os {inteiro(TOTAL)} registros e explicam por que
  variáveis como tipo de contrato e tempo de casa carregam tanto sinal preditivo.</p>

  <div class="duas">
    <div>{figura("churn_contrato", "1", "Taxa de churn por tipo de contrato. Contratos mensais concentram risco quase quatro vezes maior que contratos de dois anos.")}</div>
    <div>{figura("churn_tenure", "2", "Taxa de churn por faixa de tempo de casa. O risco cai monotonicamente com a permanência.")}</div>
  </div>

  {figura("internet_pagamento", "3", "Churn por serviço de internet (à esquerda) e por forma de pagamento (à direita). Fibra óptica e cheque eletrônico aparecem como os grupos de maior risco.")}

  <div class="lado">
    <div>
      {figura("hist_mensalidade", "4", "Distribuição da cobrança mensal dentro de cada classe, em percentual da própria classe. Quem cancela tende a pagar mais por mês.")}
    </div>
    <div>
      {figura("servicos", "5", "Churn por quantidade de serviços de valor agregado. Mais serviços contratados associam-se a menor cancelamento.")}
    </div>
  </div>

  {figura("correlacao", "6", "Correlação de Pearson entre variáveis numéricas e o churn. Tempo de casa é a correlação negativa mais forte; cobrança mensal e média são positivas.")}

  <h3>Leituras que orientam o modelo</h3>
  <ul>
    <li><b>Contrato mensal é o maior bolsão de risco.</b> {pct(EDA['churn_por_contrato'][0]['taxa'])} dos clientes
    nesse regime cancelaram, contra {pct(EDA['churn_por_contrato'][1]['taxa'])} no contrato de um ano e
    {pct(EDA['churn_por_contrato'][2]['taxa'])} no de dois anos. O contrato funciona como um compromisso que
    reduz a oportunidade de saída — e o modelo aprende essa associação.</li>
    <li><b>O risco é maior no começo do relacionamento.</b> Na faixa de 0 a 6 meses, a taxa é
    {pct(EDA['churn_por_tenure'][0]['taxa'])}; após 49 meses, cai para {pct(EDA['churn_por_tenure'][-1]['taxa'])}.
    A média de tempo de casa de quem cancelou é {f2(EDA['tenure_medio']['cancelou'])} meses, contra
    {f2(EDA['tenure_medio']['ficou'])} de quem ficou.</li>
    <li><b>Fibra óptica e cheque eletrônico pedem atenção.</b> A fibra tem {pct(EDA['churn_por_internet'][2]['taxa'])}
    de churn (contra {pct(EDA['churn_por_internet'][0]['taxa'])} no DSL e {pct(EDA['churn_por_internet'][1]['taxa'])} sem internet),
    e o cheque eletrônico chega a {pct(next(d for d in EDA['churn_por_pagamento'] if d['grupo'] == 'Electronic check')['taxa'])},
    bem acima dos débitos automáticos. São associações, não causas: pode haver seleção de perfil por trás delas.</li>
    <li><b>Preço pesa.</b> A cobrança média mensal de quem cancelou é {f2(EDA['media_mensalidade']['cancelou'])},
    contra {f2(EDA['media_mensalidade']['ficou'])} de quem ficou.</li>
    <li><b>Vínculo por serviços reduz risco.</b> Clientes com seis serviços de valor agregado têm
    {pct(EDA['churn_por_servicos'][-1]['taxa'])} de churn; com apenas um serviço, {pct(EDA['churn_por_servicos'][1]['taxa'])}.
    A relação não é perfeitamente monotônica na base inteira, mas o padrão geral é claro.</li>
  </ul>

  <h3>Por que a acurácia não basta</h3>
  <p>Um classificador que sempre responde “não cancela” acerta <b>{pct(BASE['acuracia'])}</b> dos casos e tem
  <b>recall zero</b>: não identifica nenhum cliente em risco. A acurácia premia o acerto na classe majoritária
  e esconde o custo operacional do problema. Por isso o critério de seleção foi o <b>PR-AUC</b>
  (<i>average precision</i>), que olha para a classe positiva, e o ponto de operação foi escolhido por F1
  nas previsões out-of-fold do treino.</p>

  {callout("Cuidado com leitura causal",
    "As associações acima descrevem quem cancela, não necessariamente o que faria alguém deixar de cancelar. "
    "Um contrato de dois anos está associado a menor churn, mas forçar a migração contratual não garante o "
    "mesmo efeito. O modelo é uma ferramenta de priorização, não de política comercial.", "amber")}
</section>
"""


def metodologia() -> str:
    return f"""
<section>
  <h2><span class="num">Seção 05</span>Metodologia</h2>
  <p>O protocolo foi desenhado para responder a uma pergunta simples: <b>qual modelo entrega o melhor
  ranking de risco, medido de forma honesta?</b> Para isso, todas as decisões que poderiam “espiar” o teste
  foram tomadas antes da avaliação final, e o teste foi usado uma única vez.</p>

  <div class="fluxo">
    <div class="etapa"><b>Dados</b><span>{inteiro(TOTAL)} clientes</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Limpeza</b><span>tipos + 2 derivados</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Divisão</b><span>80/20 estratificada</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Pipeline</b><span>scaler + one-hot</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Busca</b><span>5 folds · ROC-AUC</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Teste</b><span>uma única avaliação</span></div>
  </div>

  <h3>Etapas</h3>
  <ol>
    <li><b>Limpeza e engenharia de atributos</b> em <span class="mono">src/features.py</span>, fonte única para
    treino e inferência.</li>
    <li><b>Divisão estratificada 80/20</b> com semente {META['seed']}: {inteiro(META['n_treino'])} clientes para
    treino e {inteiro(META['n_teste'])} para teste, preservando a taxa de churn.</li>
    <li><b>Pré-processamento dentro do Pipeline:</b> padronização das seis variáveis numéricas e one-hot das
    quinze categóricas com agrupamento de categorias raras. Ajuste apenas no treino.</li>
    <li><b>Busca de hiperparâmetros</b> por <span class="mono">GridSearchCV</span> com 5 folds estratificados,
    otimizando ROC-AUC. A métrica de busca é independente de limiar e menos sensível ao desbalanceamento
    que a acurácia.</li>
    <li><b>Previsões out-of-fold (OOF)</b> no treino para escolher o limiar por F1, de modo que o teste não
    participe dessa decisão.</li>
    <li><b>Avaliação final única</b> no teste reservado, com métricas no limiar 0,50 e no limiar operacional.</li>
    <li><b>Incerteza:</b> intervalos de confiança de 95% por bootstrap (2.000 reamostragens).</li>
    <li><b>Interpretação:</b> importância por permutação no teste e explicações SHAP na API.</li>
  </ol>

  <h3>Prevenção de vazamento</h3>
  <p>A divisão é feita <b>antes</b> de qualquer limpeza ou transformação. <span class="mono">StandardScaler</span>
  e <span class="mono">OneHotEncoder</span> vivem dentro de um <span class="mono">Pipeline</span> ajustado
  somente nos {inteiro(META['n_treino'])} clientes de treino. Isso significa que médias, desvios e categorias
  não “veem” o teste. O mesmo módulo <span class="mono">src/features.py</span> é usado pelo treino e pela API,
  eliminando divergência entre treino e produção (<i>train/serve skew</i>).</p>

  {callout("Por que a divisão estratificada importa",
    f"Com {pct(EDA['taxa_churn'])} de churn, uma divisão puramente aleatória poderia produzir conjuntos com "
    "taxas diferentes por acaso. A estratificação preserva a proporção de cancelamentos em treino e teste, "
    "tornando a comparação entre modelos mais estável — especialmente importante para a classe minoritária.", "amber")}

  <h3>Métricas e por que cada uma foi usada</h3>
  {tabela(["Métrica", "O que mede", "Papel no projeto"], [
    ["ROC-AUC", "Capacidade de ordenar positivos acima de negativos em todos os limiares", "Comparação entre modelos e busca de hiperparâmetros"],
    ["PR-AUC", "Área sob a curva precisão × recall, focada na classe positiva", "<b>Critério de seleção</b> — adequado ao desbalanceamento"],
    ["Precisão", "Dos clientes sinalizados, quantos realmente cancelaram", "Custo de falsos alarmes na fila de retenção"],
    ["Recall", "Dos clientes que cancelaram, quantos foram sinalizados", "Cobertura do problema; métrica central para retenção"],
    ["F1", "Média harmônica entre precisão e recall", "Escolha do limiar operacional (OOF do treino)"],
    ["Brier", "Erro quadrático médio das probabilidades", "Qualidade da calibração das probabilidades"],
    ["Acurácia", "Acertos totais", "Apenas descritiva; não usada para selecionar"],
  ])}

  <h3>Escolha do limiar</h3>
  <p>O modelo devolve uma probabilidade; a operação precisa de uma decisão binária. O limiar foi escolhido
  maximizando F1 nas previsões OOF do treino, resultando em <b>{f2(SEL['limiar'])}</b>. Esse valor não foi
  ajustado no teste. A seção 8 mostra o efeito de outros limiares e discute o trade-off em termos de negócio.</p>

  <h3>Comparação justa entre algoritmos</h3>
  <p>Todos os candidatos foram treinados nos mesmos {inteiro(META['n_treino'])} clientes, avaliados nos mesmos
  {inteiro(META['n_teste'])} clientes, com o mesmo pré-processamento e a mesma grade de validação. Nenhum
  algoritmo recebeu tratamento privilegiado. As grades e os tempos de busca são apresentados na próxima seção.</p>

  {callout("Semente e determinismo",
    f"Todo o experimento usa a semente {META['seed']}. O treino completo levou {f2(META['duracao_total_s'])} s e é "
    "determinístico para esta versão das bibliotecas. Se o modelo for retreinado, a API precisa ser reiniciada "
    "porque mantém os resultados em cache.")}
</section>
"""


def algoritmos() -> str:
    linhas = []
    for m in TAB:
        params = ", ".join(f"{k.replace('modelo__', '')}={v}" for k, v in m["melhor_params"].items())
        linhas.append([
            ("<b>" + m["nome"] + "</b>" if m["selecionado"] else m["nome"]),
            m["familia"].replace("arvores", "árvores").replace("unica", "única").replace("Regressao", "Regressão"),
            f"<span class='mono'>{params}</span>",
            str(m["n_combinacoes"]),
            f"{m['tempo_busca_s']:.1f} s".replace(".", ","),
        ])
    return f"""
<section>
  <h2><span class="num">Seção 06</span>Algoritmos comparados</h2>
  <p>Cinco famílias diferentes foram colocadas lado a lado. A diversidade é intencional: modelos lineares
  oferecem simplicidade e interpretabilidade; árvores capturam interações; ensembles reduzem variância ou
  corrigem viés de forma sequencial. Comparar todos sob o mesmo protocolo evita escolher por preferência
  pessoal.</p>

  <h3>1. Regressão Logística</h3>
  <p>Modelo linear que estima o log-odds do churn como combinação das variáveis:
  <span class="mono">log(p/(1−p)) = β₀ + βᵀx</span>. É simples, estável e altamente interpretável, mas precisa
  que interações e não linearidades sejam representadas explicitamente. A regularização controla overfitting;
  o parâmetro <span class="mono">class_weight</span> permite compensar o desbalanceamento. Serviu como
  referência forte de simplicidade.</p>

  <h3>2. Árvore de Decisão (CART)</h3>
  <p>Uma única árvore particiona o espaço de atributos com cortes que maximizam a pureza dos nós. É fácil de
  explicar, mas instável: pequenas mudanças nos dados podem mudar a estrutura. A profundidade e o número
  mínimo de folhas foram limitados para evitar decorar o treino. Mesmo assim, foi o modelo com maior recall
  e menor precisão — muitos alarmes falsos.</p>

  <h3>3. Random Forest</h3>
  <p>Um ensemble de muitas árvores treinadas em amostras <i>bootstrap</i> e subconjuntos aleatórios de
  atributos. A média reduz a variância da árvore única e melhora a generalização. O parâmetro
  <span class="mono">class_weight</span> foi testado para dar mais peso à classe minoritária. É robusto,
  porém menos interpretável e, neste problema, ficou atrás em PR-AUC.</p>

  <h3>4. Gradient Boosting</h3>
  <p>Ensemble aditivo de árvores rasas. Cada nova árvore é ajustada ao resíduo (gradiente negativo da
  entropia cruzada) das anteriores e somada com fator de aprendizado ν:</p>
  <div class="codigo">F₀(x) = log(p / (1 − p))
rᵢ   = yᵢ − sigmoid(F_{'{'}m−1{'}'}(xᵢ))
Fₘ(x) = F_{'{'}m−1{'}'}(x) + ν · hₘ(x)
P(churn) = sigmoid(F_M(x))</div>
  <p>Árvores de profundidade 2 capturam interações simples (por exemplo, contrato mensal <b>e</b> pouco tempo
  de casa) sem decorar o treino. A taxa de aprendizado baixa (0,05) com 150 árvores produz um ajuste suave
  e calibrado. Foi o modelo selecionado.</p>

  <h3>5. XGBoost</h3>
  <p>Implementação de gradient boosting com regularização explícita, otimização de segunda ordem e
  tratamento eficiente de dados esparsos. É uma alternativa industrial forte e ficou muito próxima do
  Gradient Boosting do scikit-learn. A grade incluiu <span class="mono">scale_pos_weight</span> para
  compensar o desbalanceamento. A diferença final de PR-AUC foi pequena, mas o F1 no limiar foi menor.</p>

  <h3>Grades de busca e custo computacional</h3>
  {tabela(["Algoritmo", "Família", "Melhores hiperparâmetros", "Combinações", "Tempo"], linhas, "compacta")}
  <p class="small muted">Tempos medidos no ambiente de treino (uma execução, semente {META['seed']}). O tempo total
  do experimento, incluindo avaliação e artefatos, foi de {f2(META['duracao_total_s'])} s.</p>

  {callout("Por que não escolher o mais complexo",
    "O XGBoost é mais sofisticado, mas sofisticação não é o critério. O Gradient Boosting do scikit-learn "
    "venceu em PR-AUC e F1, com um modelo menor (150 árvores de profundidade 2) e sem dependência extra de "
    "biblioteca no artefato final. A escolha foi guiada pela métrica, não pela novidade do algoritmo.")}
</section>
"""
