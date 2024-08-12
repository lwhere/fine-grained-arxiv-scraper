# from paperscraper.get_dumps import biorxiv, medrxiv, chemrxiv
# medrxiv(begin_date="2024-08-01", end_date="2024-08-02")

from paperscraper.pubmed import get_and_dump_pubmed_papers
# covid19 = ['COVID-19', 'SARS-CoV-2']
ai = ['Artificial intelligence', 'Deep learning', 'Machine learning']
# mi = ['Medical imaging']
# query = [covid19, ai, mi]
query = ai

get_and_dump_pubmed_papers(query, output_filepath='ai_pubmed.jsonl')

from paperscraper.arxiv import get_and_dump_arxiv_papers

get_and_dump_arxiv_papers(query, output_filepath='ai_arxiv.jsonl')