import chromadb
import config

model = config.get_model()
chroma_client = chromadb.PersistentClient(path=config.DB_PATH)
collection = chroma_client.get_collection(name="ia_questions")

def query_studybot(user_query, topic_filter=None):
    where_clause = {}
    if topic_filter:
        where_clause = {"topic": topic_filter}
        
    results = collection.query(
        query_texts=[user_query],
        n_results=3,
        # where=where_clause
    )
    
    if not results['documents'][0]:
        return "No results found."

    retrieved_data = results['documents'][0]
    metadatas = results['metadatas'][0]
    
    context_text = ""
    for i, q_text in enumerate(retrieved_data):
        meta = metadatas[i]
        context_text += f"\n--- QUESTION ({meta['year']} Paper {meta['paper']}) ---\n{q_text}\n"

    final_prompt = f"""
    Context: Cambridge Computer Science Part IA.
    Query: "{user_query}"
    
    Relevant Questions:
    {context_text}
    
    Task:
    1. Identify the most relevant question from the list.
    2. Present the question using Markdown/LaTeX.
    3. Explain relevance to the query.
    4. Provide a conceptual hint.
    """
    
    response = model.generate_content(final_prompt)
    return response.text

if __name__ == "__main__":
    q = input("Search query: ")
    answer = query_studybot(q)
    print("\n" + answer)