"""Secoes 11 a 13 e anexos."""

from __future__ import annotations

import sklearn
import pandas as pd
import numpy as np

from .base import (
    CM, DICIONARIO, EDA, IC, LIMIARES, META, SEL, TAB,
    callout, f2, f3, inteiro, pct, tabela,
)

AJ = SEL["teste_ajustado"]
T5 = SEL["teste_05"]


def limites() -> str:
    riscos = [
        ["Correlação lida como causa", "Oferta errada ou expectativa falsa sobre o efeito de uma variável", "Comunicar associação; testar intervenções com experimentos"],
        ["Validação aleatória, não temporal", "Métricas otimistas se o comportamento mudar ao longo do tempo", "Backtest temporal e monitoramento de drift"],
        ["Base de uma única operadora", "Padrões não transferem para outro mercado", "Recalibrar e revalidar antes de reutilizar"],
        ["Probabilidade com incerteza", "Decisões individuais tratadas como certeza", "Usar faixas e combinar com julgamento humano"],
        ["Atributos sensíveis", "Tratamento desigual de gênero ou faixa etária", "Auditoria de equidade e revisão de uso"],
        ["Feedback loop", "Contatar só os sinalizados muda os dados futuros", "Registrar intervenções e comparar grupos"],
        ["Deriva de população", "Queda silenciosa de desempenho", "Monitorar distribuição, recalibrar e retreinar"],
    ]
    return f"""
<section>
  <h2><span class="num">Seção 11</span>Limitações, ética e governança</h2>
  <p>Um modelo útil é um modelo com limites explícitos. Esta seção não é um apêndice jurídico: ela define
  o que o sistema pode e não pode afirmar, e como usá-lo sem transformar uma probabilidade em sentença.</p>

  <h3>Limitações estatísticas e de dados</h3>
  <ul>
    <li><b>Correlação não é causalidade.</b> O modelo identifica associação estatística; não prova que mudar
    um atributo altera o cancelamento. Uma oferta desenhada a partir de uma correlação pode não ter efeito.</li>
    <li><b>A validação é aleatória, não temporal.</b> A divisão 80/20 embaralha os clientes. Em produção, o
    futuro não é uma amostra aleatória do passado; recomenda-se validar em um período posterior para medir
    deriva.</li>
    <li><b>Uma única operadora.</b> A base descreve um mercado e um momento específicos. Padrões de fibra,
    contrato e pagamento podem não se transferir para outra empresa ou país.</li>
    <li><b>Incerteza amostral.</b> O recall de {pct(AJ['recall'])} tem IC 95% de {pct(IC['recall'][0])} a
    {pct(IC['recall'][1])}. O número é uma estimativa, não uma garantia contratual.</li>
    <li><b>Rótulo histórico.</b> “Churn” registra o que aconteceu, não a intenção latente. Clientes que
    saíram por motivos externos podem parecer iguais aos que saíram por insatisfação.</li>
  </ul>

  <h3>Equidade e atributos sensíveis</h3>
  <p>Gênero e faixa etária (SeniorCitizen) entram como variáveis. A importância por permutação mostra efeito
  global pequeno, mas isso não basta: um atributo pode ter efeito pequeno na média e relevante em subgrupos.
  Antes de usar o score para orientar ofertas, é necessário:</p>
  <ul>
    <li>medir recall, precisão e calibração por gênero, faixa etária e outras dimensões relevantes;</li>
    <li>verificar se a ação de retenção é oferecida de forma equitativa, não apenas o score;</li>
    <li>documentar a finalidade, os limites e o responsável por cada uso;</li>
    <li>garantir revisão humana antes de qualquer consequência adversa ao cliente.</li>
  </ul>

  <h3>Privacidade e conformidade</h3>
  <p>O projeto usa uma base pública e não manipula nome, CPF, endereço ou contato. Ainda assim, um score de
  propensão é dado pessoal quando associado a um cliente identificável. Em uma implantação real, aplicam-se
  princípios de minimização, finalidade, segurança, transparência e direito de revisão, além das regras
  setoriais e da LGPD. O simulador não deve ser exposto publicamente com dados reais de clientes. Na versão
  de demonstração, a API libera CORS para facilitar testes; em produção, isso deve ser restrito, com
  autenticação, <i>rate limiting</i> e registro de auditoria. Nenhuma decisão automatizada de negativa de
  serviço é tomada pelo modelo.</p>

  <h3>Riscos e mitigações</h3>
  {tabela(["Risco", "Consequência", "Mitigação"], riscos, "compacta")}

  <h3>Princípios de uso responsável</h3>
  <ol>
    <li><b>O modelo prioriza, a pessoa decide.</b> O score não deve disparar sozinho uma ação irreversível.</li>
    <li><b>Explicar é parte do produto.</b> Toda previsão relevante deve vir acompanhada dos fatores que mais
    pesaram e da incerteza.</li>
    <li><b>Medir antes e depois.</b> A intervenção de retenção precisa de grupo de comparação para saber se
    funcionou; sem isso, o modelo pode apenas estar rotulando quem já ia sair.</li>
    <li><b>Revalidar periodicamente.</b> Distribuição de clientes, preços e concorrência mudam; o modelo
    também precisa mudar.</li>
  </ol>

  {callout("O que este modelo não é",
    "Não é um oráculo de cancelamento, não é um mecanismo de punição, não é uma prova de que um cliente "
    "vai sair e não é um substituto para ouvir o cliente. É um ranking probabilístico para alocar atenção "
    "de retenção com mais critério.", "red")}
</section>
"""


