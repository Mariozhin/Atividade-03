"""Secoes 7 a 10: resultados, modelo selecionado, interpretabilidade e operacao."""

from __future__ import annotations

from .base import (
    BASE, CM, COMPARACAO, CV, EDA, EXEMPLO, IC, LIMIARES, META, NOMES, SEL, TAB,
    callout, f2, f3, figura, inteiro, kpis, pct, tabela,
)

AJ = SEL["teste_ajustado"]
T5 = SEL["teste_05"]


def resultados() -> str:
    linhas = []
    for m in COMPARACAO:
        nome = f"<b>{m['nome']}</b>" if m["selecionado"] else m["nome"]
        linhas.append([
            nome,
            f"{f3(m['cv_auc'])} ± {f3(m['cv_auc_desvio'])}",
            f"<b>{f3(m['pr_auc'])}</b>",
            f3(m["roc_auc"]),
            f3(m["f1_aj"]),
            pct(m["recall_aj"]),
            pct(m["precisao_aj"]),
            f2(m["limiar"]),
        ])
    linhas.append([
        BASE["nome"], "—", f3(EDA["taxa_churn"]) + "*", f3(BASE["roc_auc"]), "—", "0,0%", "—", "—",
    ])
    return f"""
<section>
  <h2><span class="num">Seção 07</span>Resultados</h2>
  <p>Todos os modelos foram avaliados no mesmo conjunto de {inteiro(META['n_teste'])} clientes, que não participou
  do treino nem da escolha de hiperparâmetros ou limiar. A tabela ordena os modelos pelo critério de seleção
  definido antes do teste: PR-AUC.</p>

  {kpis([
    ("PR-AUC do selecionado", f3(T5["pr_auc"]), "Maior entre os cinco modelos"),
    ("ROC-AUC do selecionado", f3(T5["roc_auc"]), f"IC 95%: {f3(IC['roc_auc'][0])}–{f3(IC['roc_auc'][1])}"),
    ("Recall no limiar 0,34", pct(AJ["recall"]), f"{CM['tp']} de {CM['tp'] + CM['fn']} cancelamentos"),
    ("Falsos positivos", inteiro(CM["fp"]), f"Precisão de {pct(AJ['precisao'])}"),
  ])}

  {tabela(
    ["Modelo", "ROC-AUC (CV)", "PR-AUC", "ROC-AUC", "F1@limiar", "Recall@limiar", "Precisão@limiar", "Limiar"],
    linhas, "compacta", numerica=True,
  )}
  <p class="small muted">* O PR-AUC de um classificador aleatório equivale à prevalência da classe positiva
  ({pct(EDA['taxa_churn'])}). ROC-AUC de CV é a média de 5 folds no treino; as demais métricas são do teste.
  F1, recall e precisão usam o limiar operacional de cada modelo, escolhido por F1 out-of-fold no treino.</p>

  <div class="duas">
    <div>{figura("roc", "7", "Curvas ROC dos cinco modelos no teste. O Gradient Boosting (linha grossa) tem a maior área, mas a diferença em relação a Random Forest e XGBoost é pequena.")}</div>
    <div>{figura("pr", "8", "Curva precisão × recall do modelo selecionado. A linha tracejada é o desempenho de um classificador aleatório (prevalência de 26,5%).")}</div>
  </div>

  {figura("comparacao", "9", "PR-AUC e F1 no limiar por algoritmo. O Gradient Boosting combina o maior PR-AUC com o maior F1; Random Forest tem recall alto, mas precisão baixa.")}

  <h3>Leitura dos resultados</h3>
  <ul>
    <li><b>Gradient Boosting venceu nas duas métricas que importam.</b> PR-AUC {f3(T5['pr_auc'])} e F1
    {f3(AJ['f1'])} no limiar operacional. O XGBoost ficou a {f3(T5['pr_auc'] - next(m for m in TAB if m['id'] == 'xgboost')['pr_auc'])}
    de PR-AUC, mas com F1 {f3(next(m for m in TAB if m['id'] == 'xgboost')['f1_aj'])}.</li>
    <li><b>Random Forest prioriza recall.</b> Sinaliza {pct(next(m for m in TAB if m['id'] == 'floresta')['recall_aj'])}
    dos cancelamentos, porém com precisão de {pct(next(m for m in TAB if m['id'] == 'floresta')['precisao_aj'])}:
    mais clientes corretos encontrados, mais falsos alarmes. Para uma equipe com capacidade limitada, isso
    pode ser pior do que o Gradient Boosting.</li>
    <li><b>A árvore única é instável.</b> Alto recall e baixa precisão, com ROC-AUC inferior. É um exemplo
    clássico de modelo que reage bem à classe minoritária, mas paga o preço em alarmes falsos.</li>
    <li><b>A regressão logística é competitiva.</b> Com apenas 6 combinações de hiperparâmetros, alcança
    PR-AUC {f3(next(m for m in TAB if m['id'] == 'logistica')['pr_auc'])}. Se a interpretabilidade linear fosse
    requisito absoluto, seria uma alternativa defensável.</li>
    <li><b>O ganho do modelo sobre o acaso é grande.</b> O PR-AUC de {f3(T5['pr_auc'])} é cerca de
    {f2(T5['pr_auc'] / EDA['taxa_churn'])}× a prevalência; o ROC-AUC de {f3(T5['roc_auc'])} confirma boa
    separação global.</li>
  </ul>

  <h3>Incerteza das estimativas</h3>
  <p>Um número único esconde a variabilidade amostral. Os intervalos de confiança de 95% por bootstrap
  (2.000 reamostragens do teste) mostram a faixa plausível para cada métrica do modelo selecionado:</p>
  {tabela(["Métrica", "Estimativa", "IC 95%"], [
    ["Recall (cancelou)", f"<b>{pct(AJ['recall'])}</b>", f"{pct(IC['recall'][0])} – {pct(IC['recall'][1])}"],
    ["Precisão", pct(AJ['precisao']), f"{pct(IC['precisao'][0])} – {pct(IC['precisao'][1])}"],
    ["F1", f"<b>{f3(AJ['f1'])}</b>", f"{f3(IC['f1'][0])} – {f3(IC['f1'][1])}"],
    ["ROC-AUC", f3(T5['roc_auc']), f"{f3(IC['roc_auc'][0])} – {f3(IC['roc_auc'][1])}"],
    ["PR-AUC", f3(T5['pr_auc']), "— (não bootstrapped no artefato)"],
    ["Brier", f3(T5['brier']), "—"],
  ], "compacta", numerica=True)}
  <p>O recall pode variar de {pct(IC['recall'][0])} a {pct(IC['recall'][1])} em outra amostra do mesmo processo.
  Isso é relevante para expectativas operacionais: prometer “capturamos 72%” sem essa faixa seria
  excesso de confiança. A decisão individual deve combinar o score com julgamento humano.</p>

  <h3>Calibração</h3>
  <p>O Brier score de {f3(T5['brier'])} e a curva de calibração mostram que as probabilidades não são apenas
  um ranking: elas aproximam a frequência observada. Nas faixas altas, a taxa observada de churn acompanha
  a probabilidade prevista; nas faixas baixas há alguma subestimação, mas o modelo não produz probabilidades
  absurdas. Isso permite usar o score para dimensionar a fila de retenção.</p>
  {figura("calibracao", "10", "Curva de calibração em 10 faixas de probabilidade. A diagonal tracejada representa calibração perfeita; os pontos seguem de perto a diagonal nas faixas de risco alto.")}
</section>
"""


