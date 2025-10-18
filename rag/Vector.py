import os
from pinecone import Pinecone
from langchain.document_loaders import PyPDFLoader
import requests
import json
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Gemini API setup
GEMINI_API_KEY = "AIzaSyBoaHFZHWCJG4xMkVzfKTxqGZ_ybXRKH8A"
GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=" + GEMINI_API_KEY

model = SentenceTransformer('all-MiniLM-L6-v2')


def get_gemini_embedding(text):
    embedding = model.encode(text).tolist()
    return embedding

# Initialize Pinecone (new style)
pc = Pinecone(api_key="pcsk_UCz7B_SzsJLZUbzTnK9g6T72yLpTxPZYoJNLzY2WTNBMNoAQr5hxsQaxVSQ6Ev82pgGMw")
index_name = "house-color-prediction-demo1"
from pinecone import ServerlessSpec
if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=384,  # all-MiniLM-L6-v2 outputs 384-dimensional vectors
        metric="cosine",
        spec=ServerlessSpec(
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

def load_and_split_documents(file_path, chunk_size=1000, chunk_overlap=200):
    """
    Loads a PDF document and splits it into chunks.
    """
    print("Loading and splitting document...")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Document split into {len(chunks)} chunks.")
    return chunks

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
    full_query = question
    
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
    print(f"Pinecone query completed. Found {len(matches)} matches")
    return matches

def upsert_pdf_to_pinecone(pdf_path, differentiators):
    import tempfile
    import boto3
    from urllib.parse import urlparse
    
    # Check if it's an S3 path
    if pdf_path.startswith('s3://'):
        # Parse S3 URL
        parsed = urlparse(pdf_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        # Download from S3 to temp file
        s3 = boto3.client('s3')
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            s3.download_file(bucket, key, temp_file.name)
            local_path = temp_file.name
    else:
        local_path = pdf_path
    
    try:
        chunks = load_and_split_documents(local_path, chunk_size=500, chunk_overlap=50)
        print(f"Found {len(chunks)} chunks")
        
        vectors = []
        for i, chunk in enumerate(chunks):
            if not chunk.page_content.strip():
                continue
                
            embedding = get_gemini_embedding(chunk.page_content.strip())
            vectors.append({
                "id": f"{os.path.basename(pdf_path)}_{i}",
                "values": embedding,
                "metadata": {
                    "text": chunk.page_content.strip(),
                    "pdf_path": os.path.basename(pdf_path),
                    "chunk_id": i
                }
            })
        
        if vectors:
            result = index.upsert(vectors=vectors)
            print(f"✅ Stored {result['upserted_count']} chunks from {os.path.basename(pdf_path)}")
    finally:
        # Clean up temp file if S3 was used
        if pdf_path.startswith('s3://') and os.path.exists(local_path):
            os.unlink(local_path)

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
    print("question:", question);
    results = []
    for match in matches:
        results.append({
            "text": match["text"],
            "score": match["score"],
            "source": match["source"],
            "chunk_id": match["chunk_id"]
        })
    return results

def generate_answer_with_gemini(query, context, model_name="gemini-2.5-flash-preview-05-20"):
    import json
    import time
    
    GEMINI_API_KEY = ""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [{"text": f"Context: {context}\n\nQuestion: {query}"}]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    for attempt in range(3):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            answer = result['candidates'][0]['content']['parts'][0]['text']
            return answer

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                return f"API unavailable. Context summary: {str(context)[:200]}..."

# Example usage:
"""if __name__ == "__main__":
    pdf_folder = "C:\\Users\\HP\\Desktop\\Delete"
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.lower().endswith(".pdf"):
            upsert_pdf_to_pinecone(os.path.join(pdf_folder, pdf_file), differentiators)
    print("PDFs processed and upserted to Pinecone vector DB.")"""

def generate_answer_based_on_user_query(query):
    question = input("Enter your paint-related question (or type 'exit' to quit): ")
    user_query = "What would be the preference for Tropical climate?"
    context = retrieve_relevant_chunks(query, differentiators, top_k=3)
    final_answer = generate_answer_with_gemini(user_query, context)
    print(final_answer)
