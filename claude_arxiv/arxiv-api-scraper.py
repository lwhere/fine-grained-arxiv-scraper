import xml.etree.ElementTree as ET
import requests
import time
from datetime import datetime, timedelta
import csv

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
    while True:
        response = requests.get(base_url, params=params)
        root = ET.fromstring(response.content)
        
        for record in root.findall(".//{http://www.openarchives.org/OAI/2.0/}record"):
            metadata = record.find(".//{http://arxiv.org/OAI/arXiv/}arXiv")
            if metadata is not None:
                paper = {
                    "title": metadata.find("{http://arxiv.org/OAI/arXiv/}title").text.strip(),
                    "authors": "; ".join([author.text.strip() for author in metadata.findall("{http://arxiv.org/OAI/arXiv/}authors/{http://arxiv.org/OAI/arXiv/}author/{http://arxiv.org/OAI/arXiv/}name")]),
                    "abstract": metadata.find("{http://arxiv.org/OAI/arXiv/}abstract").text.strip(),
                    "categories": metadata.find("{http://arxiv.org/OAI/arXiv/}categories").text.strip(),
                    "created": metadata.find("{http://arxiv.org/OAI/arXiv/}created").text.strip()
                }
                papers.append(paper)
        
        # Check if there are more results
        resumption_token = root.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken")
        if resumption_token is None or resumption_token.text is None:
            break
        
        # Update params for the next request
        params = {"verb": "ListRecords", "resumptionToken": resumption_token.text}
        
        # Be nice to the API
        time.sleep(2)
    
    return papers

def save_to_csv(papers, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'authors', 'abstract', 'categories', 'created']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for paper in papers:
            writer.writerow(paper)

def main():
    # Example usage
    start_date = "2024-08-01"
    end_date = "2024-08-02"
    subject = "cs"  # For computer science
    
    papers = fetch_arxiv_data(start_date, end_date, subject)
    save_to_csv(papers, 'arxiv_papers_api.csv')
    print(f"Total papers fetched: {len(papers)}")

if __name__ == "__main__":
    main()