def modelo_limiar() -> str:
    linhas = []
    for item in LIMIARES:
        destaque = abs(item["limiar"] - SEL["limiar"]) < 1e-9
        linha = [
            f"<b>{f2(item['limiar'])}</b>" if destaque else f2(item["limiar"]),
            inteiro(item["acionados"]),
            inteiro(item["tp"]),
            inteiro(item["fp"]),
            inteiro(item["fn"]),
            pct(item["recall"]),
            pct(item["precisao"]),
            f3(item["f1"]),
        ]
        if destaque:
            linha = [f'<span class="destaque">{c}</span>' for c in linha]
        linhas.append(linha)
    return f"""
<section>
  <h2><span class="num">Seção 08</span>Modelo selecionado e limiar de decisão</h2>
  <p>O modelo escolhido é o <b>Gradient Boosting</b> com <span class="mono">learning_rate=0,05</span>,
  <span class="mono">max_depth=2</span> e <span class="mono">n_estimators=150</span>. Ele é um ensemble de
  150 árvores rasas que se corrigem sequencialmente; a baixa profundidade limita a capacidade de decorar
  o treino, e a taxa de aprendizado pequena suaviza o ajuste.</p>

  <h3>Justificativa da escolha</h3>
  <p>O critério foi definido antes da avaliação: maior PR-AUC no teste. O Gradient Boosting obteve
  <b>{f3(T5['pr_auc'])}</b>, à frente de XGBoost ({f3(next(m for m in TAB if m['id'] == 'xgboost')['pr_auc'])}),
  Random Forest ({f3(next(m for m in TAB if m['id'] == 'floresta')['pr_auc'])}), Árvore de Decisão
  ({f3(next(m for m in TAB if m['id'] == 'arvore')['pr_auc'])}) e Regressão Logística
  ({f3(next(m for m in TAB if m['id'] == 'logistica')['pr_auc'])}). Como desempate e validação de utilidade,
  também apresentou o maior F1 no limiar operacional ({f3(AJ['f1'])}). A escolha não foi feita olhando o
  teste repetidamente: o teste foi aberto uma vez, ao final.</p>

  {kpis([
    ("Acurácia", pct(AJ["acuracia"]), "No limiar 0,34"),
    ("Precisão", pct(AJ["precisao"]), "Dos sinalizados, quantos cancelaram"),
    ("Recall", pct(AJ["recall"]), "Dos cancelamentos, quantos foram vistos"),
    ("F1", f3(AJ["f1"]), "Equilíbrio precisão/recall"),
  ])}

  <h3>O limiar como decisão de negócio</h3>
  <p>O limiar de 0,34 foi escolhido maximizando F1 nas previsões out-of-fold do treino. Ele não é sagrado:
  se a equipe de retenção tem pouca capacidade, subir o limiar reduz falsos alarmes e aumenta a precisão,
  ao custo de deixar passar mais cancelamentos. Se o custo de perder um cliente é muito alto, descer o
  limiar amplia a cobertura. A tabela abaixo, calculada sobre as probabilidades reais do teste, mostra o
  efeito concreto dessa escolha:</p>

  {tabela(
    ["Limiar", "Acionados", "TP", "FP", "FN", "Recall", "Precisão", "F1"],
    linhas, "compacta", numerica=True,
  )}
  <p class="small muted">TP = cancelamentos corretamente sinalizados; FP = clientes que permaneceriam mas
  entram na fila; FN = cancelamentos não detectados. “Acionados” = TP + FP.</p>

  <div class="duas">
    <div>
      {figura("matriz", "11", "Matriz de confusão do modelo no limiar operacional. De 374 cancelamentos, 271 foram capturados; 204 clientes que ficariam também foram sinalizados.")}
    </div>
    <div>
      {figura("limiar", "12", "Precisão, recall e F1 ao longo do limiar. A linha vertical marca o ponto escolhido (0,34) no treino out-of-fold; a curva é calculada no teste apenas para visualização.")}
    </div>
  </div>

  <h3>Interpretação operacional</h3>
  <ul>
    <li>Com limiar 0,34, a fila contém <b>{inteiro(CM['tp'] + CM['fp'])} clientes</b>; {CM['tp']} realmente
    cancelariam e {CM['fp']} não cancelariam. A precisão de {pct(AJ['precisao'])} significa que pouco mais da
    metade da fila é “acerto”.</li>
    <li>O modelo deixa passar <b>{CM['fn']} cancelamentos</b> (falsos negativos). Nenhum modelo desta base
    captura todos; o objetivo é reduzir esse número sem inflar a fila além da capacidade.</li>
    <li>Se a operação só puder contatar, por exemplo, 300 clientes por semana, o limiar deve ser calibrado
    para esse volume — não copiado de um artigo. O score permite simular esse dimensionamento.</li>
    <li>O ponto de operação deve ser reavaliado quando o custo de retenção, a capacidade da equipe ou a
    taxa de churn mudarem. Ele é uma escolha de negócio, não uma propriedade do algoritmo.</li>
  </ul>

  {callout("Um detalhe que evita autoengano",
    "O limiar foi escolhido com previsões out-of-fold do treino, nunca com o teste. Se tivéssemos varrido "
    "o limiar no teste e reportado o melhor F1, o número seria otimista. A tabela acima mostra o teste "
    "para transparência, mas a decisão de 0,34 já estava tomada antes de olhá-lo.", "amber")}
</section>
"""


