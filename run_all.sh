#!/usr/bin/env bash
# Rebuild everything from the raw file. Needs: uv, and (for the PDF only) latexmk with pdfLaTeX.
set -euo pipefail
cd "$(dirname "$0")"
uv sync
cd src
uv run python 01_prepare.py  > ../outputs/log_01_prepare.txt
uv run python 02_explore.py  > ../outputs/log_02_explore.txt
uv run python -W ignore 03_tests.py > ../outputs/log_03_tests.txt
uv run python 04_macros.py
cd ../report
mkdir -p figures && cp ../outputs/figures/*.pdf figures/
cat preamble.tex body.tex > main.tex
if command -v latexmk >/dev/null; then latexmk -pdf -interaction=nonstopmode main.tex >/dev/null && echo "report/main.pdf built"; fi
