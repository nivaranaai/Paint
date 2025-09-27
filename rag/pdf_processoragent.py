import os
import typer
import sys
from pathlib import Path
from typing import Optional, List, Union
from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()

# --- Check for core dependencies before import ---
try:
    from phi.assistant import Assistant
    from phi.document import Document
    from phi.knowledge.pdf import PDFReader
    from phi.vectordb.pgvector import PgVector2
    from phi.embedder.openai import OpenAIEmbedder
except ImportError as e:
    typer.echo(f"Error: Missing core library. Please install 'phidata[full]' and 'typer'.", err=True)
    typer.echo(f"Details: {e}", err=True)
    typer.echo("Hint: Run 'pip install 'phidata[full]' typer'", err=True)
    typer.Exit(code=1)

# Check for the psycopg library, a prerequisite for PgVector2
try:
    import psycopg
except ImportError as e:
    typer.echo(f"Error: Missing required library. Please install the necessary packages.", err=True)
    typer.echo(f"Details: {e}", err=True)
    typer.echo("Hint: Run 'pip install psycopg'", err=True)
    typer.Exit(code=1)

# Database configuration
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    typer.echo("Error: 'DATABASE_URL' not found in .env file or environment variables.", err=True)
    typer.Exit(code=1)

# Embedder configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
embedder = None
if not OPENAI_API_KEY:
    typer.echo("Warning: 'OPENAI_API_KEY' not found. Attempting to use Ollama as the embedder.", err=True)
    try:
        from phi.embedder.ollama import OllamaEmbedder
        # Initialize OllamaEmbedder, which requires the 'ollama' Python package
        embedder = OllamaEmbedder(model="nomic-embed-text")
    except ImportError as e:
        typer.echo(f"Error: Failed to import OllamaEmbedder. Please install the 'ollama' Python library.", err=True)
        typer.echo(f"Details: {e}", err=True)
        typer.echo("Hint: Run 'pip install ollama'", err=True)
        typer.Exit(code=1)
else:
    embedder = OpenAIEmbedder(model="text-embedding-3-small")

class PDFProcessor:
    def __init__(self, db_url: str = DB_URL):
        """Initialize the PDF processor with a vector database connection."""
        self.db_url = db_url
        self.vector_db = PgVector2(
            db_url=db_url,
            collection="pdf_documents",
            embedder=embedder,
        )
        self.pdf_reader = PDFReader()

    def process_pdf(self) -> bool:
        """Process a PDF file and store its content in the vector database.
        
        Returns:
            bool: True if processing was successful, False otherwise
        """
        # Hardcoded PDF file path
        pdf_path = "C:\\Users\\HP\\Documents\\Paint\\Sample"
        typer.echo(f"Starting to process PDF from: {pdf_path}")
        try:
            # Read the PDF file
            documents = self.pdf_reader.read(pdf_path)
            
            if not documents:
                typer.echo(f"No content found in {pdf_path}")
                return False
                
            # Store the documents in the vector database
            self.vector_db.insert(documents=documents)
            typer.echo(f"Successfully processed and stored {len(documents)} chunks from {pdf_path}")
            return True
            
        except Exception as e:
            typer.echo(f"Error processing {pdf_path}: {str(e)}", err=True)
            return False

    def search_documents(self, query: str, limit: int = 5) -> List[Document]:
        """Search for documents in the vector database.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        typer.echo(f"Searching for query: '{query}'")
        try:
            results = self.vector_db.search(query=query, limit=limit)
            return results
        except Exception as e:
            typer.echo(f"Error searching documents: {str(e)}", err=True)
            return []

# Command Line Interface
app = typer.Typer(help="PDF Processor CLI")

@app.command()
def process():
    """Process a PDF file and store its content in the vector database."""
    processor = PDFProcessor()
    success = processor.process_pdf()
    if success:
        typer.echo("PDF processing completed successfully!")
    else:
        typer.echo("Failed to process PDF.", err=True)
        raise typer.Exit(code=1)

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, help="Maximum number of results")
):
    """Search for content in the vector database."""
    processor = PDFProcessor()
    results = processor.search_documents(query=query, limit=limit)
    
    if not results:
        typer.echo("No results found.")
        return
        
    typer.echo(f"Found {len(results)} results:")
    for i, doc in enumerate(results, 1):
        typer.echo(f"\n--- Result {i} ---")
        typer.echo(f"Content: {doc.content[:200]}...")
        if hasattr(doc, 'meta') and doc.meta:
            typer.echo(f"Metadata: {doc.meta}")

if __name__ == "__main__":
    app()
