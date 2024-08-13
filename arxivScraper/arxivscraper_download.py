import arxivscraper
from datetime import datetime
import pandas as pd

# 定义时间范围
date_from = '2024-01-01'
date_until = '2024-07-31'

# 将日期字符串转换为datetime对象
date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
date_until_dt = datetime.strptime(date_until, '%Y-%m-%d')

# 使用arxivscraper获取数据
scraper = arxivscraper.Scraper(category='cs', date_from=date_from, date_until=date_until)
output = scraper.scrape()

# 创建DataFrame
cols = ('id', 'title', 'categories', 'abstract', 'doi', 'created', 'updated', 'authors')
df = pd.DataFrame(output, columns=cols)

# 过滤数据，只保留created字段在date_from和date_until之间的数据
df['created'] = pd.to_datetime(df['created'])
filtered_df = df[(df['created'] >= date_from_dt) & (df['created'] <= date_until_dt)]

# # 将filtered_df中的created字段转换回原来的字符串格式
# filtered_df['created'] = filtered_df['created'].dt.strftime('%Y-%m-%d %H:%M:%S')

# 将过滤后的数据保存为JSON文件
filtered_df.to_json('second_arxiv_data_0101-0731.json', orient='records', lines=True, force_ascii=False)