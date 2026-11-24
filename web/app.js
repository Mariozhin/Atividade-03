/* PREVIA AI — front-end
   Todos os números exibidos vêm de /api/resultados (métricas medidas no
   conjunto de teste) e de /api/prever (inferência do modelo treinado). */

const NS = "http://www.w3.org/2000/svg";
const nf = new Intl.NumberFormat("pt-BR");
const nf1 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const nf2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const fmtInt = (x) => nf.format(Math.round(x));
const fmtPct = (x, d = 1) => nf1.format(x * 100).replace(",0", "") + "%";
const fmtPctD = (x, d = 1) => (d === 2 ? nf2 : nf1).format(x * 100) + "%";
const fmt3 = (x) => x.toFixed(3).replace(".", ",");
const fmt2 = (x) => nf2.format(x);

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

/* ---------------- SVG helpers ---------------- */
function S(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) e.setAttribute(k, v);
  }
  if (parent) parent.appendChild(e);
  return e;
}
function chart(w, h, parent) {
  const svg = S("svg", { viewBox: `0 0 ${w} ${h}`, class: "chart", role: "img" }, parent);
  return svg;
}
function txt(svg, x, y, str, attrs = {}) {
  const t = S("text", { x, y, ...attrs }, svg);
  t.textContent = str;
  return t;
}
function title(el, str) {
  const t = S("title", {}, el);
  t.textContent = str;
}
function lineEl(parent, attrs) {
  return S("line", attrs, parent);
}

/* Barras horizontais com rótulo e valor */
function barsH(box, items, opts = {}) {
  box.innerHTML = "";
  const W = Math.max(300, Math.round(box.clientWidth || 640));
  const rowH = opts.rowH || 32, padR = 66;
  const maxChars = Math.max(...items.map((d) => String(d.label).length));
  const padL = opts.padL || Math.max(76, Math.min(168, Math.round(maxChars * 6.4 + 14)));
  const H = items.length * rowH + 8;
  const svg = chart(W, H, box);
  const max = opts.max ?? Math.max(...items.map((d) => d.value)) * 1.02;
  items.forEach((d, i) => {
    const y = i * rowH + 4;
    const color = opts.colorFn ? opts.colorFn(d, i) : (opts.color || "#0f766e");
    txt(svg, padL - 10, y + rowH / 2 + 4, d.label, { "text-anchor": "end", class: "axis-label", style: "font-size:11.5px;fill:#344054" });
    S("rect", { x: padL, y: y + 6, width: W - padL - padR, height: rowH - 14, rx: 4, fill: "#f2f4f7" }, svg);
    const bw = Math.max(2, ((W - padL - padR) * d.value) / max);
    const r = S("rect", { x: padL, y: y + 6, width: bw, height: rowH - 14, rx: 4, fill: color }, svg);
    title(r, `${d.label}: ${opts.fmt ? opts.fmt(d.value) : d.value}${d.extra || ""}`);
    txt(svg, padL + bw + 7, y + rowH / 2 + 4, opts.fmt ? opts.fmt(d.value) : d.value, {
      class: "axis-label", style: "font-size:11px;font-weight:600;fill:#344054",
    });
  });
  return svg;
}

/* Barras verticais agrupadas (histograma) */
function barsGrouped(box, bins, series, opts = {}) {
  box.innerHTML = "";
  const W = Math.max(320, Math.round(box.clientWidth || 640));
  const H = 268, padL = 42, padB = 46, padT = 12, padR = 10;
  const svg = chart(W, H, box);
  const max = Math.max(...series.flatMap((s) => s.values)) * 1.08 || 1;
  const plotW = W - padL - padR, plotH = H - padB - padT;
  const step = plotW / bins.length;
  const bw = Math.max(2, (step - 4) / series.length);
  [0, 0.25, 0.5, 0.75, 1].forEach((f) => {
    const y = padT + plotH * (1 - f);
    S("line", { x1: padL, x2: W - padR, y1: y, y2: y, class: "grid-line" }, svg);
    txt(svg, padL - 7, y + 4, fmtInt(max * f), { "text-anchor": "end", class: "axis-label" });
  });
  bins.forEach((b, i) => {
    series.forEach((s, si) => {
      const v = s.values[i];
      const hgt = (plotH * v) / max;
      const x = padL + i * step + 2 + si * bw;
      const r = S("rect", {
        x, y: padT + plotH - hgt, width: Math.max(1.5, bw - 1), height: hgt,
        rx: 1.5, fill: s.color, opacity: 0.88,
      }, svg);
      title(r, `${b} — ${s.name}: ${fmtInt(v)} clientes`);
    });
    if (i % 4 === 0) txt(svg, padL + i * step + step / 2, H - 30, b, { "text-anchor": "middle", class: "axis-label" });
  });
  txt(svg, W - padR, H - 10, opts.xLabel || "", { "text-anchor": "end", class: "axis-label" });
  return svg;
}

/* Linhas (ROC, PR, calibração, limiar) */
function lines(box, series, opts = {}) {
  box.innerHTML = "";
  const W = Math.max(320, Math.round(box.clientWidth || 640));
  const H = opts.h || 300, padL = 46, padB = 38, padT = 14, padR = 14;
  const svg = chart(W, H, box);
  const plotW = W - padL - padR, plotH = H - padB - padT;
  const xMax = opts.xMax ?? 1, yMax = opts.yMax ?? 1;
  const xOf = (x) => padL + (x / xMax) * plotW;
  const yOf = (y) => padT + plotH - (y / yMax) * plotH;

  for (let i = 0; i <= 4; i++) {
    const f = i / 4;
    S("line", { x1: padL, x2: W - padR, y1: yOf(yMax * f), y2: yOf(yMax * f), class: "grid-line" }, svg);
    txt(svg, padL - 7, yOf(yMax * f) + 4, (yMax * f).toFixed(1).replace(".", ","), { "text-anchor": "end", class: "axis-label" });
    S("line", { x1: xOf(xMax * f), x2: xOf(xMax * f), y1: padT, y2: padT + plotH, class: "grid-line" }, svg);
    txt(svg, xOf(xMax * f), H - 20, (xMax * f).toFixed(1).replace(".", ","), { "text-anchor": "middle", class: "axis-label" });
  }
  txt(svg, padL + plotW / 2, H - 4, opts.xLabel || "", { "text-anchor": "middle", class: "axis-label" });
  txt(svg, 10, padT + plotH / 2, opts.yLabel || "", { "text-anchor": "middle", class: "axis-label", transform: `rotate(-90 10 ${padT + plotH / 2})` });

  if (opts.diagonal) {
    S("line", { x1: xOf(0), y1: yOf(0), x2: xOf(xMax), y2: yOf(yMax), stroke: "#cbd5e1", "stroke-width": 1, "stroke-dasharray": "4 4" }, svg);
  }
  if (opts.marker != null) {
    const xm = xOf(opts.marker);
    S("line", { x1: xm, x2: xm, y1: padT, y2: padT + plotH, stroke: "#0f766e", "stroke-width": 1.5, "stroke-dasharray": "3 3", opacity: .7 }, svg);
  }

  series.forEach((s) => {
    const d = s.points.map((p, i) => `${i === 0 ? "M" : "L"}${xOf(p.x).toFixed(1)},${yOf(p.y).toFixed(1)}`).join(" ");
    const path = S("path", {
      d, fill: "none", stroke: s.color, "stroke-width": s.width || 2,
      "stroke-linejoin": "round", "stroke-linecap": "round",
      "stroke-dasharray": s.dash || undefined, opacity: s.opacity ?? 1,
    }, svg);
    title(path, s.name);
  });
  return svg;
}

function legend(box, items) {
  const d = document.createElement("div");
  d.className = "legend";
  d.innerHTML = items.map((i) => `<span><i style="background:${i.color}"></i>${i.name}</span>`).join("");
  box.appendChild(d);
}

/* Donut */
function donut(box, parts, center) {
  box.innerHTML = "";
  const W = 300, H = 190, cx = 150, cy = 95, R = 74, r = 52;
  const svg = chart(W, H, box);
  const total = parts.reduce((a, b) => a + b.value, 0);
  let ang = -Math.PI / 2;
  parts.forEach((p) => {
    const sweep = (p.value / total) * Math.PI * 2;
    const a0 = ang, a1 = ang + sweep;
    const large = sweep > Math.PI ? 1 : 0;
    const p0 = [cx + R * Math.cos(a0), cy + R * Math.sin(a0)];
    const p1 = [cx + R * Math.cos(a1), cy + R * Math.sin(a1)];
    const q1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
    const q0 = [cx + r * Math.cos(a0), cy + r * Math.sin(a0)];
    const path = S("path", {
      d: `M${p0} A${R},${R} 0 ${large} 1 ${p1} L${q1} A${r},${r} 0 ${large} 0 ${q0} Z`,
      fill: p.color,
    }, svg);
    title(path, `${p.label}: ${fmtInt(p.value)} (${fmtPct(p.value / total)})`);
    ang = a1;
  });
  txt(svg, cx, cy - 2, fmtPct(parts[0].value / total), { "text-anchor": "middle", style: "font-size:22px;font-weight:700;fill:#101828" });
  txt(svg, cx, cy + 16, center || "", { "text-anchor": "middle", class: "axis-label" });
  return svg;
}

