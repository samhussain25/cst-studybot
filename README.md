# CST StudyBot

**CST StudyBot** is an AI-powered revision assistant for the Cambridge Computer Science Tripos (Part IA). It uses **Google Gemini 2.5 Flash** and **RAG (Retrieval Augmented Generation)** to let you search, practice, and analyze past exam questions with examiner insights.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange)

## Features

* **Smart Search:** Query questions by concept (e.g., "Ocaml list recursion" or "Karnaugh maps").
* **Vision Ingestion:** Automatically parses PDF exam papers, preserving LaTeX math and code blocks.
* **Examiner Insights:** Integrates data from Examiners' Reports to show difficulty ratings and common student mistakes.
* **Interactive UI:** A clean Streamlit dashboard to render questions and hide/show AI-generated hints.

## Tech Stack

* **AI Model:** Google Gemini 2.5 Flash (via `google-generativeai`)
* **Vector DB:** ChromaDB (Local)
* **Frontend:** Streamlit
* **PDF Parsing:** PyMuPDF (`fitz`) & Gemini Vision

## Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/cst-studybot.git](https://github.com/YOUR_USERNAME/cst-studybot.git)
cd cst-studybot
```
### 2. Install Dependencies

It is recommended to use a virtual environment.
Bash
```
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install libraries
pip install -r requirements.txt
```

### 3. Configure API Key
1.  Get a free API Key from Google AI Studio.
2.  Rename the template config file:
    ```bash
    mv config_example.py config.py
    ```
3.  Open `config.py` and paste your API key:
    ```python
    API_KEY = "YOUR_ACTUAL_KEY_HERE"
    ```

---

## Building the Database (The Pipeline)

Since Cambridge Examiners' Reports are protected by Raven login, you must do **Step 2** manually.

### Step 1: Scrape Question Papers
Downloads the public PDF past papers from the CL website.
```bash
python scraper.py
```

Step 2: Add Examiners' Reports (Manual)

    Log in to the Computer Science Past Exams page.

    Download the Examiners' Reports (PDFs) for the years you want (e.g., 2021-2024).

    Rename them to Report_YYYY.pdf (e.g., Report_2023.pdf).

    Place them inside a new folder named reports/.

Step 3: Ingest Questions

Uses AI Vision to read the exam papers and store them in ChromaDB.
Bash

python ingest.py

Step 4: Analyze Metadata

Reads the Examiners' Reports to extract difficulty scores and common mistakes.
Bash

python analyze_reports.py

Usage

Once the pipeline is complete, launch the web interface:
Bash

streamlit run app.py

This will open the StudyBot in your browser at http://localhost:8501.

## Project Structure

```text
cst-studybot/
├── app.py                 # The Main Streamlit UI
├── ingest.py              # Vision pipeline for Question Papers
├── analyze_reports.py     # Text pipeline for Examiners' Reports
├── scraper.py             # Downloader for public PDFs
├── query_bot.py           # CLI version of the search (for testing)
├── config.py              # API Keys (Ignored by Git)
├── requirements.txt       # Python dependencies
├── cst_db/                # Local Vector Database (Generated)
└── exam_papers/           # PDF Storage (Generated)
```

Disclaimer

This is an unofficial student project. It is not affiliated with the University of Cambridge or the Computer Lab. Please respect the University's copyright on exam materials.
