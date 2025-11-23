import os
import requests
from bs4 import BeautifulSoup
import time
import config

# Configuration
BASE_URL = "https://www.cl.cam.ac.uk/teaching/exams/pastpapers/"
OUTPUT_DIR = "exam_papers"
YEAR_START = 2018  # Stick to recent years to avoid deprecated Java/ML syntax
YEAR_END = 2024

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists("reports"):
        os.makedirs("reports") # Place your manually downloaded reports here

def get_paper_urls():
    """Scrapes the main index page to find year-based links."""
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    paper_links = []
    
    # The CL website structure usually lists years. We iterate through expected patterns.
    # Pattern: yYYYYPAPERX.pdf
    for year in range(YEAR_START, YEAR_END + 1):
        # Part IA typically has Paper 1, Paper 2, Paper 3
        for paper_num in [1, 2, 3]:
            # Construct the likely URL (Cambridge formatting varies, this is the standard pattern)
            filename = f"y{year}PAPER{paper_num}.pdf"
            url = f"{BASE_URL}{filename}"
            paper_links.append((year, paper_num, url, filename))
            
    return paper_links

def download_papers(links):
    print(f"Found potential papers. Attempting download...")
    for year, paper_num, url, filename in links:
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(save_path):
            print(f"Skipping {filename} (already exists)")
            continue
            
        try:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✓ Downloaded: {filename}")
            else:
                print(f"✗ Failed (Status {r.status_code}): {url}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
        
        time.sleep(1) # Be polite to the CL server

if __name__ == "__main__":
    setup_directories()
    links = get_paper_urls()
    download_papers(links)
    print("\n[Action Required] Please manually download Examiners' Reports for these years and place them in the 'reports/' folder.")