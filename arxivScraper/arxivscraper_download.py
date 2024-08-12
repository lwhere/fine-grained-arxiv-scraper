import arxivscraper
scraper = arxivscraper.Scraper(category='cs', date_from='2024-08-01',date_until='2024-08-10')
output = scraper.scrape()
import pandas as pd
cols = ('id', 'title', 'categories', 'abstract', 'doi', 'created', 'updated', 'authors')
df = pd.DataFrame(output,columns=cols)
df.to_csv('arxiv_data.csv', index=False, encoding='utf-8')
df.to_json('arxiv_data.json', orient='records', lines=True, force_ascii=False)