/* Matriz de confusão */
function heatmap(box, cm) {
  box.innerHTML = "";
  const W = 420, H = 210, padL = 118, padT = 34, cw = 140, ch = 68;
  const svg = chart(W, H, box);
  txt(svg, padL + cw, padT - 14, "Previsto: não", { "text-anchor": "middle", class: "axis-label", style: "font-weight:600" });
  txt(svg, padL + cw * 1.5 + 6, padT - 14, "Previsto: sim", { "text-anchor": "middle", class: "axis-label", style: "font-weight:600" });
  txt(svg, 14, padT + ch / 2, "Real: não", { class: "axis-label", style: "font-weight:600" });
  txt(svg, 14, padT + ch * 1.5 + 8, "Real: sim", { class: "axis-label", style: "font-weight:600" });
  const cells = [
    [cm.tn, 0, 0, "#dcfce7", "#14532d", "Verdadeiro negativo"],
    [cm.fp, 1, 0, "#fee4e2", "#7f1d1d", "Falso positivo"],
    [cm.fn, 0, 1, "#fee4e2", "#7f1d1d", "Falso negativo"],
    [cm.tp, 1, 1, "#ccfbf1", "#0b4a46", "Verdadeiro positivo"],
  ];
  cells.forEach(([v, cxI, cyI, bg, fg, nome]) => {
    const g = S("g", {}, svg);
    const rect = S("rect", { x: padL + cxI * cw + 3, y: padT + cyI * ch + 3, width: cw - 6, height: ch - 6, rx: 8, fill: bg }, g);
    title(rect, `${nome}: ${fmtInt(v)} clientes`);
    txt(g, padL + cxI * cw + cw / 2, padT + cyI * ch + ch / 2 + 2, fmtInt(v), { "text-anchor": "middle", style: `font-size:22px;font-weight:700;fill:${fg}` });
    txt(g, padL + cxI * cw + cw / 2, padT + cyI * ch + ch / 2 + 20, nome, { "text-anchor": "middle", style: "font-size:9.5px;fill:#667085" });
  });
  return svg;
}

/* Gauge semicircular */
function gauge(box, p, limiar) {
  box.innerHTML = "";
  const W = 320, H = 190, cx = 160, cy = 150, R = 108, thick = 18;
  const svg = chart(W, H, box);
  const arc = (a0, a1, color, op = 1) => {
    const p0 = [cx + R * Math.cos(a0), cy - R * Math.sin(a0)];
    const p1 = [cx + R * Math.cos(a1), cy - R * Math.sin(a1)];
    return S("path", {
      d: `M${p0} A${R},${R} 0 0 1 ${p1}`, stroke: color, "stroke-width": thick,
      fill: "none", "stroke-linecap": "butt", opacity: op,
    }, svg);
  };
  const A = Math.PI;
  const frac = (x) => A - x * A;
  arc(frac(0), frac(limiar), "#22c55e");
  arc(frac(limiar), frac(0.6), "#f59e0b");
  arc(frac(0.6), frac(1), "#ef4444");
  // marcador do limiar
  const ax = cx + (R + 14) * Math.cos(frac(limiar)), ay = cy - (R + 14) * Math.sin(frac(limiar));
  const bx = cx + (R - 14) * Math.cos(frac(limiar)), by = cy - (R - 14) * Math.sin(frac(limiar));
  S("line", { x1: ax, y1: ay, x2: bx, y2: by, stroke: "#0b5d5a", "stroke-width": 2 }, svg);
  // agulha
  const ang = frac(p);
  const nx = cx + (R - 26) * Math.cos(ang), ny = cy - (R - 26) * Math.sin(ang);
  S("line", { x1: cx, y1: cy, x2: nx, y2: ny, stroke: "#101828", "stroke-width": 3.2, "stroke-linecap": "round" }, svg);
  S("circle", { cx, cy, r: 6, fill: "#101828" }, svg);
  txt(svg, 22, cy + 26, "0%", { class: "axis-label" });
  txt(svg, W - 24, cy + 26, "100%", { "text-anchor": "end", class: "axis-label" });
  txt(svg, cx, cy + 30, `limiar ${limiar.toFixed(2).replace(".", ",")}`, { "text-anchor": "middle", class: "axis-label" });
  return svg;
}

/* ---------------- estado ---------------- */
const state = { S: null, AMOSTRA: [], NOVOS: null, INFO: null, clientes: [], pagina: 1, faixa: "todos", busca: "", limiar: 0.34 };

const CORES_MODELO = {
  logistica: "#64748b",
  arvore: "#a16207",
  floresta: "#0e7490",
  gradient_boosting: "#0f766e",
  xgboost: "#7c3aed",
};

/* ---------------- boot ---------------- */
document.addEventListener("DOMContentLoaded", async () => {
  registrarNav();
  try {
    const [res, amostra, novos, info] = await Promise.all([
      fetch("/api/resultados").then((r) => r.json()),
      fetch("/api/amostra-teste?limite=2000").then((r) => r.json()),
      fetch("/api/novos-clientes").then((r) => r.json()),
      fetch("/api/modelo-info").then((r) => r.json()),
    ]);
    state.S = res;
    state.AMOSTRA = amostra.registros;
    state.NOVOS = novos;
    state.INFO = info;
    state.limiar = res.selecionado.limiar;
    state.clientes = state.AMOSTRA;

    $("#status-dot").classList.remove("off");
    $("#status-text").textContent = "API online · modelo carregado";
    $("#chip-dataset").textContent = `Base: ${fmtInt(res.meta.n_registros)} clientes`;
    $("#chip-modelo").textContent = `Modelo: ${res.selecionado.nome}`;
    $("#hp-modelo").textContent = res.selecionado.nome;
    $("#hp-auc").textContent = fmt3(res.selecionado.teste_05.roc_auc);
    $("#hp-recall").textContent = fmtPct(res.selecionado.teste_ajustado.recall);
    $("#hp-limiar").textContent = res.selecionado.limiar.toFixed(2).replace(".", ",");
    $("#hp-teste").textContent = fmtInt(res.meta.n_teste);

    renderOverview();
    irPara((location.hash || "#overview").slice(1));
  } catch (e) {
    console.error(e);
    $("#status-dot").classList.add("off");
    $("#status-text").textContent = "API indisponível";
    document.body.insertAdjacentHTML("afterbegin",
      `<div style="position:fixed;inset:0;background:#f6f8fb;display:grid;place-items:center;z-index:999;padding:24px">
        <div class="card card-pad" style="max-width:520px">
          <h2 style="font-size:18px;margin-bottom:8px">Não foi possível falar com a API</h2>
          <p class="small muted">Inicie o servidor com <span class="mono">python src/api.py</span> e recarregue esta página.</p>
          <pre class="mono" style="background:#f8fafc;padding:10px;border-radius:8px;margin-top:12px;overflow:auto">${String(e)}</pre>
        </div>
      </div>`);
  }
});

/* ---------------- navegação ---------------- */
const TITULOS = {
  overview: "Visão geral",
  dados: "Base de dados",
  eda: "Análise exploratória",
  modelo: "Modelo de Machine Learning",
  simulador: "Simulador de risco",
  clientes: "Clientes em risco",
};
function registrarNav() {
  $$(".nav-item").forEach((a) => a.addEventListener("click", () => {
    $("#sidebar").classList.remove("open");
  }));
  $("#menu-btn").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
  window.addEventListener("hashchange", () => irPara((location.hash || "#overview").slice(1)));
}
const RENDERIZADORES = {
  overview: renderOverview,
  dados: renderDados,
  eda: renderEDA,
  modelo: renderModelo,
  simulador: renderSimulador,
  clientes: renderClientes,
};
const renderizados = new Set(["overview"]);

function irPara(v) {
  if (!TITULOS[v]) v = "overview";
  $$(".view").forEach((s) => s.classList.toggle("active", s.id === `view-${v}`));
  $$(".nav-item").forEach((a) => a.classList.toggle("active", a.dataset.view === v));
  $("#crumb-atual").textContent = TITULOS[v];
  // Renderiza sob demanda: só quando a seção está visível o contêiner tem
  // largura real, o que permite desenhar os gráficos em escala 1:1.
  if (state.S && !renderizados.has(v)) {
    renderizados.add(v);
    RENDERIZADORES[v]();
  }
  window.scrollTo({ top: 0, behavior: "instant" });
}

/* ============================================================
   VISÃO GERAL
   ============================================================ */
function renderOverview() {
  const S = state.S, sel = S.selecionado, cm = sel.teste_ajustado.matriz_confusao;

  $("#kpis-overview").innerHTML = [
    kpi("Clientes na base", fmtInt(S.meta.n_registros), "Base pública real (IBM Telco)"),
    kpi("Taxa de churn observada", fmtPct(S.meta.taxa_churn), `${fmtInt(S.eda.churn_sim)} cancelaram · ${fmtInt(S.eda.churn_nao)} ficaram`),
    kpi("Divisão treino / teste", `${fmtInt(S.meta.n_treino)}<small> / ${fmtInt(S.meta.n_teste)}</small>`, "80/20 estratificado, semente 42"),
    kpi("ROC-AUC no teste", fmt3(sel.teste_05.roc_auc), `PR-AUC ${fmt3(sel.teste_05.pr_auc)} · F1 ${fmt3(sel.teste_ajustado.f1)}`, true),
  ].join("");

  $("#pipeline-home").innerHTML = [
    ["Dados", `${fmtInt(S.meta.n_registros)} clientes`, "Base pública IBM, 21 colunas", true],
    ["Preparação", "21 atributos", "Limpeza + 2 atributos derivados", true],
    ["Divisão", "80 / 20", "Estratificada pelo alvo", true],
    ["Treino", "5 algoritmos", "Validação cruzada de 5 folds", true],
    ["Seleção", sel.nome, "Regra definida antes do teste", true],
    ["Produção", "API + painel", "Probabilidade e ação de retenção", true],
  ].map(([t, d, s], i) => `<div class="pipe-step done">
      <div class="num">ETAPA ${String(i + 1).padStart(2, "0")}</div>
      <div class="t">${t}</div><div class="d">${d}</div><div class="d" style="color:#0b5d5a">${s}</div>
    </div>`).join("");

  $("#origem-dados").innerHTML = `
    <div class="callout info" style="margin-bottom:14px">
      <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v5h1"/></svg>
      <div><b>Dados reais, não sintéticos.</b> O treinamento e a avaliação usam a base pública
      <b>IBM Telco Customer Churn</b> — 7.043 clientes reais de uma operadora de telecomunicações,
      com rótulo histórico de cancelamento. Não há resultados fictícios nesta página: todas as métricas
      foram medidas em um conjunto de teste que o modelo nunca viu.</div>
    </div>
    <div class="grid g2" style="gap:10px">
      <div><div class="tiny muted">Registros</div><div style="font-weight:650">${fmtInt(S.meta.n_registros)}</div></div>
      <div><div class="tiny muted">Colunas originais</div><div style="font-weight:650">${S.eda.n_colunas_brutas}</div></div>
      <div><div class="tiny muted">Atributos no modelo</div><div style="font-weight:650">${S.eda.n_atributos_modelo}</div></div>
      <div><div class="tiny muted">Gerado em</div><div style="font-weight:650">${new Date(S.meta.gerado_em).toLocaleString("pt-BR")}</div></div>
    </div>
    <p class="tiny muted" style="margin-top:12px">Fonte: <a href="${S.meta.fonte}" target="_blank" rel="noopener">IBM / telco-customer-churn (GitHub)</a>.
    Os 12 perfis usados no simulador são entradas criadas para demonstração — as previsões sobre eles vêm do modelo real.</p>`;

  const totalPos = cm.tp + cm.fn;
  $("#sub-resultado").textContent = `limiar ${sel.limiar.toFixed(2).replace(".", ",")}`;
  $("#resumo-teste").innerHTML = `
    <div class="grid g2" style="gap:14px; align-items:center">
      <div>
        <div style="font-size:38px;font-weight:700;letter-spacing:-.03em;line-height:1;color:#0b5d5a">${fmtPct(sel.teste_ajustado.recall)}</div>
        <div class="small muted" style="margin-top:6px">dos clientes que cancelaram foram sinalizados antes</div>
        <div class="split-bar" style="margin-top:14px">
          <span style="width:${sel.teste_ajustado.recall * 100}%;background:#0f766e"></span>
          <span style="width:${(1 - sel.teste_ajustado.recall) * 100}%;background:#e4e7ec"></span>
        </div>
        <div class="tiny muted" style="margin-top:6px">${fmtInt(cm.tp)} de ${fmtInt(totalPos)} cancelamentos capturados · ${fmtInt(cm.fn)} não detectados</div>
      </div>
      <div style="border-left:1px solid var(--line); padding-left:16px">
        <div class="tiny muted">Precisão</div>
        <div style="font-size:20px;font-weight:650">${fmtPct(sel.teste_ajustado.precisao)}</div>
        <div class="tiny muted" style="margin-top:8px">Dos alertas emitidos, ${fmtInt(cm.tp)} de ${fmtInt(cm.tp + cm.fp)} realmente cancelaram.</div>
        <div class="tiny muted" style="margin-top:8px">Acurácia ${fmtPct(sel.teste_ajustado.acuracia)} — menor que a do baseline ingênuo, o que é esperado em base desbalanceada.</div>
      </div>
    </div>`;
  $("#foot-meta").textContent = `Modelo: ${sel.nome} · ${S.meta.proporcao_treino_teste} · semente ${S.meta.seed}`;
}

