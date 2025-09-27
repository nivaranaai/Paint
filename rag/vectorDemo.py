import os
import pinecone
import PyPDF2
import requests

# Gemini API setup
GEMINI_API_KEY = ""
GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=" + GEMINI_API_KEY

def get_gemini_embedding(text):
    payload = {
        "model": "models/embedding-001",
        "content": {"parts": [{"text": text}]}
    }
    response = requests.post(GEMINI_EMBED_URL, json=payload)
    response.raise_for_status()
    embedding = response.json()["embedding"]["values"]
    return embedding

# Initialize Pinecone (new style)
pc = pinecone.Pinecone(api_key="")
index_name = "house-color-prediction"
if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=pinecone.ServerlessSpec(
            cloud="aws",  # or "gcp" if using Google Cloud
            region="us-east-1"  # match your Pinecone project region
        )
    )

# Specify your Pinecone index host (find this in your Pinecone console)
PINECONE_HOST = "https://paint-rag-9pgzq2d.svc.aped-4627-b74a.pinecone.io"
index = pc.Index(index_name, host=PINECONE_HOST)

# Differentiating factors as context
differentiators = """
Architectural Style, Geographic Location and Climate, Natural Light Exposure,
User's Personal Style and Psychology, HOA and Neighborhood Guidelines
"""

def extract_text_from_pdf(pdf_path):
    text = ""
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

def upsert_pdf_to_pinecone(pdf_path, differentiators):
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        context = differentiators + "\n" + chunk
        embedding = get_gemini_embedding(context)
        meta = {
            "pdf_path": pdf_path,
            "chunk_id": i,
            "differentiators": differentiators
        }
        index.upsert([(f"{os.path.basename(pdf_path)}_{i}", embedding, meta)])

if __name__ == "__main__":
    pdf_folder = "C:\\Users\\HP\\Documents\\Paint\\Sample"
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.lower().endswith(".pdf"):
            upsert_pdf_to_pinecone(os.path.join(pdf_folder, pdf_file), differentiators)
    print("PDFs processed and upserted to Pinecone vector DB.")