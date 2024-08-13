#!/bin/bash

st="2024-08-04"
ed="2024-08-05"
pdf_path="./arxiv_pdfs_${st}_to_${ed}"

python pdf-download-with-cache.py --start_date=${st} --end_date=${ed} --subject="cs"

python pdf_to_table_figures.py --pdf_path=${pdf_path}

