import xml.etree.ElementTree as ET
import requests
import time
import json
import os
import shutil
from tqdm import tqdm
from datetime import datetime, timedelta
import argparse

def fetch_arxiv_data(start_date, end_date, subject):
    base_url = "http://export.arxiv.org/oai2"
    
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    end_date_param = (end_date + timedelta(days=2)).strftime("%Y-%m-%d")
    
    params = {
        "verb": "ListRecords",
        "metadataPrefix": "arXiv",
        "from": start_date.strftime("%Y-%m-%d"),
        "until": end_date_param,
        "set": f"{subject}"
    }
    
    papers = []
    total_records = 0
    processed_records = 0
    filtered_records = 0
    
    print(f"Fetching papers for {subject} from {start_date.date()} to {end_date.date()}")
    
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
                    if start_date <= created_date <= end_date:
                        paper = {
                            "title": metadata.find("{http://arxiv.org/OAI/arXiv/}title").text.strip(),
                            "authors": [author.text.strip() for author in metadata.findall("{http://arxiv.org/OAI/arXiv/}authors/{http://arxiv.org/OAI/arXiv/}author/{http://arxiv.org/OAI/arXiv/}name")],
                            "abstract": metadata.find("{http://arxiv.org/OAI/arXiv/}abstract").text.strip(),
                            "categories": metadata.find("{http://arxiv.org/OAI/arXiv/}categories").text.strip(),
                            "created": created_date.strftime("%Y-%m-%d"),
                            "doi": metadata.find("{http://arxiv.org/OAI/arXiv/}doi").text.strip() if metadata.find("{http://arxiv.org/OAI/arXiv/}doi") is not None else None,
                            "arxiv_id": metadata.find("{http://arxiv.org/OAI/arXiv/}id").text.strip()
                        }
                        papers.append(paper)
                        filtered_records += 1
                        pbar.update(1)
                processed_records += 1
            
            resumption_token = root.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken")
            if resumption_token is None or resumption_token.text is None:
                break
            
            params = {"verb": "ListRecords", "resumptionToken": resumption_token.text}
            
            time.sleep(2)
    
    print(f"\nFetched {filtered_records} papers within the specified date range out of {processed_records} total records")
    return papers

def save_to_jsonl(papers, filename):
    print(f"Saving {len(papers)} papers to {filename}")
    with open(filename, 'w', encoding='utf-8') as jsonl_file:
        for paper in papers:
            json.dump(paper, jsonl_file, ensure_ascii=False)
            jsonl_file.write('\n')
    print(f"Save completed")

def download_pdf(arxiv_id, output_folder):
    output_path = os.path.join(output_folder, f"{arxiv_id}.pdf")

    # 检查文件是否已存在
    if os.path.exists(output_path):
        return True, True  # 文件存在，表示使用了缓存

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        return True, False  # 下载成功，但不是使用缓存
    except requests.RequestException as e:
        print(f"Error downloading {arxiv_id}: {e}")
        return False, False  # 下载失败，不是使用缓存

def organize_pdfs_by_category(papers, base_folder):
    print("\nOrganizing PDFs by category...")
    for paper in tqdm(papers, desc="Organizing PDFs", unit="paper"):
        arxiv_id = paper['arxiv_id']
        categories = paper['categories'].split()
        source_file = os.path.join(base_folder, f"{arxiv_id}.pdf")
        
        if not os.path.exists(source_file):
            print(f"Warning: PDF for {arxiv_id} not found. Skipping.")
            continue
        
        for category in categories:
            category_folder = os.path.join(base_folder, category)
            if not os.path.exists(category_folder):
                os.makedirs(category_folder)
            
            dest_file = os.path.join(category_folder, f"{arxiv_id}.pdf")
            shutil.copy2(source_file, dest_file)
    
    print("PDF organization completed.")

def main(args):
    start_date = args.start_date
    end_date = args.end_date
    subject = args.subject  # For computer science
    
    # Create output folder with date range
    output_folder = f"arxiv_pdfs_{start_date}_to_{end_date}"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    start_time = time.time()
    papers = fetch_arxiv_data(start_date, end_date, subject)
    
    # save papers' info
    # TODO
    
    end_time = time.time()
    
    print(f"\nTime taken to fetch papers: {end_time - start_time:.2f} seconds")
    
    # Save metadata to JSONL file
    filename = f'arxiv_{subject}_{start_date}_to_{end_date}.jsonl'
    save_to_jsonl(papers, filename)
    
    # Download PDFs
    print(f"\nDownloading PDFs for {len(papers)} papers")
    successful_downloads = 0
    cached_downloads = 0
    with tqdm(total=len(papers), desc="Downloading PDFs", unit="pdf") as pbar:
        for paper in papers:
            success, used_cache = download_pdf(paper['arxiv_id'], output_folder)
            if success:
                successful_downloads += 1
                if used_cache:
                    cached_downloads += 1
            pbar.update(1)
            if not used_cache:
                time.sleep(1)  # Be nice to the arXiv servers, but only if we actually downloaded
    
    print(f"\nSuccessfully downloaded or found {successful_downloads} out of {len(papers)} PDFs")
    print(f"Used existing files for {cached_downloads} PDFs")
    
    # Organize PDFs by category
    organize_pdfs_by_category(papers, output_folder)
    
    print(f"\nTotal papers fetched and saved: {len(papers)}")
    print(f"PDFs saved in folder: {output_folder}")
    print("PDFs have been organized into category subfolders within the main folder.")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Pdfs download.')
    parser.add_argument('--start_date', type=str, default="2024-08-02",
                        help='Start date.')
    parser.add_argument('--end_date', type=str, default="2024-08-04",
                        help='End date.')
    parser.add_argument('--subject', type=str, default="cs",
                        help='Subject.')

    args = parser.parse_args()
    main(args)
