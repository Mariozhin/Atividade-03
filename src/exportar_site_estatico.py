"""Gera a versao estatica do painel PREVIA AI para o GitHub Pages.

O painel original (src/api.py) depende de um servidor FastAPI e do modelo
persistido em artifacts/modelo_previa.joblib. Para que a pagina possa ser
aberta em qualquer computador, sem servidor e sem instalar Python, este script:

1. le os artefatos ja treinados (nenhum numero e recalculado);
2. exporta a arvore do Gradient Boosting e o pre-processamento para JSON;
3. pre-calcula as previsoes dos 12 clientes novos e a amostra de teste;
4. copia web/ para site/, aplicando pequenos ajustes de texto;
5. grava dados.js (dados embutidos) e prever.js (inferencia no navegador).

Resultado: publicar a raiz do repositorio no GitHub Pages entrega o painel
completo em https://mariozhin.github.io/Atividade-03/ (o simulador funciona
no proprio navegador, com as mesmas probabilidades do modelo treinado).

Uso:  python src/exportar_site_estatico.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ART = RAIZ / "artifacts"
WEB = RAIZ / "web"
SITE = RAIZ / "site"

sys.path.insert(0, str(RAIZ / "src"))
import features as feat  # noqa: E402


def num(x, casas=4):
    return round(float(x), casas)


def faixa_risco(p: float, limiar: float) -> dict:
    """Mesma regra de src/api.py (mantida em sincronia manualmente)."""
    if p >= 0.60:
        return {"rotulo": "Crítico", "cor": "#b3261e", "acao": "Contato imediato do time de retenção"}
    if p >= limiar:
        return {"rotulo": "Alto", "cor": "#d97706", "acao": "Incluir na fila de retenção da semana"}
    if p >= 0.20:
        return {"rotulo": "Moderado", "cor": "#0e7490", "acao": "Monitorar e enviar oferta preventiva"}
    return {"rotulo": "Baixo", "cor": "#15803d", "acao": "Manter acompanhamento de rotina"}


def exportar_modelo(modelo) -> dict:
    """Converte Pipeline -> estrutura JSON que o JavaScript consegue executar."""
    prep = modelo.named_steps["prep"]
    est = modelo.named_steps["modelo"]
    scaler = prep.named_transformers_["num"]
    encoder = prep.named_transformers_["cat"]
    features = list(prep.get_feature_names_out())
    indice = {nome: i for i, nome in enumerate(features)}

    numericas = {}
    for nome, media, escala in zip(feat.NUMERICAS, scaler.mean_, scaler.scale_):
        numericas[nome] = {
            "indice": indice[f"num__{nome}"],
            "media": float(media),
            "escala": float(escala),
        }

    categoricas = []
    for coluna, valores in zip(feat.CATEGORICAS, encoder.categories_):
        infrequente = None
        for candidato in (f"cat__{coluna}_infrequent_sklearn", f"cat__{coluna}_infrequent"):
            if candidato in indice:
                infrequente = indice[candidato]
                break
        mapa = {}
        for valor in valores:
            nome = f"cat__{coluna}_{valor}"
            mapa[str(valor)] = indice[nome] if nome in indice else infrequente
        categoricas.append({"nome": coluna, "valores": mapa, "infrequente": infrequente})

    arvores = []
    for estimador in est.estimators_[:, 0]:
        arvore = estimador.tree_
        nos = []
        for i in range(arvore.node_count):
            nos.append(
                {
                    "f": int(arvore.feature[i]),
                    "t": float(arvore.threshold[i]),
                    "l": int(arvore.children_left[i]),
                    "r": int(arvore.children_right[i]),
                    "v": float(arvore.value[i][0][0]),
                }
            )
        arvores.append(nos)

    # Perfil de referencia (medianas e modas da base) usado apenas para a
    # explicacao por neutralizacao de atributo no simulador estatico.
    bruto = pd.read_csv(RAIZ / "data" / "Telco-Customer-Churn.csv")
    limpo = feat.limpar(bruto)
    baseline_num = {c: float(limpo[c].median()) for c in feat.NUMERICAS}
    baseline_cat = {c: str(limpo[c].mode().iloc[0]) for c in feat.CATEGORICAS}

    return {
        "tipo": "GradientBoostingClassifier",
        "features": len(features),
        "nomes": features,
        "learning_rate": float(est.learning_rate),
        "raw_init": float(est._raw_predict_init(np.zeros((1, len(features))))[0, 0]),
        "numeric": numericas,
        "categorical": categoricas,
        "baseline": {"numeric": baseline_num, "categorical": baseline_cat},
        "arvores": arvores,
    }


def preparar_cliente(linha: dict) -> dict:
    """Reproduz o dicionario que a API devolve em `cliente`."""
    campos = [
        "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "PhoneService",
        "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
        "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
        "Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges",
    ]
    saida = {}
    for campo in campos:
        valor = linha[campo]
        if campo in ("SeniorCitizen", "tenure"):
            valor = int(valor)
        elif campo in ("MonthlyCharges", "TotalCharges"):
            valor = float(valor)
        else:
            valor = str(valor)
        saida[campo] = valor
    return saida


def main() -> None:
    modelo = joblib.load(ART / "modelo_previa.joblib")
    with open(ART / "resultados.json", encoding="utf-8") as f:
        resultados = json.load(f)
    limiar = float(resultados["selecionado"]["limiar"])

    SITE.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Modelo exportado para inferencia no navegador
    # ------------------------------------------------------------------
    modelo_json = exportar_modelo(modelo)

    # ------------------------------------------------------------------
    # 2. Previsoes dos 12 clientes novos (mesmo pipeline do treino)
    # ------------------------------------------------------------------
    novos = pd.read_csv(RAIZ / "data" / "novos_clientes.csv")
    limpo_novos = feat.limpar(novos)
    prob_novos = modelo.predict_proba(feat.preparar_matriz(limpo_novos))[:, 1]
    clientes_novos = []
    for (_, linha), p in zip(novos.iterrows(), prob_novos):
        dados = preparar_cliente(linha.to_dict())
        prob = float(p)
        clientes_novos.append(
            {
                "probabilidade": num(prob),
                "percentual": num(prob * 100, 1),
                "limiar": limiar,
                "previsao": int(prob >= limiar),
                "faixa": faixa_risco(prob, limiar),
                "cliente": dados,
                "customerID": str(linha["customerID"]),
            }
        )
    novos_json = {"limiar": limiar, "total": len(clientes_novos), "clientes": clientes_novos}

    # ------------------------------------------------------------------
    # 3. Amostra do conjunto de teste (mesma ordenacao da API)
    # ------------------------------------------------------------------
    previsoes = pd.read_csv(ART / "previsoes_teste.csv")
    colunas = [
        "customerID", "tenure", "Contract", "InternetService", "PaymentMethod",
        "MonthlyCharges", "prob_churn", "churn_real", "previsao",
    ]
    amostra = (
        previsoes.sort_values("prob_churn", ascending=False)
        .head(2000)[colunas]
        .to_dict(orient="records")
    )
    for registro in amostra:
        registro["tenure"] = int(registro["tenure"])
        registro["MonthlyCharges"] = float(registro["MonthlyCharges"])
        registro["prob_churn"] = float(registro["prob_churn"])
        registro["churn_real"] = int(registro["churn_real"])
        registro["previsao"] = int(registro["previsao"])
    amostra_json = {"total": int(len(previsoes)), "registros": amostra}

    # ------------------------------------------------------------------
    # 4. Metadados do modelo
    # ------------------------------------------------------------------
    import sklearn

    info_json = {
        "algoritmo": resultados["selecionado"]["nome"],
        "familia": resultados["selecionado"]["familia"],
        "hiperparametros": resultados["selecionado"]["melhor_params"],
        "limiar": limiar,
        "n_atributos_originais": len(feat.CATEGORICAS) + len(feat.NUMERICAS),
        "n_atributos_transformados": len(modelo_json["nomes"]),
        "categoricas": feat.CATEGORICAS,
        "numericas": feat.NUMERICAS,
        "artefato": "artifacts/modelo_previa.joblib",
        "bibliotecas": {
            "scikit-learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }

    dados = {
        "modo": "estatico",
        "resultados": resultados,
        "amostra": amostra_json,
        "novos": novos_json,
        "info": info_json,
        "modelo": modelo_json,
    }
    carga = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    carga = carga.replace("</", "<\\/")
    (SITE / "dados.js").write_text(
        "/* Dados reais embutidos, gerados por src/exportar_site_estatico.py. */\n"
        f"window.PREVIA_DADOS = {carga};\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # 5. Copia do front-end com ajustes para o modo estatico
    # ------------------------------------------------------------------
    shutil.copyfile(WEB / "styles.css", SITE / "styles.css")
    shutil.copyfile(WEB / "prever.js", SITE / "prever.js")

    app = (WEB / "app.js").read_text(encoding="utf-8")
    substituicoes = [
        ('$("#status-text").textContent = "API online · modelo carregado";',
         '$("#status-text").textContent = "Versão estática · modelo embutido";'),
        ('$("#status-text").textContent = "API indisponível";',
         '$("#status-text").textContent = "Falha ao carregar os dados";'),
        ("Falha ao consultar a API.", "Falha ao calcular a previsão."),
        ("Previsão calculada pelo modelo em produção.",
         "Previsão calculada no navegador, com o modelo treinado."),
        ("previstos pela API", "previstos pelo modelo"),
        ("Contribuição de cada atributo para a probabilidade (valores SHAP, em pontos percentuais).",
         "Impacto estimado de cada atributo: quanto a probabilidade cai quando o atributo é neutralizado (em pontos percentuais)."),
        ("Probabilidade calculada pelo modelo treinado (${state.S.selecionado.nome}), não por regra fixa.\n    Contribuições via SHAP; a soma parte da probabilidade base de ${fmtPct(d.base_probabilidade)}.",
         "Probabilidade calculada no navegador com o mesmo Gradient Boosting treinado (${state.S.selecionado.nome}), não por regra fixa.\n    Explicação por neutralização de atributo a partir da probabilidade de referência de ${fmtPct(d.base_probabilidade)}."),
        ("A API (<span class=\"mono\">src/api.py</span>) carrega o mesmo artefato para prever novos clientes.",
         "A versão local (<span class=\"mono\">src/api.py</span>) carrega o mesmo artefato; esta página publicada executa o modelo no próprio navegador."),
    ]
    for antigo, novo in substituicoes:
        if antigo not in app:
            raise SystemExit(f"Texto nao encontrado em web/app.js: {antigo[:70]!r}")
        app = app.replace(antigo, novo)
    (SITE / "app.js").write_text(app, encoding="utf-8")

    # ------------------------------------------------------------------
    # 6. index.html estatico (caminhos relativos + scripts locais)
    # ------------------------------------------------------------------
    html = (WEB / "index.html").read_text(encoding="utf-8")
    html = html.replace('href="/static/styles.css"', 'href="site/styles.css"')
    html = html.replace(
        '<script src="/static/app.js"></script>',
        '<script src="site/dados.js"></script>\n'
        '<script src="site/prever.js"></script>\n'
        '<script src="site/app.js"></script>',
    )
    html = html.replace(
        '      <div class="tiny">Modelo carregado do artefato<br><span class="mono" style="font-size:10.5px">modelo_previa.joblib</span></div>',
        '      <div class="tiny">Modelo carregado do artefato<br><span class="mono" style="font-size:10.5px">modelo_previa.joblib</span></div>\n'
        '      <a class="tiny" href="relatorio/PREVIA_AI_Relatorio.pdf" target="_blank" style="display:block;margin-top:10px;color:#0f766e;font-weight:650;text-decoration:none">📄 Relatório completo (PDF)</a>',
    )
    html = html.replace(
        'O formulário envia os dados para a API, que carrega o modelo\n        treinado e devolve a probabilidade real de churn — não é uma estimativa ilustrativa.',
        'O formulário executa o modelo treinado diretamente no navegador\n        e devolve a probabilidade real de churn — não é uma estimativa ilustrativa.',
    )
    html = html.replace(
        '<h2 class="section-title"><span class="n">09</span> Lote de novos clientes <span class="hint">previstos pela API</span></h2>',
        '<h2 class="section-title"><span class="n">09</span> Lote de novos clientes <span class="hint">previstos pelo modelo</span></h2>',
    )
    html = html.replace(
        '<span>PREVIA AI · Trabalho acadêmico de Machine Learning aplicado à retenção de clientes</span>',
        '<span>PREVIA AI · Trabalho acadêmico de Machine Learning aplicado à retenção de clientes · <a href="relatorio/PREVIA_AI_Relatorio.pdf" target="_blank" style="color:#0f766e;font-weight:600">Relatório em PDF</a></span>',
    )
    (RAIZ / "index.html").write_text(html, encoding="utf-8")
    (RAIZ / ".nojekyll").write_text("", encoding="utf-8")

    print("Site estatico gerado:")
    for caminho in (RAIZ / "index.html", SITE / "dados.js", SITE / "app.js", SITE / "prever.js"):
        print(f"  {caminho.relative_to(RAIZ)}")
    print(f"Clientes novos: {len(clientes_novos)} | amostra: {len(amostra)} | arvores: {len(modelo_json['arvores'])}")
    print("Tamanho de site/dados.js: %.1f KB" % ((SITE / "dados.js").stat().st_size / 1024))


if __name__ == "__main__":
    main()