def conclusao() -> str:
    return f"""
<section>
  <h2><span class="num">Seção 12</span>Conclusão</h2>
  <p>O projeto entregou um sistema completo de previsão de churn: da base pública real à interface
  publicada, passando por análise exploratória, comparação de cinco algoritmos, seleção justificada,
  calibração do limiar, interpretação e documentação. O resultado central é robusto e verificável:
  no conjunto de teste, o Gradient Boosting alcança <b>PR-AUC {f3(T5['pr_auc'])}</b>,
  <b>ROC-AUC {f3(T5['roc_auc'])}</b> e, no limiar {f2(SEL['limiar'])}, <b>recall de {pct(AJ['recall'])}</b>
  com precisão de {pct(AJ['precisao'])}.</p>

  <p>Mais importante do que o número é o processo que o sustenta: divisão antes do ajuste, pré-processamento
  dentro do pipeline, teste usado uma única vez, limiar escolhido em previsões out-of-fold, incerteza
  quantificada e comparação sob o mesmo protocolo. Esses detalhes são o que separa um resultado acadêmico
  confiável de uma demonstração otimista.</p>

  <h3>Contribuições</h3>
  <ul>
    <li><b>Comparação reprodutível</b> de cinco famílias de modelos, com grades, tempos e métricas no mesmo
    conjunto de teste.</li>
    <li><b>Escolha guiada por métrica adequada</b> ao desbalanceamento, com discussão explícita do custo de
    falsos positivos e falsos negativos.</li>
    <li><b>Modelo interpretável</b> em nível global (permutação) e local (SHAP na API, neutralização na
    versão estática).</li>
    <li><b>Operacionalização real</b>: API FastAPI, painel de seis seções, versão estática no GitHub Pages e
    relatório em PDF.</li>
    <li><b>Transparência</b> sobre dados, limitações, ética e reprodutibilidade.</li>
  </ul>

  <h3>Próximos passos</h3>
  {tabela(["Frente", "O que fazer", "Por que"], [
    ["Validação temporal", "Separar treino e teste por data e acompanhar drift", "Aproximar o modelo do uso real"],
    ["Modelo de uplift", "Estimar o efeito incremental de cada oferta", "Evitar gastar com quem já ficaria"],
    ["Custo assimétrico", "Otimizar o limiar por custo de retenção vs perda", "Transformar o trade-off em decisão econômica"],
    ["Equidade", "Auditar métricas por subgrupo e ajustar políticas", "Reduzir risco de tratamento desigual"],
    ["Monitoramento", "Painel de distribuição, calibração e recall ao longo do tempo", "Detectar degradação antes do prejuízo"],
    ["Experimentação", "Testes A/B com grupo de controle", "Medir o efeito real da retenção"],
  ], "compacta")}

  <p>O churn é um problema de decisão sob incerteza. O valor deste trabalho não está em prometer certeza,
  mas em oferecer uma forma disciplinada de priorizar atenção, comunicar risco e aprender com o resultado.
  Nesse sentido, o modelo está pronto para ser usado como ponto de partida — e as limitações estão
  documentadas para que ele seja usado com maturidade.</p>
</section>
"""


