import xml.etree.ElementTree as ET
import requests
import time
import json
from tqdm import tqdm

def fetch_arxiv_data(start_date, end_date, subject):
    base_url = "http://export.arxiv.org/oai2"
    
    params = {
        "verb": "ListRecords",
        "metadataPrefix": "arXiv",
        "from": start_date,
        "until": end_date,
        "set": f"{subject}"
    }
    
    papers = []
    total_records = 0
    processed_records = 0
    
    print(f"Fetching papers for {subject} from {start_date} to {end_date}")
    
    with tqdm(total=None, desc="Fetching papers", unit="paper") as pbar:
        while True:
            response = requests.get(base_url, params=params)
            root = ET.fromstring(response.content)
            
            if total_records == 0:
                total_records_elem = root.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken[@completeListSize]")
                if total_records_elem is not None:
                    total_records = int(total_records_elem.attrib['completeListSize'])
                    pbar.total = total_records
                    pbar.refresh()
            
            records = root.findall(".//{http://www.openarchives.org/OAI/2.0/}record")
            for record in records:
                metadata = record.find(".//{http://arxiv.org/OAI/arXiv/}arXiv")
                if metadata is not None:
                    paper = {
                        "title": metadata.find("{http://arxiv.org/OAI/arXiv/}title").text.strip(),
                        "authors": [author.text.strip() for author in metadata.findall("{http://arxiv.org/OAI/arXiv/}authors/{http://arxiv.org/OAI/arXiv/}author/{http://arxiv.org/OAI/arXiv/}name")],
                        "abstract": metadata.find("{http://arxiv.org/OAI/arXiv/}abstract").text.strip(),
                        "categories": metadata.find("{http://arxiv.org/OAI/arXiv/}categories").text.strip(),
                        "created": metadata.find("{http://arxiv.org/OAI/arXiv/}created").text.strip(),
                        "doi": metadata.find("{http://arxiv.org/OAI/arXiv/}doi").text.strip() if metadata.find("{http://arxiv.org/OAI/arXiv/}doi") is not None else None,
                        "arxiv_id": metadata.find("{http://arxiv.org/OAI/arXiv/}id").text.strip()
                    }
                    papers.append(paper)
                    processed_records += 1
                    pbar.update(1)
            
            resumption_token = root.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken")
            if resumption_token is None or resumption_token.text is None:
                break
            
            params = {"verb": "ListRecords", "resumptionToken": resumption_token.text}
            
            time.sleep(2)
    
    print(f"\nFetched {processed_records} papers out of {total_records} total records")
    return papers

def save_to_jsonl(papers, filename):
    print(f"Saving {len(papers)} papers to {filename}")
    with open(filename, 'w', encoding='utf-8') as jsonl_file:
        for paper in papers:
            json.dump(paper, jsonl_file, ensure_ascii=False)
            jsonl_file.write('\n')
    print(f"Save completed")

def main():
    start_date = "2024-08-01"
    end_date = "2024-08-02"
    subject = "cs"  # For computer science
    
    start_time = time.time()
    papers = fetch_arxiv_data(start_date, end_date, subject)
    end_time = time.time()
    
    print(f"\nTime taken to fetch papers: {end_time - start_time:.2f} seconds")
    
    filename = f'arxiv_{subject}_{start_date}_to_{end_date}.jsonl'
    save_to_jsonl(papers, filename)
    
    print(f"\nTotal papers fetched and saved: {len(papers)}")

if __name__ == "__main__":
    main()