function kpi(label, value, foot, accent = false) {
  return `<div class="kpi ${accent ? "accent" : ""}">
    <div class="label">${label}</div>
    <div class="value">${value}</div>
    <div class="foot">${foot}</div>
  </div>`;
}

/* ============================================================
   BASE DE DADOS
   ============================================================ */
const SCHEMA = [
  ["customerID", "texto", "identificador", "7043 valores únicos — removido do modelo"],
  ["gender", "categórica", "atributo", "Female / Male"],
  ["SeniorCitizen", "binária", "atributo", "0 / 1"],
  ["Partner", "categórica", "atributo", "Yes / No"],
  ["Dependents", "categórica", "atributo", "Yes / No"],
  ["tenure", "numérica", "atributo", "0 a 72 meses"],
  ["PhoneService", "categórica", "atributo", "Yes / No"],
  ["MultipleLines", "categórica", "atributo", "Yes / No / No phone service"],
  ["InternetService", "categórica", "atributo", "DSL / Fiber optic / No internet service"],
  ["OnlineSecurity", "categórica", "atributo", "Yes / No / No internet service"],
  ["OnlineBackup", "categórica", "atributo", "Yes / No / No internet service"],
  ["DeviceProtection", "categórica", "atributo", "Yes / No / No internet service"],
  ["TechSupport", "categórica", "atributo", "Yes / No / No internet service"],
  ["StreamingTV", "categórica", "atributo", "Yes / No / No internet service"],
  ["StreamingMovies", "categórica", "atributo", "Yes / No / No internet service"],
  ["Contract", "categórica", "atributo", "Month-to-month / One year / Two year"],
  ["PaperlessBilling", "categórica", "atributo", "Yes / No"],
  ["PaymentMethod", "categórica", "atributo", "4 formas de pagamento"],
  ["MonthlyCharges", "numérica", "atributo", "18,25 a 118,75"],
  ["TotalCharges", "numérica", "atributo", "0 a 8.684,80 — 11 brancos tratados"],
  ["Churn", "categórica", "alvo", "Yes (1.869) / No (5.174)"],
];

function renderDados() {
  const S = state.S, eda = S.eda;
  $("#kpis-dados").innerHTML = [
    kpi("Registros", fmtInt(eda.n_registros), "um cliente por linha"),
    kpi("Colunas originais", eda.n_colunas_brutas, `→ ${eda.n_atributos_modelo} atributos (19 originais + 2 derivados)`),
    kpi("Classe positiva", fmtPct(eda.taxa_churn), `${fmtInt(eda.churn_sim)} cancelamentos`),
    kpi("Valores ausentes", eda.ausentes_totalcharges, "em TotalCharges (tenure = 0) → preenchidos com 0"),
  ].join("");

  $("#tabela-schema tbody").innerHTML = SCHEMA.map(([c, t, p, v]) => `
    <tr>
      <td class="mono">${c}</td>
      <td style="text-align:left"><span class="tag ${p === "alvo" ? "sel" : "muted"}">${t}</span></td>
      <td style="text-align:left">${p}</td>
      <td style="text-align:left" class="small muted">${v}</td>
    </tr>`).join("");

  const donutBox = document.createElement("div");
  $("#donut-classe").appendChild(donutBox);
  donut(donutBox, [
    { label: "Cancelou", value: eda.churn_sim, color: "#0f766e" },
    { label: "Permaneceu", value: eda.churn_nao, color: "#d9dee5" },
  ], "taxa de churn");
  legend($("#donut-classe"), [
    { name: `Cancelou (${fmtInt(eda.churn_sim)})`, color: "#0f766e" },
    { name: `Permaneceu (${fmtInt(eda.churn_nao)})`, color: "#d9dee5" },
  ]);

  $("#callout-desbalance").innerHTML = `
    <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 2.5 17.4A2 2 0 0 0 4.2 20h15.6a2 2 0 0 0 1.7-2.6L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>
    <div><b>Base desbalanceada.</b> Apenas ${fmtPct(eda.taxa_churn)} dos clientes cancelaram. Por isso acurácia não é a métrica principal:
    um modelo que sempre responde “não cancela” acerta ${fmtPct(eda.churn_nao / eda.n_registros)} — e não identifica nenhum cliente em risco.</div>`;

  $("#lista-qualidade").innerHTML = [
    [true, "Identificadores únicos: 7.043 customerID, sem duplicatas."],
    [false, `${eda.ausentes_totalcharges} registros com TotalCharges em branco (clientes com tenure = 0), preenchidos com 0.`],
    [true, "customerID removido: é um identificador, não um atributo preditivo."],
    [true, "Divisão treino/teste estratificada antes de qualquer ajuste."],
    [true, "Padronização e one-hot ajustados somente no conjunto de treino."],
    [true, "Nenhum atributo derivado do alvo (sem vazamento de rótulo)."],
  ].map(([ok, t]) => `<li class="${ok ? "" : "bad"}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">${ok ? '<path d="m5 13 4 4L19 7"/>' : '<path d="M12 8v5M12 17h.01"/><circle cx="12" cy="12" r="9"/>'}</svg>
      <span>${t}</span></li>`).join("");

  const b = S.baseline, sel = S.selecionado;
  $("#bloco-acuracia").innerHTML = `
    <div class="grid g2" style="align-items:center">
      <div>
        <p class="small">Em uma base com ${fmtPct(eda.taxa_churn)} de cancelamentos, dizer “ninguém vai cancelar” produz
        <b>${fmtPct(b.acuracia)} de acurácia</b> — e <b>zero</b> de recall. O modelo escolhido tem acurácia um pouco menor
        (${fmtPct(sel.teste_ajustado.acuracia)}), mas encontra ${fmtPct(sel.teste_ajustado.recall)} dos cancelamentos reais.
        Para retenção, esse é o trade-off correto.</p>
        <div class="callout neutral" style="margin-top:12px">
          <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m7 14 4-4 3 3 5-6"/></svg>
          <div>Acurácia, precisão, recall, F1, ROC-AUC e PR-AUC foram calculados no conjunto de teste de ${fmtInt(S.meta.n_teste)} clientes.</div>
        </div>
      </div>
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Modelo</th><th>Acurácia</th><th>Recall</th><th>F1</th></tr></thead>
          <tbody>
            <tr><td>Baseline ingênuo</td><td class="num">${fmtPct(b.acuracia)}</td><td class="num" style="color:#b3261e">${fmtPct(b.recall)}</td><td class="num">${fmt3(b.f1)}</td></tr>
            <tr class="selected"><td>${sel.nome}</td><td class="num">${fmtPct(sel.teste_ajustado.acuracia)}</td><td class="num best">${fmtPct(sel.teste_ajustado.recall)}</td><td class="num">${fmt3(sel.teste_ajustado.f1)}</td></tr>
          </tbody>
        </table>
      </div>
    </div>`;
}

/* ============================================================
   ANÁLISE EXPLORATÓRIA
   ============================================================ */