def reprodutibilidade() -> str:
    return f"""
<section>
  <h2><span class="num">Seção 13</span>Reprodutibilidade e referências</h2>
  <p>Todo o resultado pode ser regenerado a partir da base pública. O treino é determinístico para a semente
  {META['seed']} e o tempo total registrado foi de {f2(META['duracao_total_s'])} s. Os artefatos ficam em
  <span class="mono">artifacts/</span>; o model card em <span class="mono">reports/modelo_card.md</span>;
  o painel em <span class="mono">web/</span>.</p>

  <div class="codigo"><span class="c"># 1. dependências</span>
pip install pandas numpy scikit-learn xgboost shap fastapi uvicorn joblib matplotlib

<span class="c"># 2. treinar, comparar, selecionar e gravar os artefatos</span>
python src/train.py

<span class="c"># 3. regenerar o model card e a tabela comparativa</span>
python src/gerar_relatorio.py

<span class="c"># 4. subir a API + painel local</span>
python src/api.py            <span class="c"># http://127.0.0.1:8000</span>

<span class="c"># 5. gerar a versão estática publicada no GitHub Pages</span>
python src/exportar_site_estatico.py

<span class="c"># 6. gerar este relatório em PDF</span>
python src/gerar_relatorio_pdf.py</div>

  <h3>Ambiente de geração</h3>
  <p class="small">Python 3.12 · scikit-learn {sklearn.__version__} · pandas {pd.__version__} ·
  numpy {np.__version__} · Matplotlib 3.11 · Microsoft Edge headless (A4) · semente {META['seed']}.
  Artefato do modelo: <span class="mono">artifacts/modelo_previa.joblib</span>.</p>

  <h3>Referências</h3>
  <ol class="small">
    <li>IBM. <i>Telco Customer Churn</i> (base pública). Disponível em:
    raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv.</li>
    <li>Pedregosa, F. et al. Scikit-learn: Machine Learning in Python. <i>Journal of Machine Learning
    Research</i>, v. 12, p. 2825–2830, 2011. scikit-learn.org.</li>
    <li>Friedman, J. H. Greedy Function Approximation: A Gradient Boosting Machine.
    <i>Annals of Statistics</i>, v. 29, n. 5, p. 1189–1232, 2001.</li>
    <li>Breiman, L. Random Forests. <i>Machine Learning</i>, v. 45, p. 5–32, 2001.</li>
    <li>Chen, T.; Guestrin, C. XGBoost: A Scalable Tree Boosting System. <i>KDD</i>, 2016.
    xgboost.readthedocs.io.</li>
    <li>Lundberg, S. M.; Lee, S.-I. A Unified Approach to Interpreting Model Predictions.
    <i>NeurIPS</i>, 2017. shap.readthedocs.io.</li>
    <li>Saito, T.; Rehmsmeier, M. The Precision-Recall Plot Is More Informative than the ROC Plot When
    Evaluating Binary Classifiers on Imbalanced Datasets. <i>PLoS ONE</i>, v. 10, n. 3, 2015.</li>
    <li>FastAPI. Documentação oficial: fastapi.tiangolo.com.</li>
    <li>GitHub. <i>GitHub Pages</i>: docs.github.com/pages.</li>
    <li>Repositório do projeto: github.com/Mariozhin/Atividade-03.</li>
  </ol>

  <div class="rubrica">
    <b>Como citar este relatório:</b> FERREIRA, Mario Joaquim. <i>PREVIA AI — Previsão de churn em
    telecomunicações: relatório técnico</i>. Projeto Atividade 03, 2026. Disponível em
    https://mariozhin.github.io/Atividade-03/.
  </div>
</section>
"""


