"""Folha de estilo do relatorio (otimizada para impressao A4)."""

CSS = r"""
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
@page { size: A4; margin: 16mm 15mm 15mm 15mm; }
@page :first { margin: 0; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Segoe UI", "DejaVu Sans", Arial, sans-serif;
  font-size: 10.2pt; line-height: 1.55; color: #1f2937; background: #fff;
}
p { margin: 0 0 8px; text-align: justify; }
strong { color: #0b3b3a; }
a { color: #0f766e; text-decoration: none; }
small, .small { font-size: 8.6pt; }
.muted { color: #667085; }
.mono { font-family: "Cascadia Mono", Consolas, monospace; font-size: 8.8pt; background: #f6f8fb; padding: 1px 4px; border-radius: 3px; }

/* ---------------- capa ---------------- */
.capa { height: 297mm; padding: 24mm 22mm; background: linear-gradient(160deg, #0b3b3a 0%, #0f5f59 55%, #0f766e 100%); color: #fff; position: relative; page-break-after: always; overflow: hidden; }
.capa:before { content: ""; position: absolute; width: 120mm; height: 120mm; border: 1.2mm solid rgba(94,234,212,.14); border-radius: 50%; right: -45mm; top: -35mm; }
.capa:after { content: ""; position: absolute; width: 80mm; height: 80mm; border: .8mm solid rgba(94,234,212,.16); border-radius: 50%; right: -20mm; bottom: 40mm; }
.capa .marca { display: flex; align-items: center; gap: 5mm; }
.capa .logo { width: 17mm; height: 17mm; border-radius: 4mm; background: #0f766e; border: .4mm solid rgba(94,234,212,.5); display: grid; place-items: center; }
.capa .logo svg { width: 11mm; height: 11mm; }
.capa .marca-nome { font-size: 20pt; font-weight: 700; letter-spacing: .5px; }
.capa .marca-nome span { color: #5eead4; }
.capa .marca-sub { font-size: 8.5pt; letter-spacing: 2.4px; text-transform: uppercase; color: rgba(255,255,255,.72); }
.capa .eyebrow { margin-top: 38mm; font-size: 9pt; letter-spacing: 3px; text-transform: uppercase; color: #5eead4; font-weight: 600; }
.capa h1 { font-size: 34pt; line-height: 1.08; margin: 4mm 0 5mm; font-weight: 700; letter-spacing: -.5px; }
.capa h1 em { color: #5eead4; font-style: normal; }
.capa .subtitulo { font-size: 13pt; color: rgba(255,255,255,.86); max-width: 150mm; line-height: 1.5; }
.capa .faixa { margin-top: 12mm; display: flex; gap: 4mm; flex-wrap: wrap; }
.capa .faixa div { border: .35mm solid rgba(94,234,212,.35); border-radius: 3mm; padding: 2.2mm 3.6mm; font-size: 8.2pt; color: rgba(255,255,255,.9); background: rgba(255,255,255,.04); }
.capa .rodape { position: absolute; left: 22mm; right: 22mm; bottom: 18mm; display: flex; justify-content: space-between; align-items: flex-end; font-size: 8.8pt; color: rgba(255,255,255,.75); border-top: .25mm solid rgba(255,255,255,.2); padding-top: 5mm; }
.capa .rodape b { color: #fff; display: block; font-size: 10pt; }

/* ---------------- estrutura ---------------- */
.conteudo { padding: 0; }
h2 { font-size: 15pt; color: #0b3b3a; margin: 0 0 4mm; padding: 0 0 2.4mm 4mm; border-left: 2.2mm solid #0f766e; border-bottom: .25mm solid #d9e2e0; page-break-after: avoid; line-height: 1.25; }
h2 .num { color: #0f766e; font-size: 9pt; letter-spacing: 1.4px; display: block; margin-bottom: 1mm; text-transform: uppercase; }
h3 { font-size: 11.2pt; color: #134e4a; margin: 6mm 0 2.2mm; page-break-after: avoid; }
h4 { font-size: 10pt; color: #0b3b3a; margin: 4mm 0 1.6mm; page-break-after: avoid; }
section { page-break-before: always; }
section.primeira { page-break-before: avoid; }
ul, ol { margin: 0 0 8px 5mm; padding: 0; }
li { margin-bottom: 2.4px; text-align: justify; }
hr { border: 0; border-top: .2mm solid #e4e7ec; margin: 6mm 0; }

/* ---------------- sumario ---------------- */
.sumario { page-break-after: always; }
.sumario h2 { margin-bottom: 6mm; }
.sumario ol { list-style: none; margin: 0; padding: 0; counter-reset: item; }
.sumario li { counter-increment: item; display: flex; align-items: baseline; gap: 2mm; font-size: 10.2pt; padding: 1.7mm 0; border-bottom: .2mm dotted #d0d5dd; }
.sumario li:before { content: counter(item, decimal-leading-zero); color: #0f766e; font-weight: 700; font-size: 8.6pt; width: 8mm; }
.sumario li span.t { flex: 1; }
.sumario li span.p { color: #667085; font-size: 9pt; }
.sumario .nota { margin-top: 7mm; font-size: 8.8pt; color: #667085; background: #f8fafc; border: .2mm solid #e4e7ec; border-radius: 2mm; padding: 4mm; }

/* ---------------- componentes ---------------- */
.callout { border-left: 1.4mm solid #0f766e; background: #f0fdfa; border-radius: 0 2mm 2mm 0; padding: 3.4mm 4mm; margin: 3mm 0 4mm; page-break-inside: avoid; }
.callout.amber { border-color: #d97706; background: #fffbeb; }
.callout.red { border-color: #b3261e; background: #fef3f2; }
.callout .tit { font-weight: 700; color: #0b3b3a; font-size: 9.4pt; margin-bottom: 1mm; display: block; }

.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.6mm; margin: 3mm 0 5mm; }
.kpi { border: .25mm solid #d9e2e0; border-top: 1.1mm solid #0f766e; border-radius: 2mm; padding: 3mm; background: #fff; page-break-inside: avoid; }
.kpi .v { font-size: 16pt; font-weight: 700; color: #0b3b3a; line-height: 1.1; }
.kpi .k { font-size: 7.8pt; color: #667085; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 1mm; }
.kpi .d { font-size: 7.6pt; color: #667085; margin-top: 1mm; }

table { width: 100%; border-collapse: collapse; margin: 2.5mm 0 4mm; font-size: 8.4pt; page-break-inside: avoid; }
thead th { background: #ecfdf5; color: #0b3b3a; font-weight: 700; text-align: left; padding: 2mm 2.2mm; border-bottom: .3mm solid #99f6e4; }
tbody td { padding: 1.8mm 2.2mm; border-bottom: .2mm solid #eaecf0; vertical-align: top; }
tbody tr:nth-child(even) td { background: #fafcfc; }
table.num tbody td:not(:first-child), table.num thead th:not(:first-child) { text-align: right; }
table.compacta { font-size: 7.8pt; }
table.compacta td, table.compacta th { padding: 1.4mm 1.7mm; }
.destaque { background: #f0fdfa !important; font-weight: 600; color: #0b3b3a; }

figure { margin: 3mm 0 5mm; page-break-inside: avoid; }
figure img { width: 100%; display: block; border: .2mm solid #eaecf0; border-radius: 1.5mm; }
figcaption { font-size: 8pt; color: #667085; margin-top: 1.6mm; line-height: 1.4; }
figcaption b { color: #344054; }
.duas { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; align-items: start; }
.tres { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm; }
.lado { display: grid; grid-template-columns: 1.15fr .85fr; gap: 6mm; align-items: start; }

.fluxo { display: flex; align-items: stretch; gap: 0; margin: 3mm 0 5mm; page-break-inside: avoid; }
.fluxo .etapa { flex: 1; border: .25mm solid #d9e2e0; border-radius: 2mm; padding: 2.6mm; text-align: center; background: #fff; }
.fluxo .etapa b { display: block; font-size: 8.4pt; color: #0b3b3a; }
.fluxo .etapa span { font-size: 7.4pt; color: #667085; }
.fluxo .seta { display: grid; place-items: center; width: 7mm; color: #0f766e; font-size: 12pt; }

.codigo { background: #0b3b3a; color: #d1fae5; border-radius: 2mm; padding: 3.4mm 4mm; font-family: "Cascadia Mono", Consolas, monospace; font-size: 8pt; line-height: 1.55; margin: 2.5mm 0 4mm; white-space: pre-wrap; page-break-inside: avoid; }
.codigo .c { color: #6ee7b7; }

.rubrica { margin-top: 8mm; padding-top: 4mm; border-top: .2mm solid #e4e7ec; font-size: 8.4pt; color: #667085; }
.fim { text-align: center; margin-top: 12mm; font-size: 8.6pt; color: #667085; }

/* ---------------- contracapa ---------------- */
.contracapa { page-break-before: always; background: linear-gradient(160deg, #0b3b3a 0%, #0f5f59 60%, #0f766e 100%); color: #fff; border-radius: 3mm; padding: 20mm 18mm; height: 250mm; position: relative; overflow: hidden; }
.contracapa:before { content: ""; position: absolute; width: 110mm; height: 110mm; border: 1mm solid rgba(94,234,212,.14); border-radius: 50%; right: -35mm; top: -30mm; }
.contracapa:after { content: ""; position: absolute; width: 70mm; height: 70mm; border: .7mm solid rgba(94,234,212,.16); border-radius: 50%; right: -15mm; bottom: 30mm; }
.contracapa .marca { display: flex; align-items: center; gap: 5mm; }
.contracapa .logo { width: 15mm; height: 15mm; border-radius: 3.5mm; background: #0f766e; border: .35mm solid rgba(94,234,212,.5); display: grid; place-items: center; }
.contracapa .logo svg { width: 9.5mm; height: 9.5mm; }
.contracapa .marca-nome { font-size: 17pt; font-weight: 700; letter-spacing: .5px; }
.contracapa .marca-nome span { color: #5eead4; }
.contracapa .marca-sub { font-size: 7.8pt; letter-spacing: 2.2px; text-transform: uppercase; color: rgba(255,255,255,.7); }
.contracapa .eyebrow { margin-top: 30mm; font-size: 8.5pt; letter-spacing: 3px; text-transform: uppercase; color: #5eead4; font-weight: 600; }
.contracapa h2 { color: #fff; border: 0; padding: 0; font-size: 25pt; margin: 3mm 0 9mm; }
.contracapa .links { display: grid; gap: 4mm; }
.contracapa .links div { border-left: 1mm solid #5eead4; padding: 3mm 5mm; background: rgba(255,255,255,.06); border-radius: 0 2mm 2mm 0; }
.contracapa .links b { display: block; font-size: 7.8pt; letter-spacing: 1.6px; text-transform: uppercase; color: #5eead4; margin-bottom: 1mm; }
.contracapa .links span { font-size: 10.5pt; }
.contracapa .nota { color: rgba(255,255,255,.8); font-size: 9pt; margin-top: 9mm; max-width: 145mm; }
.contracapa .rodape { position: absolute; left: 18mm; right: 18mm; bottom: 14mm; border-top: .25mm solid rgba(255,255,255,.22); padding-top: 4mm; font-size: 8.2pt; color: rgba(255,255,255,.72); display: flex; justify-content: space-between; }
"""