function renderEDA() {
  const eda = state.S.eda;
  const ordem = (arr, o) => [...arr].sort((a, b) => o.indexOf(a.grupo) - o.indexOf(b.grupo));

  barsH($("#chart-contrato"), ordem(eda.churn_por_contrato, ["Month-to-month", "One year", "Two year"]).map((d) => ({
    label: d.grupo === "Month-to-month" ? "Mensal" : d.grupo === "One year" ? "1 ano" : "2 anos",
    value: d.taxa, extra: ` · ${fmtInt(d.n)} clientes`,
  })), { fmt: (v) => fmtPct(v), max: 0.5, colorFn: (d, i) => ["#b3261e", "#d97706", "#15803d"][i] });

  barsH($("#chart-tenure"), eda.churn_por_tenure.map((d) => ({ label: `${d.grupo} meses`, value: d.taxa, extra: ` · ${fmtInt(d.n)} clientes` })),
    { fmt: (v) => fmtPct(v), max: 0.6, colorFn: (d, i) => `hsl(176 ${72 - i * 6}% ${28 + i * 7}%)` });

  barsH($("#chart-internet"), eda.churn_por_internet.map((d) => ({ label: d.grupo, value: d.taxa, extra: ` · ${fmtInt(d.n)}` })),
    { fmt: (v) => fmtPct(v), max: 0.45, color: "#0f766e" });

  barsH($("#chart-pagamento"), eda.churn_por_pagamento.map((d) => ({ label: d.grupo.replace(" (automatic)", " (auto)"), value: d.taxa, extra: ` · ${fmtInt(d.n)}` })),
    { fmt: (v) => fmtPct(v), max: 0.5, color: "#0e7490" });

  const hist = eda.hist_mensalidade;
  const bins = hist.bordas.slice(0, -1).map((b, i) => `${Math.round(b)}–${Math.round(hist.bordas[i + 1])}`);
  const box = $("#chart-hist");
  barsGrouped(box, bins, [
    { name: "Permaneceu", values: hist.ficou, color: "#cbd5e1" },
    { name: "Cancelou", values: hist.cancelou, color: "#0f766e" },
  ], { xLabel: "cobrança mensal (R$)" });
  legend(box, [{ name: "Permaneceu", color: "#cbd5e1" }, { name: "Cancelou", color: "#0f766e" }]);

  const corr = eda.correlacao_numericas;
  const nomes = { tenure: "Tempo de casa", MonthlyCharges: "Cobrança mensal", TotalCharges: "Total pago", CobrancaMedia: "Cobrança média", ServicosContratados: "Serviços contratados", SeniorCitizen: "Idoso (0/1)" };
  const itens = Object.entries(corr).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ label: nomes[k] || k, value: Math.abs(v), corr: v }));
  barsH($("#chart-corr"), itens, {
    fmt: (v) => {
      const it = itens.find((i) => Math.abs(i.value - v) < 1e-9);
      return (it.corr > 0 ? "+" : "−") + Math.abs(it.corr).toFixed(2).replace(".", ",");
    },
    max: 0.4,
    colorFn: (d) => (d.corr > 0 ? "#b3261e" : "#0f766e"),
  });
  legend($("#chart-corr"), [{ name: "Aumenta o churn", color: "#b3261e" }, { name: "Reduz o churn", color: "#0f766e" }]);

  const ct = eda.churn_por_contrato.find((d) => d.grupo === "Month-to-month");
  const c2 = eda.churn_por_contrato.find((d) => d.grupo === "Two year");
  const t6 = eda.churn_por_tenure.find((d) => d.grupo === "0-6");
  const t72 = eda.churn_por_tenure.find((d) => d.grupo === "49-72");
  const fibra = eda.churn_por_internet.find((d) => d.grupo === "Fiber optic");
  const dsl = eda.churn_por_internet.find((d) => d.grupo === "DSL");
  const check = eda.churn_por_pagamento.find((d) => d.grupo === "Electronic check");

  $("#insights-eda").innerHTML = [
    insight("Contrato é o sinal mais forte", `Contrato mensal tem ${fmtPct(ct.taxa)} de churn, contra ${fmtPct(c2.taxa)} no contrato de dois anos — ${(ct.taxa / c2.taxa).toFixed(0)}× mais. Sem fidelidade, sair é barato.`),
    insight("O risco cai com o tempo de casa", `Clientes com até 6 meses cancelam a ${fmtPct(t6.taxa)}; acima de 4 anos, ${fmtPct(t72.taxa)}. Os primeiros meses concentram a maior perda.`),
    insight("Fibra e cheque eletrônico", `Fibra óptica (${fmtPct(fibra.taxa)}) supera DSL (${fmtPct(dsl.taxa)}); pagamento por cheque eletrônico concentra ${fmtPct(check.taxa)} de churn.`),
  ].join("");
}
function insight(t, d) {
  return `<div class="card card-pad"><h3 style="font-size:14px">${t}</h3><p class="small muted" style="margin-top:6px">${d}</p></div>`;
}

/* ============================================================
   MODELO DE MACHINE LEARNING
   ============================================================ */
const ALGOS = {
  logistica: {
    como: `A regressão logística calcula uma soma ponderada dos atributos e aplica a função sigmoide, que comprime o resultado para o intervalo (0, 1). Os pesos são estimados maximizando a verossimilhança (minimizando a entropia cruzada). Cada coeficiente é interpretável: indica o efeito de um atributo nas chances de churn, mantendo os demais constantes.`,
    forca: "Simples, rápida, estável e com probabilidades razoavelmente calibradas. Serve de referência (baseline) forte.",
    limite: "Assume relação linear entre os atributos e o log-odds; interações precisam ser criadas manualmente.",
  },
  arvore: {
    como: `Uma árvore de decisão divide os clientes recursivamente por regras do tipo “tenure ≤ 6 meses?”. Em cada nó, escolhe a divisão que mais reduz a impureza (Gini) da classe. As folhas devolvem a proporção de cancelamentos observada no treino.`,
    forca: "Totalmente interpretável e capaz de capturar relações não lineares e interações sem transformação.",
    limite: "Alta variância: pequenas mudanças nos dados alteram a árvore. Profundidade e número mínimo de amostras por folha controlam o sobreajuste.",
  },
  floresta: {
    como: `Random Forest treina centenas de árvores em amostras bootstrap e, em cada divisão, considera apenas um subconjunto aleatório de atributos. As probabilidades das árvores são então averagedas. A aleatoriedade descorrelaciona as árvores e reduz a variância do conjunto.`,
    forca: "Robusta a ruído e outliers, pouco sensível a escala e difícil de sobreajustar sem ajuste fino.",
    limite: "Menos interpretável; tende a diluir o sinal de atributos raros e é mais pesada em memória.",
  },
  gradient_boosting: {
    como: `Gradient Boosting constrói árvores em sequência: cada nova árvore é ajustada aos resíduos (erros) do conjunto anterior, e sua contribuição é somada com um fator de aprendizado. O resultado é um modelo aditivo de árvores rasas que corrige, passo a passo, os erros das anteriores.`,
    forca: "Excelente desempenho em dados tabulares, captura interações e não lineares com poucos atributos; robusto ao desbalanceamento quando o limiar é ajustado.",
    limite: "Sensível a hiperparâmetros e mais lento para treinar; pode sobreajustar com muitas árvores e profundidade alta.",
  },
  xgboost: {
    como: `XGBoost é uma implementação de gradient boosting com regularização explícita (L1/L2), aproximação de segunda ordem da função de perda, subsampling de linhas e colunas e divisões por histograma. É o mesmo princípio do boosting, com controle mais fino contra sobreajuste.`,
    forca: "Alta performance, treino paralelizável e bom controle de regularização.",
    limite: "Muitos hiperparâmetros; ganhos sobre boosting clássico costumam ser marginais em bases pequenas.",
  },
};

