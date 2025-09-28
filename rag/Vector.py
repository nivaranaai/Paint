import os
import pinecone
import PyPDF2
import requests
from sentence_transformers import SentenceTransformer

# Gemini API setup
GEMINI_API_KEY = "AIzaSyBoaHFZHWCJG4xMkVzfKTxqGZ_ybXRKH8A"
GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=" + GEMINI_API_KEY

model = SentenceTransformer('all-MiniLM-L6-v2')


def get_gemini_embedding(text):
    embedding = model.encode(text).tolist()
    return embedding

# Initialize Pinecone (new style)
pc = pinecone.Pinecone(api_key="pcsk_cg1dn_Qx2V8L2voCnGvGMBHKVXD8nAFUEPxpJVzuh1uPUH7jXL4r6jNpNkX2NCXsAAMmH")
index_name = "house-color-prediction-demo1"
if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=384,  # all-MiniLM-L6-v2 outputs 384-dimensional vectors
        metric="cosine",
        spec=pinecone.ServerlessSpec(
            cloud="aws",  # or "gcp" if using Google Cloud
            region="us-east-1"  # match your Pinecone project region
        )
    )

index = pc.Index(index_name)

# Differentiating factors as context
differentiators = """
Architectural Style, Geographic Location and Climate, Natural Light Exposure,
User's Personal Style and Psychology, HOA and Neighborhood Guidelines
"""

def extract_text_from_pdf(pdf_path):
    text = ""
    print("pdf_path",pdf_path)
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def chunk_text(text, chunk_size=500):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def query_pinecone(question, differentiators, top_k=3):
    """
    Query Pinecone for similar documents based on the input question
    
    Args:
        question (str): The question to search for
        differentiators (str): The context/differentiators to add to the query
        top_k (int): Number of results to return
        
    Returns:
        list: List of matching documents with scores and metadata
    """
    # Combine differentiators with the question
    full_query = differentiators + "\n" + question
    
    # Get embedding for the query
    query_embedding = get_gemini_embedding(full_query)
    
    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # Format results
    matches = []
    for match in results.matches:
        matches.append({
            'id': match.id,
            'score': match.score,
            'text': match.metadata.get('text', ''),
            'source': match.metadata.get('pdf_path', 'unknown'),
            'chunk_id': match.metadata.get('chunk_id', -1)
        })
    
    return matches

def upsert_pdf_to_pinecone(pdf_path, differentiators):
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    print("chunks",chunks)
    for i, chunk in enumerate(chunks):
        context = differentiators + "\n" + chunk
        embedding = get_gemini_embedding(context)
        meta = {
            "pdf_path": pdf_path,
            "chunk_id": i,
            "differentiators": differentiators
        }
        print("meta",meta)
        index.upsert([(f"{os.path.basename(pdf_path)}_{i}", embedding, meta)])

def retrieve_relevant_chunks(question, differentiators, top_k=3):
    """
    Retrieves the most relevant chunks from Pinecone based on the input question.
    
    Args:
        question (str): The question to search for.
        differentiators (str): Context/differentiators to add to the query.
        top_k (int): Number of results to return.
        
    Returns:
        list: List of matching document texts.
    """
    matches = query_pinecone(question, differentiators, top_k=top_k)
    results = []
    for match in matches:
        results.append({
            "text": match["text"],
            "score": match["score"],
            "source": match["source"],
            "chunk_id": match["chunk_id"]
        })
    return results

# Example usage:
if __name__ == "__main__":
    pdf_folder = "C:\\Users\\HP\\Desktop\\Delete"
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.lower().endswith(".pdf"):
            upsert_pdf_to_pinecone(os.path.join(pdf_folder, pdf_file), differentiators)
    print("PDFs processed and upserted to Pinecone vector DB.")

    while True:
        question = input("Enter your paint-related question (or type 'exit' to quit): ")
        if question.strip().lower() == "exit":
            print("Exiting.")
            break
        results = retrieve_relevant_chunks(question, differentiators, top_k=3)
        if not results:
            print("No relevant information found.\n" + "-"*40)
        else:
            for idx, res in enumerate(results, 1):
                print(f"Result {idx}:")
                print(f"Score: {res['score']}")
                print(f"Source: {res['source']} (Chunk {res['chunk_id']})")
                print(f"Text: {res['text']}\n{'-'*40}")