def interpretabilidade() -> str:
    def valor(nome, v):
        if nome == "tenure":
            return f"{int(v)} meses"
        if nome in ("MonthlyCharges", "TotalCharges", "CobrancaMedia"):
            return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if nome == "SeniorCitizen":
            return "Sim" if int(v) == 1 else "Não"
        if nome == "Contract":
            return {"Month-to-month": "Mensal", "One year": "1 ano", "Two year": "2 anos"}.get(str(v), str(v))
        if nome == "InternetService":
            return {"DSL": "DSL", "Fiber optic": "Fibra", "No": "Sem internet"}.get(str(v), str(v))
        if nome == "PaymentMethod":
            return {"Electronic check": "Cheque eletrônico", "Mailed check": "Cheque enviado",
                    "Bank transfer (automatic)": "Transf. automática",
                    "Credit card (automatic)": "Cartão automático"}.get(str(v), str(v))
        if nome == "ServicosContratados":
            return f"{int(v)} serviços"
        return str(v).replace("No internet service", "Sem internet").replace("No phone service", "Sem telefone")

    linhas = []
    for nome, delta, atual, base in EXEMPLO["fatores"]:
        sinal = "+" if delta >= 0 else "−"
        linhas.append([
            NOMES.get(nome, nome),
            valor(nome, atual),
            valor(nome, base),
            f"{sinal}{abs(delta) * 100:.1f} p.p.".replace(".", ","),
        ])
    importancias = SEL["importancia"][:8]
    linhas_imp = [
        [NOMES.get(d["atributo"], d["atributo"]), f"{d['queda_auc']:.3f}".replace(".", ","),
         f"{d['desvio']:.3f}".replace(".", ",")]
        for d in importancias
    ]
    return f"""
<section>
  <h2><span class="num">Seção 09</span>Interpretabilidade</h2>
  <p>Um score sem explicação é difícil de operacionalizar. A interpretação foi tratada em dois níveis:
  <b>global</b>, para entender quais atributos o modelo mais usa, e <b>local</b>, para justificar a
  probabilidade de um cliente específico.</p>

  <h3>Importância global</h3>
  <p>A importância por permutação mede quanto o ROC-AUC cai quando um atributo é embaralhado no teste,
  destruindo sua relação com o alvo. É uma medida agnóstica ao modelo e complementa a importância nativa
  das árvores.</p>
  {figura("importancia", "13", "Queda de ROC-AUC ao embaralhar cada atributo no teste (média ± desvio em 10 permutações). Tempo de casa e tipo de contrato dominam.")}
  {tabela(["Atributo", "Queda de ROC-AUC", "Desvio"], linhas_imp, "compacta", numerica=True)}
  <p>Os dois atributos dominantes — <b>tempo de casa</b> e <b>tipo de contrato</b> — são justamente os que a
  análise exploratória apontou. Internet, segurança online e suporte vêm em seguida, com efeitos menores.
  Atributos demográficos como gênero e dependentes têm contribuição quase nula neste modelo, o que é um
  bom sinal para a discussão de equidade.</p>

  <h3>Explicação local: um cliente de alto risco</h3>
  <p>Para o perfil <b>{EXEMPLO['id']}</b> do lote de novos clientes, o modelo estima
  <b>{pct(EXEMPLO['probabilidade'])}</b> de churn — faixa crítica. A tabela mostra o efeito de neutralizar
  cada atributo (substituí-lo pela mediana/moda da base), mantendo os demais valores do cliente. A coluna
  “impacto” é quanto a probabilidade cai, em pontos percentuais, quando aquele atributo deixa de contribuir:</p>
  {tabela(["Atributo", "Valor do cliente", "Referência da base", "Impacto"], linhas, "compacta", numerica=False)}
  <p class="small muted">Probabilidade de referência com todos os atributos neutralizados:
  {pct(EXEMPLO['base_probabilidade'])}. A explicação local deste relatório usa neutralização de atributo;
  a API em produção usa valores SHAP (TreeExplainer), que decompõem a margem do modelo de forma aditiva.</p>

  <h3>Como ler (e como não ler) as explicações</h3>
  <ul>
    <li><b>Importância não é causalidade.</b> Dizer que tempo de casa “causa” retenção é um salto indevido;
    a variável pode capturar seleção, satisfação acumulada ou outros fatores não observados.</li>
    <li><b>Impacto local é condicionado ao perfil.</b> O mesmo atributo pode empurrar o risco para cima em
    um cliente e para baixo em outro. As explicações são locais, não regras universais.</li>
    <li><b>Neutralização e SHAP respondem perguntas ligeiramente diferentes.</b> SHAP distribui a margem
    entre os atributos; a neutralização mede o efeito de voltar ao perfil de referência. Ambas são úteis,
    desde que rotuladas com honestidade.</li>
    <li><b>Explicação não substitui julgamento.</b> O contato de retenção deve considerar contexto, histórico
    e o custo da oferta; o modelo apenas ordena e justifica o risco.</li>
  </ul>

  {callout("Transparência da versão publicada",
    "A versão estática no GitHub Pages executa o mesmo Gradient Boosting no navegador e mostra a explicação "
    "por neutralização. A versão com API usa SHAP. Em ambas, a probabilidade é a mesma; o que muda é o "
    "método de atribuição das contribuições, e a interface informa qual está em uso.")}
</section>
"""