function renderModelo() {
  const S = state.S, sel = S.selecionado, tab = S.tabela;
  const cm = sel.teste_ajustado.matriz_confusao;

  $("#kpis-modelo").innerHTML = [
    kpi("Algoritmos comparados", tab.length, "mesmos dados, mesmo protocolo"),
    kpi("Validação cruzada", "5 folds", "estratificada, só no treino"),
    kpi("Conjunto de teste", fmtInt(S.meta.n_teste), "reservado até a avaliação final"),
    kpi("ROC-AUC do escolhido", fmt3(sel.teste_05.roc_auc), `PR-AUC ${fmt3(sel.teste_05.pr_auc)}`, true),
  ].join("");

  $("#protocolo").innerHTML = `
    <div class="grid g3" style="gap:14px">
      ${[
        ["1. Limpeza", "TotalCharges convertido para número; 11 brancos preenchidos; atributos derivados criados.", "src/features.py"],
        ["2. Divisão", `${fmtInt(S.meta.n_treino)} treino / ${fmtInt(S.meta.n_teste)} teste, estratificada para manter ${fmtPct(S.meta.taxa_churn)} de churn em ambos.`, "train_test_split"],
        ["3. Pré-processamento", "Padronização das numéricas e one-hot das categóricas dentro do Pipeline — ajustado apenas no treino.", "ColumnTransformer"],
        ["4. Busca de hiperparâmetros", "GridSearchCV com 5 folds estratificados no treino, otimizando ROC-AUC.", "GridSearchCV"],
        ["5. Limiar de decisão", "Escolhido por F1 usando previsões out-of-fold do treino, nunca do teste.", "cross_val_predict"],
        ["6. Avaliação final", "Cada modelo é medido uma única vez no teste reservado.", "métricas + bootstrap"],
      ].map(([t, d, tag]) => `<div style="border:1px solid var(--line);border-radius:11px;padding:13px 14px;background:#fbfcfd">
        <div style="font-size:12.5px;font-weight:650">${t}</div>
        <p class="tiny muted" style="margin-top:4px;line-height:1.45">${d}</p>
        <div class="mono" style="font-size:10.5px;color:#0f766e;margin-top:6px">${tag}</div></div>`).join("")}
    </div>
    <div class="callout info" style="margin-top:14px">
      <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3 4 7v6c0 5 3.5 7.5 8 8 4.5-.5 8-3 8-8V7l-8-4Z"/><path d="m9 12 2 2 4-4"/></svg>
      <div><b>Sem vazamento de dados.</b> O teste não participa da escolha de hiperparâmetros, do limiar nem da seleção do modelo.
      O limiar foi definido com previsões out-of-fold do treino e o teste foi aberto uma única vez, ao final.</div>
    </div>`;

  $("#accordion-algoritmos").innerHTML = tab.map((m, i) => {
    const a = ALGOS[m.id];
    const selTag = m.selecionado ? `<span class="tag sel">Selecionado</span>` : "";
    return `<div class="accordion ${m.selecionado ? "open" : ""}" data-acc>
      <button class="acc-head" type="button">
        <span class="idx">${String(i + 1).padStart(2, "0")}</span>
        <span><span class="nm">${m.nome}</span><br><span class="fm">${m.familia}</span></span>
        <span class="res">
          ${selTag}
          <span class="tiny muted">PR-AUC <b style="color:#101828">${fmt3(m.pr_auc)}</b></span>
          <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
        </span>
      </button>
      <div class="acc-body">
        <p><b>Como funciona.</b> ${a.como}</p>
        <p><b>Pontos fortes.</b> ${a.forca} <b>Limitação.</b> ${a.limite}</p>
        <div class="kv">
          ${Object.entries(m.melhor_params).map(([k, v]) => `<span class="pill">${k} = ${v === null ? "None" : v}</span>`).join("")}
        </div>
        <p class="tiny muted" style="margin-top:10px">${m.n_combinacoes} combinações testadas em 5 folds · ${m.tempo_busca_s}s de busca ·
        no teste: ROC-AUC ${fmt3(m.roc_auc)}, PR-AUC ${fmt3(m.pr_auc)}, recall ${fmtPct(m.recall_aj)} no limiar ${m.limiar.toFixed(2).replace(".", ",")}.</p>
      </div>
    </div>`;
  }).join("");
  $$("[data-acc] .acc-head").forEach((b) => b.addEventListener("click", () => b.parentElement.classList.toggle("open")));

  /* tabela comparativa (transposta: métricas nas linhas, modelos nas colunas) */
  const melhor = (key) => Math.max(...tab.map((m) => m[key]));
  const best = { cv_auc: melhor("cv_auc"), pr_auc: melhor("pr_auc"), acuracia: melhor("acuracia"), precisao: melhor("precisao"), recall: melhor("recall"), f1: melhor("f1"), roc_auc: melhor("roc_auc"), recall_aj: melhor("recall_aj"), precisao_aj: melhor("precisao_aj"), f1_aj: melhor("f1_aj") };
  const cls = (k, v) => (Math.abs(v - best[k]) < 1e-9 ? "best" : "");
  const linhas = [
    { rot: "ROC-AUC — validação cruzada (5 folds)", k: "cv_auc", f: (m) => `${fmt3(m.cv_auc)} <span class="tiny muted">± ${m.cv_auc_desvio.toFixed(3).replace(".", ",")}</span>` },
    { rot: "PR-AUC — teste (critério principal)", k: "pr_auc", f: (m) => fmt3(m.pr_auc), destaque: true },
    { rot: "Acurácia — limiar 0,50", k: "acuracia", f: (m) => fmtPct(m.acuracia), grp: true },
    { rot: "Precisão — limiar 0,50", k: "precisao", f: (m) => fmtPct(m.precisao) },
    { rot: "Recall — limiar 0,50", k: "recall", f: (m) => fmtPct(m.recall) },
    { rot: "F1-score — limiar 0,50", k: "f1", f: (m) => fmt3(m.f1) },
    { rot: "ROC-AUC — teste", k: "roc_auc", f: (m) => fmt3(m.roc_auc), grp: true },
    { rot: "Limiar operacional (escolhido no treino)", k: null, f: (m) => m.limiar.toFixed(2).replace(".", ",") },
    { rot: "Recall — limiar operacional", k: "recall_aj", f: (m) => fmtPct(m.recall_aj) },
    { rot: "Precisão — limiar operacional", k: "precisao_aj", f: (m) => fmtPct(m.precisao_aj) },
    { rot: "F1-score — limiar operacional", k: "f1_aj", f: (m) => fmt3(m.f1_aj) },
  ];
  $("#n-teste-tabela").textContent = fmtInt(S.meta.n_teste);
  $("#tabela-comparativa").innerHTML = `
    <thead>
      <tr>
        <th style="min-width:205px">Métrica</th>
        ${tab.map((m) => `<th class="${m.selecionado ? "sel-col" : ""}" style="min-width:86px">${m.nome}${m.selecionado ? '<br><span class="tag sel">selecionado</span>' : ""}</th>`).join("")}
        <th style="min-width:86px;color:#98a2b3">Baseline</th>
      </tr>
    </thead>
    <tbody>
      ${linhas.map((l) => `<tr class="${l.destaque ? "row-destaque" : ""}">
        <td style="text-align:left;${l.grp ? "border-top:1px solid var(--line)" : ""}">${l.rot}</td>
        ${tab.map((m) => `<td class="num ${m.selecionado ? "sel-col" : ""} ${l.k ? cls(l.k, m[l.k]) : ""}" ${l.destaque ? 'style="background:#ecfdf9;color:#0b5d5a;font-weight:700"' : ""}>${l.f(m)}</td>`).join("")}
        <td class="num muted" style="${l.grp ? "border-top:1px solid var(--line)" : ""}">${
          l.k === "acuracia" ? fmtPct(S.baseline.acuracia) :
          l.k === "precisao" ? fmtPct(S.baseline.precisao) :
          l.k === "recall" ? fmtPct(S.baseline.recall) :
          l.k === "f1" ? fmt3(S.baseline.f1) :
          l.k === "roc_auc" ? fmt3(S.baseline.roc_auc) :
          l.k === "pr_auc" ? `${fmt3(S.meta.taxa_churn)}*` :
          l.k === "recall_aj" ? fmtPct(S.baseline.recall) :
          l.k === "precisao_aj" ? fmtPct(S.baseline.precisao) :
          l.k === "f1_aj" ? fmt3(S.baseline.f1) : "—"
        }</td>
      </tr>`).join("")}
    </tbody>`;
  $("#nota-tabela").innerHTML = `* PR-AUC de um classificador aleatório equivale à prevalência da classe positiva (${fmtPct(S.meta.taxa_churn)}).
    <b>Negrito</b> = melhor valor da coluna. A seleção usou PR-AUC (critério principal para classe minoritária) e, entre modelos com diferença menor que 0,01, o F1 no limiar operacional.
    Intervalos de confiança de 95% por bootstrap (2.000 reamostragens) para o modelo escolhido: recall ${fmtPct(sel.ic95.recall[0])}–${fmtPct(sel.ic95.recall[1])}, F1 ${fmt3(sel.ic95.f1[0])}–${fmt3(sel.ic95.f1[1])}, ROC-AUC ${fmt3(sel.ic95.roc_auc[0])}–${fmt3(sel.ic95.roc_auc[1])}.`;

  /* curvas ROC / PR */
  const rocSeries = Object.entries(S.comparacao_roc).map(([id, m]) => ({
    name: `${m.nome} (${fmt3(m.auc)})`,
    color: CORES_MODELO[id],
    width: id === sel.id ? 2.8 : 1.7,
    opacity: id === sel.id ? 1 : 0.75,
    points: m.roc.map((p) => ({ x: p.fpr, y: p.tpr })),
  }));
  const rocBox = $("#chart-roc");
  lines(rocBox, rocSeries, { xLabel: "taxa de falsos positivos", yLabel: "taxa de verdadeiros positivos", diagonal: true, h: 300 });
  legend(rocBox, rocSeries.map((s) => ({ name: s.name, color: s.color })));

  const prSeries = [{ name: sel.nome, color: "#0f766e", width: 2.8, points: sel.pr.map((p) => ({ x: p.recall, y: p.precisao })) }];
  const prBox = $("#chart-pr");
  const prSvg = lines(prBox, prSeries, { xLabel: "recall", yLabel: "precisão", h: 300, xMax: 1, yMax: 1 });
  legend(prBox, [{ name: `${sel.nome} · PR-AUC ${fmt3(sel.teste_05.pr_auc)}`, color: "#0f766e" },
    { name: `acaso · ${fmtPct(S.meta.taxa_churn)}`, color: "#cbd5e1" }]);
  const yAcaso = 14 + (300 - 38 - 14) * (1 - S.meta.taxa_churn);
  const Wp = Number(prSvg.getAttribute("viewBox").split(" ")[2]);
  lineEl(prSvg, { x1: 46, y1: yAcaso, x2: Wp - 14, y2: yAcaso, stroke: "#cbd5e1", "stroke-dasharray": "5 5", "stroke-width": 1.4 });

  /* selecionado */
  $("#sel-nome").textContent = sel.nome;
  $("#sel-familia").textContent = `${sel.familia} · limiar ${sel.limiar.toFixed(2).replace(".", ",")}`;
  $("#sel-hint").textContent = `escolhido entre ${tab.length} algoritmos`;
  $("#sel-justificativa").innerHTML = textoJustificativa(S, sel);
  $("#sel-kpis").innerHTML = [
    kpi("Recall (cancelou)", fmtPct(sel.teste_ajustado.recall), `IC 95%: ${fmtPct(sel.ic95.recall[0])}–${fmtPct(sel.ic95.recall[1])}`, true),
    kpi("Precisão", fmtPct(sel.teste_ajustado.precisao), `IC 95%: ${fmtPct(sel.ic95.precisao[0])}–${fmtPct(sel.ic95.precisao[1])}`),
    kpi("F1-score", fmt3(sel.teste_ajustado.f1), `IC 95%: ${fmt3(sel.ic95.f1[0])}–${fmt3(sel.ic95.f1[1])}`),
    kpi("ROC-AUC", fmt3(sel.teste_05.roc_auc), `IC 95%: ${fmt3(sel.ic95.roc_auc[0])}–${fmt3(sel.ic95.roc_auc[1])}`),
  ].join("");

  const hm = document.createElement("div");
  $("#sel-matriz").appendChild(hm);
  heatmap(hm, cm);
  const extra = document.createElement("p");
  extra.className = "tiny muted";
  extra.style.marginTop = "6px";
  extra.textContent = `De ${fmtInt(cm.tp + cm.fn)} clientes que cancelaram, ${fmtInt(cm.tp)} foram sinalizados (${fmtPct(sel.teste_ajustado.recall)}). ${fmtInt(cm.fp)} falsos alarmes entre ${fmtInt(cm.tn + cm.fp)} que permaneceram.`;
  $("#sel-matriz").appendChild(extra);

  $("#sel-params").innerHTML = `<div class="kv">${Object.entries(sel.melhor_params).map(([k, v]) => `<span class="pill">${k} = ${v === null ? "None" : v}</span>`).join("")}</div>`;

  const calBox = document.createElement("div");
  calBox.style.marginTop = "14px";
  $("#sel-calib").appendChild(calBox);
  const calPts = sel.calibracao.map((c) => ({ x: c.prob_media, y: c.taxa_observada }));
  lines(calBox, [
    { name: "ideal", color: "#cbd5e1", width: 1.4, dash: "5 5", points: [{ x: 0, y: 0 }, { x: 1, y: 1 }] },
    { name: "observado", color: "#0f766e", width: 2.4, points: calPts },
  ], { h: 210, xLabel: "probabilidade prevista", yLabel: "taxa observada" });
  const cap = document.createElement("p");
  cap.className = "tiny muted";
  cap.style.marginTop = "4px";
  cap.textContent = "Calibração: a probabilidade prevista acompanha de perto a taxa observada de churn no teste.";
  calBox.appendChild(cap);

  renderLimiar();
  renderImportancia();
  renderComoFunciona();
  renderLimitacoes();
  renderFicha();
}

