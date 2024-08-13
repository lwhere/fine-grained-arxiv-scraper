import xml.etree.ElementTree as ET
import requests
import time
import json
import os
from tqdm import tqdm
from datetime import datetime, timedelta

def fetch_arxiv_data(start_date, end_date, subjects):
    base_url = "http://export.arxiv.org/oai2"
    
    papers = []
    total_records = 0
    processed_records = 0
    
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    # Add one day to end_date to include papers from the end date
    end_date_param = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
    # Use the broader 'cs' category for the API request
    params = {
        "verb": "ListRecords",
        "metadataPrefix": "arXiv",
        "from": start_date.strftime("%Y-%m-%d"),
        "until": end_date_param,
        "set": "cs"  # Computer Science
    }
    
    print(f"Fetching papers for Computer Science from {start_date.date()} to {end_date.date()}")
    
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
                    created_date = datetime.strptime(metadata.find("{http://arxiv.org/OAI/arXiv/}created").text.strip(), "%Y-%m-%d")
                    categories = metadata.find("{http://arxiv.org/OAI/arXiv/}categories").text.strip().split()
                    
                    # Check if any of the paper's categories match our desired subjects
                    if start_date <= created_date <= end_date and any(subj in categories for subj in subjects):
                        paper = {
                            "title": metadata.find("{http://arxiv.org/OAI/arXiv/}title").text.strip(),
                            "authors": [author.text.strip() for author in metadata.findall("{http://arxiv.org/OAI/arXiv/}authors/{http://arxiv.org/OAI/arXiv/}author/{http://arxiv.org/OAI/arXiv/}name")],
                            "abstract": metadata.find("{http://arxiv.org/OAI/arXiv/}abstract").text.strip(),
                            "categories": categories,
                            "primary_category": categories[0],  # The first category is typically the primary one
                            "created": created_date.strftime("%Y-%m-%d"),
                            "doi": metadata.find("{http://arxiv.org/OAI/arXiv/}doi").text.strip() if metadata.find("{http://arxiv.org/OAI/arXiv/}doi") is not None else None,
                            "arxiv_id": metadata.find("{http://arxiv.org/OAI/arXiv/}id").text.strip()
                        }
                        papers.append(paper)
                        pbar.update(1)
                processed_records += 1
            
            pbar.total = total_records
            pbar.n = processed_records
            pbar.refresh()
            
            resumption_token = root.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken")
            if resumption_token is None or resumption_token.text is None:
                break
            
            params = {"verb": "ListRecords", "resumptionToken": resumption_token.text}
            
            time.sleep(2)
    
    print(f"\nFetched {len(papers)} papers within the specified date range and subjects out of {processed_records} total records")
    return papers

def save_to_jsonl(papers, filename):
    print(f"Saving {len(papers)} papers to {filename}")
    with open(filename, 'w', encoding='utf-8') as jsonl_file:
        for paper in papers:
            json.dump(paper, jsonl_file, ensure_ascii=False)
            jsonl_file.write('\n')
    print(f"Save completed")

def download_pdf(arxiv_id, output_folder, subject):
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    subject_folder = os.path.join(output_folder, subject)
    if not os.path.exists(subject_folder):
        os.makedirs(subject_folder)
    output_path = os.path.join(subject_folder, f"{arxiv_id}.pdf")
    
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        return True
    except requests.RequestException as e:
        print(f"Error downloading {arxiv_id}: {e}")
        return False

def main():
    start_date = "2024-08-01"
    end_date = "2024-08-02"
    subjects = ["cs.CV", "cs.AI"]  # Computer Vision and Artificial Intelligence
    output_folder = "arxiv_pdfs_fine_grained"
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    start_time = time.time()
    papers = fetch_arxiv_data(start_date, end_date, subjects)
    end_time = time.time()
    
    print(f"\nTime taken to fetch papers: {end_time - start_time:.2f} seconds")
    
    filename = f'arxiv_{"_".join(subjects)}_{start_date}_to_{end_date}.jsonl'
    save_to_jsonl(papers, filename)
    
    print(f"\nDownloading PDFs for {len(papers)} papers")
    successful_downloads = 0
    with tqdm(total=len(papers), desc="Downloading PDFs", unit="pdf") as pbar:
        for paper in papers:
            if download_pdf(paper['arxiv_id'], output_folder, paper['primary_category']):
                successful_downloads += 1
            pbar.update(1)
            time.sleep(1)  # Be nice to the arXiv servers
    
    print(f"\nSuccessfully downloaded {successful_downloads} out of {len(papers)} PDFs")
    print(f"\nTotal papers fetched and saved: {len(papers)}")

if __name__ == "__main__":
    main()
