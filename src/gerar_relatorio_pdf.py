"""Gera o relatorio tecnico completo em PDF.

Uso:  python src/gerar_relatorio_pdf.py

O PDF e o HTML de origem ficam em relatorio/. Todos os numeros vem de
artifacts/resultados.json e dos CSVs gerados por src/train.py.
"""

from relatorio_pdf.build import main

if __name__ == "__main__":
    main()