function textoJustificativa(S, sel) {
  const tab = S.tabela;
  const gb = tab.find((m) => m.id === sel.id);
  const xgb = tab.find((m) => m.id === "xgboost");
  const rf = tab.find((m) => m.id === "floresta");
  const cm = sel.teste_ajustado.matriz_confusao;
  const totalPos = cm.tp + cm.fn;
  let segundo = "";
  if (xgb) {
    segundo = ` O XGBoost, concorrente mais próximo, ficou em ${fmt3(xgb.pr_auc)} de PR-AUC e ${fmt3(xgb.f1_aj)} de F1`;
    segundo += xgb.f1_aj < gb.f1_aj ? " — abaixo nos dois critérios." : ".";
  }
  const rfNota = rf && rf.recall > sel.teste_05.recall
    ? ` O Random Forest tem recall maior no limiar 0,50 (${fmtPct(rf.recall)}), mas perde em precisão e PR-AUC; o limiar mais baixo apenas desloca o trade-off, sem melhorar a separação entre as classes.`
    : "";
  return `
    <p style="margin:0 0 10px">Foram avaliados <b>${tab.length} algoritmos</b> nos mesmos conjuntos de treino (${fmtInt(S.meta.n_treino)} clientes)
    e teste (${fmtInt(S.meta.n_teste)} clientes), com hiperparâmetros ajustados por validação cruzada de 5 folds
    <b>apenas no treino</b>. Como a base é desbalanceada (${fmtPct(S.meta.taxa_churn)} de churn) e deixar passar um cancelamento
    custa caro, o critério principal foi o <b>PR-AUC</b> (average precision), que resume o trade-off precisão/recall na classe
    “cancelou” — e não a acurácia, dominada pela classe majoritária.</p>
    <p style="margin:0 0 10px"><b>${sel.nome}</b> obteve o maior PR-AUC (${fmt3(gb.pr_auc)}) e o melhor F1 no limiar operacional
    (${fmt3(gb.f1_aj)}).${segundo}${rfNota}</p>
    <p style="margin:0">No limiar <b>${sel.limiar.toFixed(2).replace(".", ",")}</b>, definido por F1 com previsões out-of-fold do treino,
    o modelo identifica <b>${cm.tp} dos ${totalPos}</b> clientes que efetivamente cancelaram no teste (${fmtPct(sel.teste_ajustado.recall)} de recall),
    com precisão de ${fmtPct(sel.teste_ajustado.precisao)} e ROC-AUC de ${fmt3(sel.teste_05.roc_auc)}.
    O conjunto de teste foi aberto uma única vez, ao final: nenhum hiperparâmetro, limiar ou escolha de modelo usou esses rótulos.</p>`;
}

/* ---- limiar interativo (recalculado do teste) ---- */function metricasNoLimiar(t) {
  let tp = 0, fp = 0, fn = 0, tn = 0;
  for (const r of state.AMOSTRA) {
    const prev = r.prob_churn >= t ? 1 : 0;
    if (prev === 1 && r.churn_real === 1) tp++;
    else if (prev === 1 && r.churn_real === 0) fp++;
    else if (prev === 0 && r.churn_real === 1) fn++;
    else tn++;
  }
  const prec = tp + fp ? tp / (tp + fp) : 0;
  const rec = tp + fn ? tp / (tp + fn) : 0;
  const f1 = prec + rec ? (2 * prec * rec) / (prec + rec) : 0;
  const acc = (tp + tn) / (tp + tn + fp + fn);
  return { tp, fp, fn, tn, prec, rec, f1, acc, n: tp + tn + fp + fn };
}

function renderLimiar() {
  const sel = state.S.selecionado;
  const slider = $("#slider-limiar");
  slider.value = Math.round(sel.limiar * 100);
  const upd = () => {
    const t = Number(slider.value) / 100;
    state.limiar = t;
    const m = metricasNoLimiar(t);
    $("#limiar-kpis").innerHTML = [
      kpi("Recall", fmtPct(m.rec), `${fmtInt(m.tp)} de ${fmtInt(m.tp + m.fn)} cancelamentos`),
      kpi("Precisão", fmtPct(m.prec), `${fmtInt(m.fp)} falsos alarmes`),
      kpi("F1-score", fmt3(m.f1), `limiar ${t.toFixed(2).replace(".", ",")}`),
    ].join("");
    const acoes = m.tp + m.fp;
    $("#limiar-texto").innerHTML = `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></svg>
      <div>Com limiar <b>${t.toFixed(2).replace(".", ",")}</b>, o time de retenção abordaria <b>${fmtInt(acoes)} clientes</b> no teste:
      ${fmtInt(m.tp)} cancelamentos seriam interceptados e ${fmtInt(m.fp)} clientes receberiam oferta sem necessidade.
      O limiar de produção escolhido no treino é <b>${sel.limiar.toFixed(2).replace(".", ",")}</b>.</div>`;

    // curva
    const box = $("#chart-limiar");
    box.innerHTML = "";
    const pts = { prec: [], rec: [], f1: [] };
    for (let x = 0.05; x <= 0.9001; x += 0.01) {
      const mm = metricasNoLimiar(x);
      pts.prec.push({ x, y: mm.prec });
      pts.rec.push({ x, y: mm.rec });
      pts.f1.push({ x, y: mm.f1 });
    }
    const svg = lines(box, [
      { name: "Precisão", color: "#b45309", width: 1.9, points: pts.prec },
      { name: "Recall", color: "#0f766e", width: 1.9, points: pts.rec },
      { name: "F1", color: "#334155", width: 2.4, points: pts.f1 },
    ], { h: 250, xLabel: "limiar de decisão", yLabel: "valor da métrica", marker: t });
    legend(box, [{ name: "Precisão", color: "#b45309" }, { name: "Recall", color: "#0f766e" }, { name: "F1", color: "#334155" }]);
  };
  slider.oninput = upd;
  upd();
}

/* ---- importância ---- */
function renderImportancia() {
  const imp = state.S.selecionado.importancia;
  const nomes = {
    tenure: "Tempo de casa", Contract: "Tipo de contrato", InternetService: "Serviço de internet",
    OnlineSecurity: "Segurança online", TechSupport: "Suporte técnico", PaymentMethod: "Forma de pagamento",
    TotalCharges: "Total pago", PaperlessBilling: "Fatura digital", MultipleLines: "Múltiplas linhas",
    SeniorCitizen: "Idoso", MonthlyCharges: "Cobrança mensal", CobrancaMedia: "Cobrança média",
    ServicosContratados: "Serviços contratados", Dependents: "Dependentes", Partner: "Parceiro(a)",
    gender: "Gênero", PhoneService: "Telefone", OnlineBackup: "Backup online",
    DeviceProtection: "Proteção do aparelho", StreamingTV: "Streaming TV", StreamingMovies: "Streaming filmes",
  };
  const itens = imp.slice(0, 10).map((d) => ({ label: nomes[d.atributo] || d.atributo, value: d.queda_auc, desvio: d.desvio }));
  barsH($("#chart-importancia"), itens, { fmt: (v) => fmt3(v), color: "#0f766e", padL: 178 });

  const top = itens[0];
  $("#importancia-texto").innerHTML = `
    <h3 style="font-size:15px">Leitura da importância</h3>
    <p class="small muted" style="margin-top:8px">A importância por permutação mede o quanto o ROC-AUC cai quando os valores de um atributo são embaralhados no teste,
    quebrando sua relação com o alvo. Não é causalidade: indica dependência aprendida pelo modelo.</p>
    <p class="small" style="margin-top:10px"><b>${top.label}</b> é o atributo mais importante: embaralhá-lo derruba o ROC-AUC em ${fmt3(top.value)} pontos.
    ${itens[1] ? `<b>${itens[1].label}</b> vem em seguida (${fmt3(itens[1].value)}).` : ""}</p>
    <p class="small muted" style="margin-top:10px">O resultado conversa com a análise exploratória: contrato mensal e pouco tempo de casa são os
    principais marcadores de risco. Variáveis demográficas têm peso pequeno — o modelo se apoia sobretudo no comportamento contratual.</p>`;
}

/* ---- como funciona ---- */
function renderComoFunciona() {
  const sel = state.S.selecionado;
  const p = sel.melhor_params;
  $("#como-funciona").innerHTML = `
    <h3 style="font-size:15px">O modelo escolhido: Gradient Boosting</h3>
    <p class="small" style="margin-top:10px">Gradient Boosting é um <b>ensemble aditivo</b>: em vez de treinar uma árvore profunda, treina muitas árvores rasas,
    cada uma corrigindo os erros da soma das anteriores. O resultado final é a soma das contribuições de todas as árvores.</p>
    <div class="math" style="margin-top:12px">
      <div><span class="c"># pontuação inicial (log-odds da prevalência)</span></div>
      <div>F₀(x) = log(p / (1 − p))</div>
      <div style="margin-top:8px"><span class="c"># cada árvore hₘ ajusta o resíduo (gradiente negativo)</span></div>
      <div>rᵢ = yᵢ − σ(Fₘ₋₁(xᵢ))</div>
      <div>Fₘ(x) = Fₘ₋₁(x) + <span class="hl">ν</span> · hₘ(x)</div>
      <div style="margin-top:8px"><span class="c"># probabilidade final</span></div>
      <div>P(churn) = σ(F_M(x)) = 1 / (1 + e<sup>−F_M(x)</sup>)</div>
    </div>
    <p class="small" style="margin-top:12px">Com <span class="mono">learning_rate = ${p.learning_rate ?? "—"}</span>,
    <span class="mono">max_depth = ${p.max_depth ?? "—"}</span> e
    <span class="mono">n_estimators = ${p.n_estimators ?? "—"}</span>, o modelo combina ${p.n_estimators ?? "várias"} árvores de profundidade
    ${p.max_depth ?? "—"}: cada uma enxerga no máximo ${2 ** (p.max_depth ?? 1)} folhas. Árvores rasas capturam interações simples
    (por exemplo, “contrato mensal <b>e</b> pouco tempo de casa”) sem decorar o treino.</p>
    <p class="small muted" style="margin-top:10px">Por que funciona bem aqui: os atributos são majoritariamente categóricos, as relações são não lineares
    (o risco cai com o tempo de casa, mas não de forma linear) e há interações relevantes entre contrato, serviços e forma de pagamento.</p>`;
}

