import os
import fitz  # PyMuPDF
import json
import re
import config

model = config.get_model()

def extract_text_from_pdf(pdf_path):
    """Extracts text, but stops reading when it hits Part IB to save time."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        page_text = page.get_text()
        text += page_text
        
        # STOPPER: If we see the header for the next year group, stop reading.
        # Note: We check for variations like "Part IB" or "Computer Science Tripos Part IB"
        if "Part IB" in page_text and "Part IA" not in page_text:
            print("  -> Detected start of Part IB. Truncating text to save time...")
            break
            
    return text

def analyze_monolithic_report(year, report_text):
    print(f"Analyzing Full Report for {year} (Filtering for Part IA)...")

    # The prompt is now responsible for filtering out Part IB/II
    prompt = f"""
    You are an expert Data Analyst for Cambridge Computer Science.
    
    CONTEXT:
    The text below is the "Examiners' Report" for Year {year}. 
    It contains commentary for Part IA, Part IB, and Part II.
    
    TASK:
    1. LOCATE the sections specifically for "Part IA" (Papers 1, 2, and 3).
    2. IGNORE any text related to Part IB or Part II.
    3. For each Part IA question found, extract:
       - "paper": 1, 2, or 3.
       - "question_number": The question number (e.g., "1", "5", "10").
       - "topic": The subject (e.g., "Discrete Maths", "OCaml").
       - "difficulty": Integer 1-10 (10 = catastrophic failure rate).
       - "mistakes": A brief summary of why students lost marks.

    OUTPUT JSON ONLY (List of objects):
    [
      {{
        "paper": 1,
        "question_number": "1",
        "topic": "Foundations of CS",
        "difficulty": 4,
        "mistakes": "Students forgot the base case."
      }},
      ...
    ]
    
    REPORT TEXT:
    {report_text}
    """
    
    try:
        # We send the whole text. Gemini 1.5 Flash handles up to ~700 pages of text easily.
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        data = json.loads(response.text)
        
        print(f"  -> Found {len(data)} Part IA data points.")
        return data
    except Exception as e:
        print(f"  -> Error parsing report for {year}: {e}")
        return []

def save_metadata(year, data):
    """Saves the extracted wisdom to a file (or DB)"""
    filename = f"metadata_{year}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  -> Saved insights to {filename}")

if __name__ == "__main__":
    report_dir = "reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        print("Created 'reports/' folder. Place files like 'Report_2023.pdf' here.")
    
    for f in os.listdir(report_dir):
        if f.endswith(".pdf") and f.startswith("Report_"):
            try:
                # Expected filename: Report_2023.pdf
                year_str = re.search(r'\d{4}', f).group()
                year = int(year_str)
                
                full_path = os.path.join(report_dir, f)
                text = extract_text_from_pdf(full_path)
                
                # Run the analysis
                data = analyze_monolithic_report(year, text)
                
                if data:
                    save_metadata(year, data)
                    
            except Exception as e:
                print(f"Skipping {f}: {e}")