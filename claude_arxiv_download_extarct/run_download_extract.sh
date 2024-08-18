#!/bin/bash

st="2024-08-04"
ed="2024-08-05"
pdf_path="./arxiv_pdfs_${st}_to_${ed}"

python pdf-download-with-cache.py --start_date=${st} --end_date=${ed} --subject="cs"

# # Load the pre-trained model from Hugging Face
# python pdf_to_table_figures.py --pdf_path=${pdf_path} --model_id="yifeihu/TF-ID-large"
# python pdf_to_table_figures.py --pdf_path=${pdf_path} --model_id="yifeihu/TF-ID-large-no-caption"

# Load the already downloaded pre-trained model from ./yifeihu/TF-ID-large or ./yifeihu/TF-ID-large-no-caption
# with-caption
python pdf_to_table_figures.py --pdf_path=${pdf_path} --model_id="./yifeihu/TF-ID-large"

# without-caption
python pdf_to_table_figures.py --pdf_path=${pdf_path} --model_id="./yifeihu/TF-ID-large-no-caption"
