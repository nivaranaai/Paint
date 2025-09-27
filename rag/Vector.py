# This script demonstrates a hybrid Retrieval-Augmented Generation (RAG) pipeline
# using a local Sentence Transformer for embeddings and the Gemini API for text generation.

import os
from dotenv import load_dotenv
import requests
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# --- Setup and Configuration ---
# Load environment variables from a .env file (e.g., GEMINI_API_KEY="your_api_key")
load_dotenv()

# Set your Gemini API key from the environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set the environment variable.")

# --- Document Processing Functions ---

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

def get_vector_store(chunks):
    """
    Creates a Chroma vector store from document chunks using a Sentence Transformer model.
    """
    print("Creating vector store...")
    # Use a local Hugging Face model for embeddings
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    vector_store = Chroma.from_documents(chunks, embeddings)
    print("Vector store created successfully.")
    return vector_store

def retrieve_relevant_chunks(vector_store, query, k=4):
    """
    Retrieves the most relevant chunks from the vector store based on a query.
    """
    print("Retrieving relevant document chunks...")
    docs = vector_store.similarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in docs])
    print("Relevant chunks retrieved.")
    return context

# --- Gemini API Function for Answer Generation ---

def generate_answer_with_gemini(query, context, model_name="gemini-2.5-flash-preview-05-20"):
    """
    Generates a response using the Gemini API, grounded by the retrieved context.
    """
    print(f"Generating answer with Gemini model: {model_name}...")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

    system_prompt = "You are a helpful assistant. Use the provided context to answer the user's question. If the information is not in the context, say 'I cannot answer based on the provided information.'"
    
    payload = {
        "contents": [
            {
                "parts": [{"text": f"Context: {context}\n\nQuestion: {query}"}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']
        
        print("Answer generated successfully.")
        return answer

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return "An error occurred while communicating with the Gemini API."

# --- Main RAG Pipeline Execution ---

def main():
    """
    Main function to run the RAG pipeline.
    """
    # Replace with the path to your document file
    cwd = os.getcwd()
    print("Current Working Directory:", cwd)
    pdf_file_path = "./paint_project/Vector_DB/1.pdf" # Make sure this file exists in the same directory.
    
    # 1. Load and process the document
    chunks = load_and_split_documents(pdf_file_path)
    
    # 2. Create the vector store
    vector_store = get_vector_store(chunks)
    
    # 3. Define the user query
    user_query = "how many words are there in the document and you need to replace the sentences on the first page to plural rathaer than singular."
    
    # 4. Retrieve context from the vector store
    context = retrieve_relevant_chunks(vector_store, user_query)
    
    # 5. Generate the final answer using the Gemini API
    final_answer = generate_answer_with_gemini(user_query, context)
    
    print("\n--- RAG Pipeline Results ---")
    print(f"User Query: {user_query}")
    print("\nGenerated Answer:")
    print(final_answer)

if __name__ == "__main__":
    main()
