"""Monta o HTML e imprime o PDF final."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pymupdf

from .base import RAIZ, REL, SEL
from .estilo import CSS
from .figuras import gerar_todas
from . import secoes_a, secoes_b, secoes_c

EDGE_CAMINHOS = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def montar_html() -> str:
    corpo = (
        secoes_a.capa()
        + '<div class="conteudo">'
        + secoes_a.sumario()
        + secoes_a.resumo()
        + secoes_a.contexto()
        + secoes_a.dados()
        + secoes_a.eda()
        + secoes_a.metodologia()
        + secoes_a.algoritmos()
        + secoes_b.resultados()
        + secoes_b.modelo_limiar()
        + secoes_b.interpretabilidade()
        + secoes_b.operacao()
        + secoes_c.limites()
        + secoes_c.conclusao()
        + secoes_c.reprodutibilidade()
        + secoes_c.anexos()
        + "</div>"
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>PREVIA AI — Relatório técnico de previsão de churn</title>
<meta name="author" content="Mario Joaquim Ferreira">
<meta name="description" content="Relatório técnico do projeto PREVIA AI: previsão de churn com a base IBM Telco Customer Churn.">
<style>{CSS}</style>
</head>
<body>
{corpo}
</body>
</html>
"""


def achar_edge() -> Path:
    for caminho in EDGE_CAMINHOS:
        if caminho.exists():
            return caminho
    raise SystemExit("Microsoft Edge nao encontrado para gerar o PDF.")


def imprimir_pdf(html: Path, pdf_bruto: Path) -> None:
    edge = achar_edge()
    perfil = Path(r"C:\Users\TCM ENGENHARIA\AppData\Local\Temp\opencode\edge-perfil-relatorio")
    comando = [
        str(edge),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-pdf-header-footer",
        f"--user-data-dir={perfil}",
        f"--print-to-pdf={pdf_bruto}",
        html.as_uri(),
    ]
    subprocess.run(comando, capture_output=True, timeout=180)
    limite = time.time() + 30
    while time.time() < limite and not (pdf_bruto.exists() and pdf_bruto.stat().st_size > 10_000):
        time.sleep(0.5)
    if not pdf_bruto.exists():
        raise SystemExit("O Edge nao gerou o PDF.")


def numerar_paginas(pdf_bruto: Path, pdf_final: Path) -> tuple[int, float]:
    doc = pymupdf.open(pdf_bruto)
    total = doc.page_count
    for i, pagina in enumerate(doc):
        if i == 0:
            continue
        largura, altura = pagina.rect.width, pagina.rect.height
        y = altura - 22
        pagina.insert_text(
            (40, y), "PREVIA AI · Relatório técnico · previsão de churn",
            fontsize=6.8, fontname="helv", color=(0.42, 0.47, 0.52),
        )
        texto = f"{i + 1} / {total}"
        largura_texto = pymupdf.get_text_length(texto, fontname="helv", fontsize=7)
        pagina.insert_text(
            (largura - 40 - largura_texto, y), texto,
            fontsize=7, fontname="helv", color=(0.42, 0.47, 0.52),
        )
    doc.set_metadata({
        "title": "PREVIA AI — Relatório técnico de previsão de churn",
        "author": "Mario Joaquim Ferreira",
        "subject": "Previsão de churn com a base IBM Telco Customer Churn",
        "keywords": "churn, machine learning, gradient boosting, retenção, telecomunicações",
        "creator": "PREVIA AI",
        "producer": "Microsoft Edge + PyMuPDF",
    })
    doc.save(pdf_final, garbage=4, deflate=True)
    doc.close()
    return total, pdf_final.stat().st_size / (1024 * 1024)


def main() -> None:
    print("1/4 gerando figuras...")
    gerar_todas()
    print("2/4 montando HTML...")
    html = REL / "relatorio.html"
    html.write_text(montar_html(), encoding="utf-8")
    print("3/4 imprimindo PDF...")
    bruto = REL / "_relatorio_bruto.pdf"
    final = REL / "PREVIA_AI_Relatorio.pdf"
    bruto.unlink(missing_ok=True)
    imprimir_pdf(html, bruto)
    print("4/4 numerando paginas...")
    paginas, tamanho = numerar_paginas(bruto, final)
    bruto.unlink(missing_ok=True)
    print(f"PDF final: {final}")
    print(f"Paginas: {paginas} | Tamanho: {tamanho:.1f} MB | Limiar do modelo: {SEL['limiar']}")


if __name__ == "__main__":
    main()