function renderLimitacoes() {
  const sel = state.S.selecionado;
  $("#limitacoes").innerHTML = `
    <h3 style="font-size:15px">Limitações e uso responsável</h3>
    <ul class="list-check" style="margin-top:12px">
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 13 4 4L19 7"/></svg><span><b>Correlação não é causalidade.</b> O modelo identifica associação estatística; não prova que mudar um atributo altera o cancelamento.</span></li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 13 4 4L19 7"/></svg><span><b>Validação temporal ausente.</b> A divisão é aleatória, não por data. Em produção, recomenda-se validar em um período futuro para medir deriva (drift).</span></li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 13 4 4L19 7"/></svg><span><b>Base de uma única operadora.</b> Os padrões podem não se transferir para outro mercado; recalibrar antes de usar em outra empresa.</span></li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 13 4 4L19 7"/></svg><span><b>Probabilidade ≠ certeza.</b> O intervalo de confiança do recall vai de ${fmtPct(sel.ic95.recall[0])} a ${fmtPct(sel.ic95.recall[1])}; decisões individuais devem ser combinadas com julgamento humano.</span></li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 13 4 4L19 7"/></svg><span><b>Atributos sensíveis.</b> Gênero e faixa etária entram como variáveis; o uso em ofertas deve passar por auditoria de equidade antes de virar política comercial.</span></li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 13 4 4L19 7"/></svg><span><b>Monitoramento.</b> Métricas devem ser reavaliadas periodicamente e o modelo retreinado quando a distribuição dos clientes mudar.</span></li>
    </ul>`;
}

function renderFicha() {
  const S = state.S, sel = S.selecionado, info = state.INFO;
  $("#ficha-tecnica").innerHTML = `
    <div class="grid g4" style="gap:14px">
      ${[
        ["Algoritmo", sel.nome], ["Família", sel.familia],
        ["Atributos de entrada", `${info.n_atributos_originais} atributos → ${info.n_atributos_transformados} colunas após one-hot`],
        ["Limiar de decisão", sel.limiar.toFixed(2).replace(".", ",")],
        ["Treino / teste", `${fmtInt(S.meta.n_treino)} / ${fmtInt(S.meta.n_teste)}`],
        ["Semente", S.meta.seed], ["Artefato", "artifacts/modelo_previa.joblib"],
        ["Gerado em", new Date(S.meta.gerado_em).toLocaleString("pt-BR")],
      ].map(([k, v]) => `<div><div class="tiny muted">${k}</div><div style="font-weight:620;font-size:13px;margin-top:2px">${v}</div></div>`).join("")}
    </div>
    <div class="callout neutral" style="margin-top:16px">
      <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h5"/></svg>
      <div>Reprodutibilidade: <span class="mono">python src/train.py</span> regenera todos os números deste painel a partir da base pública,
      com semente ${S.meta.seed}. A API (<span class="mono">src/api.py</span>) carrega o mesmo artefato para prever novos clientes.</div>
    </div>`;
}

/* ============================================================
   SIMULADOR
   ============================================================ */
const CAMPOS = [
  ["gender", "Gênero", "select", ["Female", "Male"]],
  ["SeniorCitizen", "Idoso (60+)", "select", [[0, "Não"], [1, "Sim"]]],
  ["Partner", "Tem parceiro(a)", "select", ["No", "Yes"]],
  ["Dependents", "Tem dependentes", "select", ["No", "Yes"]],
  ["tenure", "Tempo de casa (meses)", "number", { min: 0, max: 100 }],
  ["Contract", "Tipo de contrato", "select", ["Month-to-month", "One year", "Two year"]],
  ["InternetService", "Serviço de internet", "select", ["DSL", "Fiber optic", "No internet service"]],
  ["PaymentMethod", "Forma de pagamento", "select", ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]],
  ["MonthlyCharges", "Cobrança mensal (R$)", "number", { min: 0, max: 500, step: 0.05 }],
  ["TotalCharges", "Total já pago (R$)", "number", { min: 0, max: 100000, step: 0.05 }],
  ["PhoneService", "Serviço de telefone", "select", ["Yes", "No"]],
  ["MultipleLines", "Múltiplas linhas", "select", ["No", "Yes", "No phone service"]],
  ["OnlineSecurity", "Segurança online", "select", ["No", "Yes", "No internet service"]],
  ["OnlineBackup", "Backup online", "select", ["No", "Yes", "No internet service"]],
  ["DeviceProtection", "Proteção do aparelho", "select", ["No", "Yes", "No internet service"]],
  ["TechSupport", "Suporte técnico", "select", ["No", "Yes", "No internet service"]],
  ["StreamingTV", "Streaming de TV", "select", ["No", "Yes", "No internet service"]],
  ["StreamingMovies", "Streaming de filmes", "select", ["No", "Yes", "No internet service"]],
  ["PaperlessBilling", "Fatura digital", "select", ["Yes", "No"]],
];

const PRESETS = {
  novo: { gender: "Female", SeniorCitizen: 0, Partner: "No", Dependents: "No", tenure: 2, Contract: "Month-to-month", InternetService: "Fiber optic", PaymentMethod: "Electronic check", MonthlyCharges: 95.5, TotalCharges: 191, PhoneService: "Yes", MultipleLines: "No", OnlineSecurity: "No", OnlineBackup: "No", DeviceProtection: "No", TechSupport: "No", StreamingTV: "Yes", StreamingMovies: "Yes", PaperlessBilling: "Yes" },
  fiel: { gender: "Male", SeniorCitizen: 0, Partner: "Yes", Dependents: "Yes", tenure: 60, Contract: "Two year", InternetService: "DSL", PaymentMethod: "Bank transfer (automatic)", MonthlyCharges: 60.1, TotalCharges: 2884.8, PhoneService: "Yes", MultipleLines: "Yes", OnlineSecurity: "Yes", OnlineBackup: "Yes", DeviceProtection: "Yes", TechSupport: "Yes", StreamingTV: "No", StreamingMovies: "No", PaperlessBilling: "No" },
  medio: { gender: "Female", SeniorCitizen: 0, Partner: "No", Dependents: "Yes", tenure: 24, Contract: "One year", InternetService: "DSL", PaymentMethod: "Mailed check", MonthlyCharges: 74.3, TotalCharges: 1783.2, PhoneService: "Yes", MultipleLines: "Yes", OnlineSecurity: "No", OnlineBackup: "Yes", DeviceProtection: "Yes", TechSupport: "No", StreamingTV: "Yes", StreamingMovies: "Yes", PaperlessBilling: "Yes" },
  risco: { gender: "Male", SeniorCitizen: 1, Partner: "No", Dependents: "No", tenure: 1, Contract: "Month-to-month", InternetService: "Fiber optic", PaymentMethod: "Electronic check", MonthlyCharges: 79.9, TotalCharges: 79.9, PhoneService: "Yes", MultipleLines: "No", OnlineSecurity: "No", OnlineBackup: "No", DeviceProtection: "No", TechSupport: "No", StreamingTV: "No", StreamingMovies: "No", PaperlessBilling: "Yes" },
};

function renderSimulador() {
  const form = $("#form-cliente");
  form.innerHTML = CAMPOS.map(([id, label, tipo, opts]) => {
    if (tipo === "select") {
      const options = opts.map((o) => Array.isArray(o) ? `<option value="${o[0]}">${o[1]}</option>` : `<option value="${o}">${o}</option>`).join("");
      return `<div class="field"><label for="f-${id}">${label}</label><select id="f-${id}" name="${id}">${options}</select></div>`;
    }
    const o = opts;
    return `<div class="field"><label for="f-${id}">${label}</label><input type="number" id="f-${id}" name="${id}" min="${o.min}" max="${o.max}" step="${o.step || 1}"></div>`;
  }).join("");

  aplicarPreset("novo");
  $$(".preset").forEach((b) => b.addEventListener("click", () => aplicarPreset(b.dataset.preset)));
  $("#btn-prever").addEventListener("click", prever);
  $("#form-cliente").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); prever(); } });

  const box = $("#tabela-novos");
  const nv = state.NOVOS;
  box.innerHTML = `
    <thead><tr><th>Cliente</th><th>Tempo</th><th>Contrato</th><th>Internet</th><th>Cobrança</th><th>Probabilidade</th><th>Faixa</th><th>Ação recomendada</th></tr></thead>
    <tbody>${nv.clientes.map((c) => {
      const cl = c.cliente, f = c.faixa;
      return `<tr>
        <td class="mono">${c.customerID}</td>
        <td class="num">${cl.tenure} m</td>
        <td>${cl.Contract === "Month-to-month" ? "Mensal" : cl.Contract === "One year" ? "1 ano" : "2 anos"}</td>
        <td>${cl.InternetService === "Fiber optic" ? "Fibra" : cl.InternetService === "DSL" ? "DSL" : "Sem internet"}</td>
        <td class="num">R$ ${fmt2(cl.MonthlyCharges)}</td>
        <td class="num"><b>${fmtPct(c.probabilidade)}</b></td>
        <td><span class="badge ${f.rotulo.toLowerCase().replace("í", "i").replace("ó", "o")}"><span class="d"></span>${f.rotulo}</span></td>
        <td class="small muted">${f.acao}</td>
      </tr>`;
    }).join("")}</tbody>`;
  $("#lote-sub").textContent = `${nv.total} perfis · limiar ${nv.limiar.toFixed(2).replace(".", ",")} · previstos pela API`;
}