def operacao() -> str:
    rotas = [
        ["GET", "/api/saude", "Status do serviço e do modelo"],
        ["GET", "/api/modelo-info", "Metadados, hiperparâmetros e versões"],
        ["GET", "/api/resultados", "Métricas completas consumidas pelo painel"],
        ["GET", "/api/novos-clientes", "Previsões em lote para os 12 perfis"],
        ["GET", "/api/amostra-teste", "Amostra do conjunto de teste para auditoria"],
        ["POST", "/api/prever", "Probabilidade de um cliente + explicação SHAP"],
        ["POST", "/api/prever-lote", "Probabilidade para uma lista de até 500 clientes"],
    ]
    return f"""
<section>
  <h2><span class="num">Seção 10</span>Do modelo à operação</h2>
  <p>O projeto não termina no notebook: o modelo treinado é persistido, servido por uma API e apresentado em
  um painel web. Há duas formas de acesso — uma versão local com FastAPI e uma versão estática publicada no
  GitHub Pages, que funciona sem servidor e sem instalar nada.</p>

  <div class="fluxo">
    <div class="etapa"><b>Dados</b><span>base + novos perfis</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Treino</b><span>train.py</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Artefatos</b><span>modelo + métricas</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>API</b><span>FastAPI / estática</span></div>
    <div class="seta">→</div>
    <div class="etapa"><b>Painel</b><span>6 seções interativas</span></div>
  </div>

  <h3>Arquitetura local</h3>
  <p><span class="mono">src/train.py</span> treina os cinco modelos, seleciona o melhor e grava
  <span class="mono">artifacts/modelo_previa.joblib</span>, <span class="mono">resultados.json</span> e
  <span class="mono">previsoes_teste.csv</span>. A API em <span class="mono">src/api.py</span> carrega o
  artefato e serve o painel em <span class="mono">web/</span>. As probabilidades vêm do pipeline treinado,
  não de regras fixas.</p>

  {tabela(["Método", "Rota", "Descrição"], rotas, "compacta")}

  <h3>Painel web</h3>
  <p>O painel tem seis seções: <b>Visão geral</b>, <b>Base de dados</b>, <b>Análise exploratória</b>,
  <b>Modelo de Machine Learning</b> (algoritmos, comparação, métricas, matriz de confusão, curva de limiar,
  importância e ficha técnica), <b>Simulador de risco</b> (formulário, medidor e explicação) e
  <b>Clientes em risco</b> (ranking da base com filtros e busca). Os gráficos são desenhados em SVG a partir
  dos dados reais.</p>

  <h3>Versão publicada, sem servidor</h3>
  <p>Para que o link funcione em qualquer computador, sem Python e sem API, o site publica uma versão
  estática do painel. Um script de exportação lê os artefatos e embute:</p>
  <ul>
    <li>as métricas e a amostra de teste já calculadas;</li>
    <li>as previsões dos 12 novos clientes;</li>
    <li>a estrutura do Gradient Boosting (150 árvores de profundidade 2) e o pré-processamento,
    permitindo que o simulador calcule probabilidades no próprio navegador.</li>
  </ul>
  <p>A inferência no navegador foi validada contra o Python em 120 perfis aleatórios, com diferença máxima
  de <b>4,9 × 10⁻⁷</b> — ou seja, o site não mostra uma aproximação: mostra o mesmo modelo. O teste também
  reproduziu as 1.409 probabilidades de <span class="mono">previsoes_teste.csv</span>.</p>
</section>
"""