def anexos() -> str:
    linhas = [[n, t, p, d] for n, t, p, d in DICIONARIO]
    return f"""
<section>
  <h2><span class="num">Anexos</span>A. Dicionário de variáveis</h2>
  {tabela(["Coluna", "Tipo", "Papel", "Descrição"], linhas, "compacta")}
  <p class="small muted">A base bruta tem {EDA['n_colunas_brutas']} colunas. Após remover o identificador e o alvo,
  restam 19 atributos originais; com os dois derivados, o modelo usa {EDA['n_atributos_modelo']} atributos.
  O one-hot com agrupamento de categorias raras produz 47 colunas numéricas.</p>

  <h3>B. Ficha técnica do modelo</h3>
  {tabela(["Campo", "Valor"], [
    ["Algoritmo", "GradientBoostingClassifier (scikit-learn)"],
    ["Hiperparâmetros", "learning_rate=0,05 · max_depth=2 · n_estimators=150 · random_state=42"],
    ["Entrada", "19 atributos originais + 2 derivados = 21"],
    ["Transformação", "StandardScaler (6 numéricas) + OneHotEncoder (15 categóricas, min_frequency=10)"],
    ["Colunas após transformação", "47"],
    ["Alvo", "Churn (Yes/No), codificado como 1/0"],
    ["Limiar operacional", f"{f2(SEL['limiar'])} (F1 out-of-fold no treino)"],
    ["Treino / teste", f"{inteiro(META['n_treino'])} / {inteiro(META['n_teste'])}"],
    ["PR-AUC (teste)", f3(T5['pr_auc'])],
    ["ROC-AUC (teste)", f"{f3(T5['roc_auc'])} (IC 95%: {f3(IC['roc_auc'][0])}–{f3(IC['roc_auc'][1])})"],
    ["Recall (limiar)", f"{pct(AJ['recall'])} (IC 95%: {pct(IC['recall'][0])}–{pct(IC['recall'][1])})"],
    ["Precisão (limiar)", pct(AJ['precisao'])],
    ["F1 (limiar)", f"{f3(AJ['f1'])} (IC 95%: {f3(IC['f1'][0])}–{f3(IC['f1'][1])})"],
    ["Brier", f3(T5['brier'])],
    ["Matriz de confusão", f"TN {CM['tn']} · FP {CM['fp']} · FN {CM['fn']} · TP {CM['tp']}"],
    ["Artefato", "artifacts/modelo_previa.joblib"],
  ], "compacta")}

  <h3>C. Glossário</h3>
  {tabela(["Termo", "Definição"], [
    ["Churn", "Cancelamento do cliente; no projeto, Churn = Yes."],
    ["Classe positiva", "Evento de interesse (cancelamento), minoritário na base."],
    ["Desbalanceamento", "Distribuição desigual entre classes; aqui 26,5% de positivos."],
    ["Pipeline", "Sequência de transformações e modelo ajustada como uma unidade, evitando vazamento."],
    ["Vazamento (leakage)", "Uso indevido de informação do teste no treino ou na escolha do modelo."],
    ["Validação cruzada", "Divisão do treino em folds para estimar desempenho e ajustar hiperparâmetros."],
    ["OOF", "Previsões out-of-fold: cada cliente do treino é previsto por um modelo que não o viu."],
    ["ROC-AUC", "Probabilidade de ordenar um positivo acima de um negativo."],
    ["PR-AUC", "Área sob a curva precisão × recall; adequada a classes desbalanceadas."],
    ["Limiar", "Probabilidade a partir da qual o cliente é sinalizado para retenção."],
    ["Calibração", "Concordância entre probabilidade prevista e frequência observada."],
    ["SHAP", "Método de atribuição aditiva da previsão aos atributos."],
    ["Deriva (drift)", "Mudança na distribuição dos dados ao longo do tempo."],
  ], "compacta")}

  <div class="contracapa">
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

    <div class="eyebrow">Projeto publicado</div>
    <h2>Links de acesso</h2>

    <div class="links">
      <div><b>Painel interativo</b><span>https://mariozhin.github.io/Atividade-03/</span></div>
      <div><b>Repositório</b><span>https://github.com/Mariozhin/Atividade-03</span></div>
      <div><b>Este relatório em PDF</b><span>https://mariozhin.github.io/Atividade-03/relatorio/PREVIA_AI_Relatorio.pdf</span></div>
    </div>

    <p class="nota">O painel e o PDF ficam disponíveis independentemente do computador ou servidor local.
    O simulador de risco calcula as probabilidades no próprio navegador, com o mesmo modelo treinado em Python.</p>

    <div class="rodape">
      <div>PREVIA AI · Relatório técnico de previsão de churn</div>
      <div>github.com/Mariozhin/Atividade-03</div>
    </div>
  </div>
</section>
"""
