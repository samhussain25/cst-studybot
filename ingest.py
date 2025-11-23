import os
import fitz  # PyMuPDF
import chromadb
from PIL import Image
import io
import config
import concurrent.futures
from tqdm import tqdm  # Progress bar
import time

# Initialize
model = config.get_model()
chroma_client = chromadb.PersistentClient(path=config.DB_PATH)
collection = chroma_client.get_or_create_collection(name="ia_questions")

VISION_PROMPT = """
Analyze this exam page.
1. Identify distinct Question content.
2. Transcribe text to Markdown (LaTeX for math $...$, Code Blocks for code).
3. Classify Syllabus Topic.
4. Output JSON: {"topic": "...", "content": "...", "question_id": "..."}
"""

def parse_pdf_page_as_image(pdf_path, page_num):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    # Lower DPI to 100 to speed up upload (still readable for AI)
    pix = page.get_pixmap(dpi=100) 
    img_data = pix.tobytes("png")
    return Image.open(io.BytesIO(img_data))

def process_single_page(args):
    """Helper function for parallel processing"""
    pdf_path, pdf_filename, page_num, year, paper = args
    
    page_id = f"{year}_P{paper}_Pg{page_num}"
    
    # 1. SKIP if already exists (Crucial for restarting)
    existing = collection.get(ids=[page_id])
    if existing['ids']:
        return "Skipped"

    try:
        # 2. Vision AI Call
        image = parse_pdf_page_as_image(pdf_path, page_num)
        response = model.generate_content([VISION_PROMPT, image])
        extracted_text = response.text
        
        # 3. Save to DB
        collection.add(
            documents=[extracted_text],
            metadatas=[{
                "year": year, 
                "paper": paper, 
                "topic": "General", # Simplified for speed
                "source": pdf_filename,
                "page": page_num
            }],
            ids=[page_id]
        )
        return "Processed"
    except Exception as e:
        # If rate limit hit (429), wait and retry once
        if "429" in str(e):
            time.sleep(10)
            return "RateLimited"
        return f"Error: {e}"

def ingest_all_parallel():
    if not os.path.exists("exam_papers"):
        print("No 'exam_papers' folder found.")
        return

    tasks = []
    papers = [f for f in os.listdir("exam_papers") if f.endswith(".pdf")]
    
    print(f"Preparing to ingest {len(papers)} papers...")

    # 1. Build the Task List
    for pdf_filename in papers:
        try:
            year = int(pdf_filename[1:5])
            paper = int(pdf_filename[10:11])
            path = os.path.join("exam_papers", pdf_filename)
            doc = fitz.open(path)
            
            # Skip cover pages (0 and 1)
            for page_num in range(2, len(doc)):
                tasks.append((path, pdf_filename, page_num, year, paper))
        except:
            continue

    # 2. Run in Parallel (Max 4 workers to stay under Rate Limit)
    print(f"Processing {len(tasks)} pages in parallel...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Wrap with tqdm for a progress bar
        results = list(tqdm(executor.map(process_single_page, tasks), total=len(tasks)))

    print(f"\nDone! Processed: {results.count('Processed')}, Skipped: {results.count('Skipped')}")

if __name__ == "__main__":
    ingest_all_parallel()