function aplicarPreset(nome) {
  const p = PRESETS[nome];
  if (!p) return;
  for (const [k, v] of Object.entries(p)) {
    const el = $(`#f-${k}`);
    if (el) el.value = v;
  }
  $("#form-status").textContent = "";
}

function lerFormulario() {
  const o = {};
  for (const [id, , tipo] of CAMPOS) {
    const el = $(`#f-${id}`);
    if (!el) continue;
    o[id] = tipo === "number" ? Number(el.value) : el.value;
  }
  return o;
}

async function prever() {
  const btn = $("#btn-prever");
  const dados = lerFormulario();
  btn.disabled = true;
  $("#form-status").textContent = "Consultando o modelo…";
  try {
    const r = await fetch("/api/prever", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(dados),
    });
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    mostrarResultado(d);
    $("#form-status").textContent = "Previsão calculada pelo modelo em produção.";
  } catch (e) {
    $("#form-status").textContent = "Falha ao consultar a API.";
    console.error(e);
  } finally {
    btn.disabled = false;
  }
}

function mostrarResultado(d) {
  const f = d.faixa;
  const cor = f.cor;
  const classe = f.rotulo.toLowerCase().replace("í", "i").replace("ó", "o");
  const box = $("#resultado");
  box.innerHTML = `
    <div class="result-hero">
      <div class="cap">Probabilidade de cancelamento</div>
      <div class="pct" style="color:${cor}">${fmtPctD(d.probabilidade)}</div>
      <div class="band"><span class="badge ${classe}"><span class="d"></span>Risco ${f.rotulo.toLowerCase()}</span></div>
    </div>
    <div id="gauge-box"></div>
    <div class="action-box"><b>Ação recomendada</b>${f.acao}</div>
    <div class="grid g2" style="gap:10px; margin-top:14px">
      <div><div class="tiny muted">Limiar de decisão</div><div style="font-weight:650">${d.limiar.toFixed(2).replace(".", ",")}</div></div>
      <div><div class="tiny muted">Classificação</div><div style="font-weight:650">${d.previsao === 1 ? "Acionar retenção" : "Sem ação imediata"}</div></div>
    </div>
    ${d.contribuicoes ? `
      <div style="margin-top:18px">
        <div class="small" style="font-weight:650;margin-bottom:4px">Fatores que mais pesaram</div>
        <div class="tiny muted" style="margin-bottom:10px">Contribuição de cada atributo para a probabilidade (valores SHAP, em pontos percentuais).</div>
        <div class="contrib">${d.contribuicoes.map((c) => {
          const max = Math.max(...d.contribuicoes.map((x) => Math.abs(x.impacto_pp))) || 1;
          const w = (Math.abs(c.impacto_pp) / max) * 50;
          const pos = c.impacto_pp >= 0;
          const corr = pos ? "#b3261e" : "#15803d";
          return `<div class="contrib-row">
            <span class="name" title="${c.atributo}">${nomeAtributo(c.atributo)}</span>
            <span class="track"><span class="bar" style="${pos ? `left:50%;width:${w}%` : `right:50%;width:${w}%`};background:${corr}"></span></span>
            <span class="val" style="color:${corr}">${pos ? "+" : "−"}${Math.abs(c.impacto_pp).toFixed(1).replace(".", ",")} p.p.</span>
          </div>`;
        }).join("")}</div>
      </div>` : ""}
    <p class="tiny muted" style="margin-top:14px">Probabilidade calculada pelo modelo treinado (${state.S.selecionado.nome}), não por regra fixa.
    Contribuições via SHAP; a soma parte da probabilidade base de ${fmtPct(d.base_probabilidade)}.</p>`;
  gauge($("#gauge-box"), d.probabilidade, d.limiar);
  $("#res-sub").textContent = `calculado agora · ${new Date().toLocaleTimeString("pt-BR")}`;
}

const NOMES_ATRIBUTO = {
  tenure: "Tempo de casa", Contract: "Contrato", InternetService: "Internet",
  OnlineSecurity: "Segurança online", TechSupport: "Suporte", PaymentMethod: "Pagamento",
  MonthlyCharges: "Cobrança mensal", TotalCharges: "Total pago", PaperlessBilling: "Fatura digital",
  MultipleLines: "Múltiplas linhas", SeniorCitizen: "Idoso", gender: "Gênero",
  Partner: "Parceiro(a)", Dependents: "Dependentes", PhoneService: "Telefone",
  OnlineBackup: "Backup online", DeviceProtection: "Proteção", StreamingTV: "Streaming TV",
  StreamingMovies: "Streaming filmes", ServicosContratados: "Serviços", CobrancaMedia: "Cobrança média",
};
const nomeAtributo = (a) => NOMES_ATRIBUTO[a] || a;

/* ============================================================
   CLIENTES EM RISCO
   ============================================================ */
function faixaDe(p, limiar) {
  if (p >= 0.6) return "critico";
  if (p >= limiar) return "alto";
  if (p >= 0.2) return "moderado";
  return "baixo";
}
const ROTULO_FAIXA = { critico: "Crítico", alto: "Alto", moderado: "Moderado", baixo: "Baixo" };

function renderClientes() {
  const limiar = state.S.selecionado.limiar;
  const total = state.AMOSTRA.length;
  const cont = { critico: 0, alto: 0, moderado: 0, baixo: 0 };
  let acionar = 0, tp = 0, fp = 0;
  for (const r of state.AMOSTRA) {
    cont[faixaDe(r.prob_churn, limiar)]++;
    if (r.prob_churn >= limiar) {
      acionar++;
      if (r.churn_real === 1) tp++; else fp++;
    }
  }
  $("#kpis-clientes").innerHTML = [
    kpi("Clientes avaliados", fmtInt(total), "conjunto de teste (não vistos no treino)"),
    kpi("Na fila de retenção", fmtInt(acionar), `probabilidade ≥ ${limiar.toFixed(2).replace(".", ",")}`, true),
    kpi("Cancelamentos capturados", `${fmtInt(tp)}<small> de ${fmtInt(state.S.selecionado.teste_ajustado.matriz_confusao.tp + state.S.selecionado.teste_ajustado.matriz_confusao.fn)}</small>`, `precisão ${fmtPct(acionar ? tp / acionar : 0)}`),
    kpi("Falsos alarmes", fmtInt(fp), "clientes que permaneceram"),
  ].join("");

  $("#busca-clientes").oninput = (e) => { state.busca = e.target.value.trim().toLowerCase(); state.pagina = 1; desenharTabelaClientes(); };
  $("#filtro-faixa").onchange = (e) => { state.faixa = e.target.value; state.pagina = 1; desenharTabelaClientes(); };
  desenharTabelaClientes();
}

function desenharTabelaClientes() {
  const limiar = state.S.selecionado.limiar;
  let lista = state.AMOSTRA.filter((r) => {
    if (state.faixa !== "todos" && faixaDe(r.prob_churn, limiar) !== state.faixa) return false;
    if (state.busca && !String(r.customerID).toLowerCase().includes(state.busca)) return false;
    return true;
  });
  const porPag = 40;
  const paginas = Math.max(1, Math.ceil(lista.length / porPag));
  state.pagina = Math.min(state.pagina, paginas);
  const ini = (state.pagina - 1) * porPag;
  const pagina = lista.slice(ini, ini + porPag);

  $("#tabela-clientes").innerHTML = `
    <thead><tr><th>Cliente</th><th>Tempo</th><th>Contrato</th><th>Internet</th><th>Pagamento</th><th>Mensalidade</th><th>Prob. de churn</th><th>Faixa</th><th>Desfecho real</th></tr></thead>
    <tbody>${pagina.map((r) => {
      const fx = faixaDe(r.prob_churn, limiar);
      return `<tr>
        <td class="mono">${r.customerID}</td>
        <td class="num">${r.tenure} m</td>
        <td>${r.Contract === "Month-to-month" ? "Mensal" : r.Contract === "One year" ? "1 ano" : "2 anos"}</td>
        <td>${r.InternetService === "Fiber optic" ? "Fibra" : r.InternetService === "DSL" ? "DSL" : "—"}</td>
        <td class="small">${r.PaymentMethod.replace(" (automatic)", " (auto)")}</td>
        <td class="num">R$ ${fmt2(r.MonthlyCharges)}</td>
        <td class="num"><div style="display:flex;align-items:center;gap:8px;justify-content:flex-end">
          <span style="width:56px;height:5px;background:#eef1f5;border-radius:3px;overflow:hidden;display:inline-block">
            <span style="display:block;height:100%;width:${r.prob_churn * 100}%;background:${r.prob_churn >= limiar ? "#0f766e" : "#94a3b8"}"></span></span>
          <b>${fmtPct(r.prob_churn)}</b></div></td>
        <td><span class="badge ${fx}"><span class="d"></span>${ROTULO_FAIXA[fx]}</span></td>
        <td class="small ${r.churn_real === 1 ? "" : "muted"}">${r.churn_real === 1 ? "Cancelou" : "Permaneceu"}</td>
      </tr>`;
    }).join("")}</tbody>`;
  if (!pagina.length) $("#tabela-clientes").innerHTML += `<tbody><tr><td colspan="9" style="text-align:center;color:#98a2b3;padding:30px">Nenhum cliente encontrado.</td></tr></tbody>`;

  $("#pager-clientes").innerHTML = `
    <span>${fmtInt(lista.length)} clientes · página ${state.pagina} de ${paginas}</span>
    <button id="pg-prev" ${state.pagina <= 1 ? "disabled" : ""}>Anterior</button>
    <button id="pg-next" ${state.pagina >= paginas ? "disabled" : ""}>Próxima</button>`;
  $("#pg-prev").onclick = () => { state.pagina--; desenharTabelaClientes(); };
  $("#pg-next").onclick = () => { state.pagina++; desenharTabelaClientes(); };
}
