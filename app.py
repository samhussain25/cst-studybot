import streamlit as st
import chromadb
import config
import json
import os
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="CST StudyBot", page_icon="🎓", layout="wide")

# --- LOAD RESOURCES ---
@st.cache_resource
def load_resources():
    chroma_client = chromadb.PersistentClient(path=config.DB_PATH)
    collection = chroma_client.get_collection(name="ia_questions")
    model = config.get_model()
    return collection, model

@st.cache_resource
def load_stats():
    """Loads all generated metadata_YYYY.json files into a lookup dictionary."""
    stats_db = {}
    report_dir = "." # Assuming json files are in the root
    
    # Look for metadata_2023.json, metadata_2022.json, etc.
    for f in os.listdir(report_dir):
        if f.startswith("metadata_") and f.endswith(".json"):
            try:
                year = int(re.search(r'\d{4}', f).group())
                with open(os.path.join(report_dir, f), 'r') as file:
                    data = json.load(file)
                    
                # Re-organize for fast lookup: stats_db[2023][1]["5"] = { ... }
                if year not in stats_db: stats_db[year] = {}
                
                for item in data:
                    p_num = item['paper']
                    q_num = str(item['question_number'])
                    
                    if p_num not in stats_db[year]: stats_db[year][p_num] = {}
                    stats_db[year][p_num][q_num] = item
            except Exception as e:
                print(f"Error loading {f}: {e}")
    return stats_db

try:
    collection, model = load_resources()
    stats_db = load_stats()
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Study Config")
    selected_topic = st.selectbox(
        "Filter by Topic",
        ["All Topics", "Foundations of Computer Science", "Discrete Mathematics", 
         "Digital Electronics", "Object-Oriented Programming", "Algorithms"]
    )

# --- MAIN UI ---
st.title("🎓 Cambridge Part IA StudyBot")
st.markdown("Search the archives. Real examiner data included.")

query = st.text_input("Search Query", placeholder="e.g., Karnaugh maps...")

if st.button("Find Questions", type="primary"):
    if not query:
        st.warning("Please enter a search term.")
    else:
        with st.spinner("Scanning archives..."):
            # 1. SEARCH DB
            where_clause = {"topic": selected_topic} if selected_topic != "All Topics" else {}
            results = collection.query(query_texts=[query], n_results=5) # , where=where_clause

            if not results['documents'][0]:
                st.error("No questions found.")
            else:
                # 2. PREPARE CONTEXT
                docs = results['documents'][0]
                metas = results['metadatas'][0]
                
                context = ""
                for i, doc in enumerate(docs[:3]):
                    m = metas[i]
                    context += f"\n--- CANDIDATE {i+1} ({m['year']} Paper {m['paper']}) ---\n{doc}\n"

                # 3. GEMINI PROMPT (Updated to extract Question Number)
                prompt = f"""
                You are an expert Tutor. 
                User Query: "{query}"
                
                Candidates:
                {context}
                
                TASK:
                1. Select the BEST question.
                2. Extract the Year, Paper, and Question Number (e.g. "5", "10", "3a").
                3. Format the question in Markdown/LaTeX.
                4. Write a Hint.

                OUTPUT FORMAT (Strict):
                [METADATA]
                Year: 20XX | Paper: X | Question: Y
                
                [QUESTION]
                (Markdown text)
                
                [HINT]
                (Hint text)
                """
                
                response = model.generate_content(prompt).text
                
                # 4. PARSE RESPONSE
                try:
                    parts = response.split("[QUESTION]")
                    meta_str = parts[0].replace("[METADATA]", "").strip()
                    
                    remaining = parts[1].split("[HINT]")
                    q_text = remaining[0].strip()
                    hint = remaining[1].strip()
                    
                    # Extract Year/Paper/Q from the string "Year: 2023 | Paper: 1 | Question: 5"
                    try:
                        m_year = int(re.search(r'Year:\s*(\d+)', meta_str).group(1))
                        m_paper = int(re.search(r'Paper:\s*(\d+)', meta_str).group(1))
                        m_qnum = re.search(r'Question:\s*([0-9a-zA-Z]+)', meta_str).group(1)
                    except:
                        m_year, m_paper, m_qnum = None, None, None

                    # -- UI DISPLAY --
                    st.subheader(f"📄 Selected Question (Year {m_year}, Q{m_qnum})")
                    st.markdown("---")
                    st.markdown(q_text)
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        with st.expander("🆘 Need a Hint?"):
                            st.info(hint)
                            
                    with col2:
                        with st.expander("🧐 Examiner's Stats"):
                        # 1. CLEANUP: Turn "4c" -> "4"
                            if m_qnum:
                                # Removes letters, leaves only numbers
                                clean_lookup_q = re.sub(r"[^0-9]", "", str(m_qnum))
                            else:
                                clean_lookup_q = "Unknown"

                            stat_found = False
                            
                            if m_year and m_paper:
                                y_data = stats_db.get(m_year, {})
                                paper_data = y_data.get(m_paper, {})
                                
                                # --- DEBUGGING: SHOW WHAT WE HAVE ---
                                if not paper_data:
                                    st.warning(f"No data found for {m_year} Paper {m_paper} in your JSON files.")
                                else:
                                    # This line shows you exactly what keys exist in the DB
                                    available_keys = sorted(list(paper_data.keys()), key=lambda x: int(x) if x.isdigit() else 0)
                                    st.caption(f"Available Questions for this paper: {', '.join(available_keys)}")

                                # 2. LOOKUP
                                # Try exact match (e.g. "4")
                                q_data = paper_data.get(clean_lookup_q)
                                
                                if q_data:
                                    st.markdown(f"**Difficulty:** {q_data.get('difficulty', '?')}/10")
                                    st.markdown(f"**Popularity:** {q_data.get('popularity', '?')}/10")
                                    st.info(f"⚠️ **Main Mistake:** {q_data.get('mistakes', 'No data')}")
                                    stat_found = True
                            
                            if not stat_found:
                                st.warning(f"Could not find stats for Q{clean_lookup_q}")
                                st.write("If you see the question number in the list above, the AI extracted it correctly but the lookup failed.")

                except Exception as e:
                    st.error(f"Parsing Error: {e}")
                    st.write(response)