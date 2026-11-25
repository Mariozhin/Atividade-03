/* PREVIA AI — modo estático
   Executa o mesmo Gradient Boosting do artefato treinado diretamente no
   navegador. Os dados são embutidos em site/dados.js por
   src/exportar_site_estatico.py; nenhuma chamada de rede é necessária.

   Este arquivo substitui a API (/api/*) somente na versão publicada no
   GitHub Pages. O painel servido por src/api.py continua usando o servidor. */
(function () {
  "use strict";

  const D = window.PREVIA_DADOS;
  if (!D) return;

  const M = D.modelo;
  const LIMIAR = D.resultados.selecionado.limiar;
  const SERVICOS = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
  ];

  const numerico = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };

  /* Mesma engenharia de atributos de src/features.py: limpar(). */
  function atributosNumericos(c) {
    const tenure = numerico(c.tenure);
    const mensal = numerico(c.MonthlyCharges);
    const total = numerico(c.TotalCharges);
    return {
      SeniorCitizen: numerico(c.SeniorCitizen),
      tenure,
      MonthlyCharges: mensal,
      TotalCharges: total,
      ServicosContratados: SERVICOS.filter((s) => c[s] === "Yes").length,
      CobrancaMedia: tenure > 0 ? total / tenure : mensal,
    };
  }

  /* Monta o vetor de 47 colunas após StandardScaler + OneHotEncoder. */
  function vetor(c) {
    const x = new Array(M.features).fill(0);
    const num = atributosNumericos(c);
    for (const nome of Object.keys(M.numeric)) {
      const cfg = M.numeric[nome];
      x[cfg.indice] = (num[nome] - cfg.media) / cfg.escala;
    }
    for (const cfg of M.categorical) {
      let indice = cfg.valores[String(c[cfg.nome])];
      if (indice === undefined || indice === null) indice = cfg.infrequente;
      if (indice !== undefined && indice !== null) x[indice] = 1;
    }
    return x;
  }

  /* Soma aditiva das 150 árvores rasas (profundidade 2). */
  function probabilidade(c) {
    const x = vetor(c);
    let z = M.raw_init;
    for (const arvore of M.arvores) {
      let i = 0;
      while (arvore[i].f >= 0) {
        i = x[arvore[i].f] <= arvore[i].t ? arvore[i].l : arvore[i].r;
      }
      z += M.learning_rate * arvore[i].v;
    }
    return 1 / (1 + Math.exp(-z));
  }

  /* Mesma regra de faixas de src/api.py. */
  function faixa(p, limiar) {
    if (p >= 0.60) return { rotulo: "Crítico", cor: "#b3261e", acao: "Contato imediato do time de retenção" };
    if (p >= limiar) return { rotulo: "Alto", cor: "#d97706", acao: "Incluir na fila de retenção da semana" };
    if (p >= 0.20) return { rotulo: "Moderado", cor: "#0e7490", acao: "Monitorar e enviar oferta preventiva" };
    return { rotulo: "Baixo", cor: "#15803d", acao: "Manter acompanhamento de rotina" };
  }

  function arredondar(v, casas) {
    const f = Math.pow(10, casas);
    return Math.round(v * f) / f;
  }

  /* Explicação local: probabilidade com o atributo neutralizado (mediana/moda
     da base), mantendo os demais valores do cliente. */
  function contribuicoes(c, p) {
    const itens = [];
    for (const nome of Object.keys(M.baseline.numeric)) {
      const alternativo = { ...c, [nome]: M.baseline.numeric[nome] };
      const delta = p - probabilidade(alternativo);
      itens.push({ atributo: nome, impacto_pp: arredondar(delta * 100, 2), direcao: delta > 0 ? "aumenta" : "reduz" });
    }
    for (const nome of Object.keys(M.baseline.categorical)) {
      const alternativo = { ...c, [nome]: M.baseline.categorical[nome] };
      const delta = p - probabilidade(alternativo);
      itens.push({ atributo: nome, impacto_pp: arredondar(delta * 100, 2), direcao: delta > 0 ? "aumenta" : "reduz" });
    }
    return itens.sort((a, b) => Math.abs(b.impacto_pp) - Math.abs(a.impacto_pp)).slice(0, 7);
  }

  function preverUm(cliente, limiar, comExplicacao) {
    const p = probabilidade(cliente);
    const resposta = {
      probabilidade: arredondar(p, 4),
      percentual: arredondar(p * 100, 1),
      limiar,
      previsao: p >= limiar ? 1 : 0,
      faixa: faixa(p, limiar),
      cliente,
    };
    if (comExplicacao) {
      const base = probabilidade(basePerfil());
      resposta.contribuicoes = contribuicoes(cliente, p);
      resposta.base_probabilidade = arredondar(base, 4);
      resposta.metodo_explicacao = "neutralizacao";
    }
    return resposta;
  }

  function basePerfil() {
    return { ...M.baseline.categorical, ...M.baseline.numeric };
  }

  function responder(obj, ok = true, status = 200) {
    return {
      ok,
      status,
      json: async () => obj,
      text: async () => JSON.stringify(obj),
    };
  }

  function rotaDe(url) {
    const i = String(url).indexOf("/api/");
    if (i < 0) return null;
    return String(url).slice(i + 5).split("?")[0].replace(/\/+$/, "");
  }

  /* Substitui apenas as rotas da API; qualquer outro fetch segue normal. */
  const fetchNativo = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function (entrada, init) {
    const url = typeof entrada === "string" ? entrada : (entrada && entrada.url) || "";
    const rota = rotaDe(url);
    if (!rota) {
      if (fetchNativo) return fetchNativo(entrada, init);
      return Promise.reject(new Error("fetch indisponível"));
    }
    if (rota === "resultados") return Promise.resolve(responder(D.resultados));
    if (rota === "modelo-info") return Promise.resolve(responder(D.info));
    if (rota === "novos-clientes") return Promise.resolve(responder(D.novos));
    if (rota === "saude") {
      const r = D.resultados;
      return Promise.resolve(responder({
        status: "ok",
        modelo: r.selecionado.nome,
        limiar: r.selecionado.limiar,
        treinado_em: r.meta.gerado_em,
        roc_auc: r.selecionado.teste_05.roc_auc,
      }));
    }
    if (rota === "amostra-teste") {
      const limite = Number((String(url).split("limite=")[1] || "2000").split("&")[0]);
      return Promise.resolve(responder({
        total: D.amostra.total,
        registros: D.amostra.registros.slice(0, Number.isFinite(limite) ? limite : 2000),
      }));
    }
    if (rota === "prever") {
      let corpo = {};
      try { corpo = JSON.parse((init && init.body) || "{}"); } catch (e) { corpo = {}; }
      const limiar = corpo.limiar != null ? Number(corpo.limiar) : LIMIAR;
      return Promise.resolve(responder(preverUm(corpo, limiar, true)));
    }
    if (rota === "prever-lote") {
      let corpo = {};
      try { corpo = JSON.parse((init && init.body) || "{}"); } catch (e) { corpo = {}; }
      const limiar = corpo.limiar != null ? Number(corpo.limiar) : LIMIAR;
      const clientes = Array.isArray(corpo.clientes) ? corpo.clientes : [];
      return Promise.resolve(responder({
        limiar,
        previsoes: clientes.map((c) => preverUm(c, limiar, false)),
      }));
    }
    return Promise.resolve(responder({ detail: "Rota não disponível na versão estática." }, false, 404));
  };

  window.PREVIA_PREVER = preverUm;
  window.PREVIA_PROBABILIDADE = probabilidade;
})();
