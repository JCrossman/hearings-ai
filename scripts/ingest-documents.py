#!/usr/bin/env python3
"""Document ingestion pipeline for Hearings AI.

Processes PDF documents:
1. Extract text from PDF
2. Chunk text (512 tokens, 128 overlap)
3. Generate embeddings via Azure OpenAI
4. Index chunks in Azure AI Search
5. Store metadata in Cosmos DB
"""

import asyncio
import json
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

import tiktoken
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.storage.blob.aio import BlobServiceClient
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from pypdf import PdfReader

# Load environment
load_dotenv(Path(__file__).parent.parent / "api" / ".env")

# Configuration
SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX", "hearings-index")
OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-3-large")
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "hearings")
STORAGE_URL = os.environ["STORAGE_ACCOUNT_URL"]
STORAGE_CONTAINER = os.environ.get("STORAGE_CONTAINER", "hearing-documents")

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE_TOKENS", "512"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP_TOKENS", "128"))

# Tokenizer for chunk sizing
TOKENIZER = tiktoken.get_encoding("cl100k_base")

# Document metadata from sample-proceedings.json
SAMPLE_METADATA = json.loads(
    (Path(__file__).parent.parent / "test-data" / "metadata" / "sample-proceedings.json").read_text()
)


def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    """Extract text from PDF, preserving page numbers."""
    pages = []
    try:
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({
                    "page_number": i + 1,
                    "text": text,
                })
    except Exception as e:
        print(f"    Warning: Error extracting PDF: {e}")
    return pages


def extract_paragraph_numbers(text: str) -> list[str]:
    """Extract -style paragraph numbers like [1], [2], etc."""
    return re.findall(r'\[(\d+)\]', text)


def extract_regulatory_citations(text: str) -> list[str]:
    """Extract regulatory citations from text."""
    citations = set()
    
    # Legislation patterns
    legislation_patterns = [
        r'REDA\s+s\.?\s*\d+',
        r'EPEA\s+s\.?\s*\d+',
        r'OGCA\s+s\.?\s*\d+',
        r'Pipeline\s+Act\s+s\.?\s*\d+',
        r'Water\s+Act\s+s\.?\s*\d+',
        r'Public\s+Lands\s+Act\s+s\.?\s*\d+',
    ]
    
    # Directive patterns
    directive_patterns = [
        r'Directive\s+0?\d+',
        r'Directive\s+0?\d+\s+s\.?\s*[\d\.]+',
    ]
    
    for pattern in legislation_patterns + directive_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        citations.update(matches)
    
    return list(citations)


def chunk_text(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Chunk text into token-sized pieces with overlap, preserving page info."""
    chunks = []
    current_chunk = []
    current_tokens = 0
    current_page = 1
    chunk_id = 0
    
    for page in pages:
        page_num = page["page_number"]
        text = page["text"]
        
        # Split by paragraphs (try to preserve paragraph structure)
        paragraphs = re.split(r'\n\s*\n', text)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            para_tokens = len(TOKENIZER.encode(para))
            
            # If this paragraph alone exceeds chunk size, split it
            if para_tokens > chunk_size:
                # First, save current chunk if any
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    para_nums = extract_paragraph_numbers(chunk_text)
                    chunks.append({
                        "chunk_id": chunk_id,
                        "content": chunk_text,
                        "page_number": current_page,
                        "paragraph_number": para_nums[0] if para_nums else None,
                        "regulatory_citations": extract_regulatory_citations(chunk_text),
                    })
                    chunk_id += 1
                    current_chunk = []
                    current_tokens = 0
                
                # Split long paragraph by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    sent_tokens = len(TOKENIZER.encode(sent))
                    if current_tokens + sent_tokens > chunk_size and current_chunk:
                        chunk_text = " ".join(current_chunk)
                        para_nums = extract_paragraph_numbers(chunk_text)
                        chunks.append({
                            "chunk_id": chunk_id,
                            "content": chunk_text,
                            "page_number": current_page,
                            "paragraph_number": para_nums[0] if para_nums else None,
                            "regulatory_citations": extract_regulatory_citations(chunk_text),
                        })
                        chunk_id += 1
                        # Keep overlap
                        overlap_text = " ".join(current_chunk[-2:]) if len(current_chunk) >= 2 else ""
                        current_chunk = [overlap_text] if overlap_text else []
                        current_tokens = len(TOKENIZER.encode(overlap_text)) if overlap_text else 0
                    
                    current_chunk.append(sent)
                    current_tokens += sent_tokens
                    current_page = page_num
            
            elif current_tokens + para_tokens > chunk_size:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                para_nums = extract_paragraph_numbers(chunk_text)
                chunks.append({
                    "chunk_id": chunk_id,
                    "content": chunk_text,
                    "page_number": current_page,
                    "paragraph_number": para_nums[0] if para_nums else None,
                    "regulatory_citations": extract_regulatory_citations(chunk_text),
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                overlap_paragraphs = current_chunk[-1:] if current_chunk else []
                current_chunk = overlap_paragraphs + [para]
                current_tokens = sum(len(TOKENIZER.encode(p)) for p in current_chunk)
                current_page = page_num
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
                current_page = page_num
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_text = "\n\n".join(current_chunk)
        para_nums = extract_paragraph_numbers(chunk_text)
        chunks.append({
            "chunk_id": chunk_id,
            "content": chunk_text,
            "page_number": current_page,
            "paragraph_number": para_nums[0] if para_nums else None,
            "regulatory_citations": extract_regulatory_citations(chunk_text),
        })
    
    return chunks


def get_document_metadata(filename: str) -> Optional[dict]:
    """Get metadata for a document from sample-proceedings.json."""
    for doc in SAMPLE_METADATA.get("sample_documents", []):
        # Match by filename patterns
        if doc.get("abaer_citation") and doc["abaer_citation"].replace("-", "") in filename.replace("-", ""):
            return doc
        if "proceeding" in filename.lower():
            # Try to match by proceeding ID
            for proc in SAMPLE_METADATA.get("proceedings", []):
                if f"proceeding-{proc['proceeding_id']}" in filename.lower():
                    return {
                        "proceeding_id": proc["proceeding_id"],
                        "document_type": "transcript" if "vol" in filename.lower() else "procedural",
                        "title": proc["title"],
                        "confidentiality_level": "public",
                        "parties": [proc.get("applicant", {})] + proc.get("interveners", []),
                    }
    
    # Default metadata based on filename
    if "ABAER" in filename.upper():
        return {
            "document_type": "decision",
            "abaer_citation": filename.replace(".pdf", ""),
            "confidentiality_level": "public",
        }
    
    return None


async def generate_embeddings(
    openai_client: AsyncAzureOpenAI,
    texts: list[str],
    batch_size: int = 16,
) -> list[list[float]]:
    """Generate embeddings for texts in batches."""
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = await openai_client.embeddings.create(
            input=batch,
            model=EMBEDDING_DEPLOYMENT,
        )
        embeddings.extend([e.embedding for e in response.data])
    
    return embeddings


async def index_chunks(
    search_client: SearchClient,
    document_id: str,
    chunks: list[dict],
    embeddings: list[list[float]],
    metadata: dict,
) -> int:
    """Index chunks in Azure AI Search."""
    documents = []
    
    for chunk, embedding in zip(chunks, embeddings):
        doc = {
            "id": f"{document_id}-{chunk['chunk_id']}",
            "documentId": document_id,
            "proceedingId": metadata.get("proceeding_id", "unknown"),
            "documentType": metadata.get("document_type", "unknown"),
            "abaerCitation": metadata.get("abaer_citation"),
            "chunkId": chunk["chunk_id"],
            "pageNumber": chunk["page_number"],
            "paragraphNumber": chunk.get("paragraph_number"),
            "sectionTitle": None,  # Could be extracted from headers
            "content": chunk["content"],
            "contentVector": embedding,
            "confidentialityLevel": metadata.get("confidentiality_level", "public"),
            "parties": [p.get("name", p) if isinstance(p, dict) else p for p in metadata.get("parties", [])],
            "regulatoryCitations": chunk.get("regulatory_citations", []),
            "title": metadata.get("title", "Unknown Document"),
            "sourceUrl": metadata.get("source_url"),
        }
        documents.append(doc)
    
    # Upload in batches
    batch_size = 100
    indexed = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        result = await search_client.upload_documents(documents=batch)
        indexed += len([r for r in result if r.succeeded])
    
    return indexed


async def save_document_metadata(
    cosmos_container,
    document_id: str,
    filename: str,
    metadata: dict,
    chunk_count: int,
) -> None:
    """Save document metadata to Cosmos DB."""
    doc = {
        "id": document_id,
        "proceedingId": metadata.get("proceeding_id", "unknown"),
        "documentType": metadata.get("document_type", "unknown"),
        "abaerCitation": metadata.get("abaer_citation"),
        "title": metadata.get("title", filename),
        "confidentialityLevel": metadata.get("confidentiality_level", "public"),
        "parties": metadata.get("parties", []),
        "regulatoryCitations": metadata.get("regulatory_citations", []),
        "sourceUrl": metadata.get("source_url"),
        "uploadedAt": datetime.utcnow().isoformat(),
        "processingStatus": "indexed",
        "chunkCount": chunk_count,
        "filename": filename,
    }
    
    await cosmos_container.upsert_item(doc)


async def process_document(
    pdf_path: Path,
    credential,
    openai_client: AsyncAzureOpenAI,
    search_client: SearchClient,
    cosmos_container,
) -> dict:
    """Process a single document end-to-end."""
    filename = pdf_path.name
    document_id = str(uuid.uuid4())
    
    print(f"\n  Processing: {filename}")
    
    # Get metadata
    metadata = get_document_metadata(filename) or {}
    metadata["source_url"] = f"https://static.aer.ca/prd/documents/decisions/2024/{filename}"
    
    # Extract text
    print(f"    Extracting text...")
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        print(f"    ✗ No text extracted")
        return {"filename": filename, "status": "failed", "reason": "no text"}
    
    total_text = sum(len(p["text"]) for p in pages)
    print(f"    Found {len(pages)} pages, {total_text:,} characters")
    
    # Chunk text
    print(f"    Chunking...")
    chunks = chunk_text(pages)
    print(f"    Created {len(chunks)} chunks")
    
    if not chunks:
        return {"filename": filename, "status": "failed", "reason": "no chunks"}
    
    # Generate embeddings
    print(f"    Generating embeddings...")
    texts = [c["content"] for c in chunks]
    embeddings = await generate_embeddings(openai_client, texts)
    print(f"    Generated {len(embeddings)} embeddings")
    
    # Index in search
    print(f"    Indexing...")
    indexed = await index_chunks(search_client, document_id, chunks, embeddings, metadata)
    print(f"    Indexed {indexed} chunks")
    
    # Save metadata to Cosmos
    print(f"    Saving metadata...")
    await save_document_metadata(cosmos_container, document_id, filename, metadata, len(chunks))
    
    print(f"    ✓ Complete: {filename}")
    
    return {
        "filename": filename,
        "document_id": document_id,
        "status": "success",
        "pages": len(pages),
        "chunks": len(chunks),
        "indexed": indexed,
    }


async def main():
    """Process all documents in test-data/documents."""
    print("=" * 60)
    print("Hearings AI - Document Ingestion Pipeline")
    print("=" * 60)
    
    docs_dir = Path(__file__).parent.parent / "test-data" / "documents"
    pdf_files = list(docs_dir.glob("*.pdf"))
    
    print(f"\nFound {len(pdf_files)} PDF files to process")
    print(f"Search endpoint: {SEARCH_ENDPOINT}")
    print(f"OpenAI endpoint: {OPENAI_ENDPOINT}")
    print(f"Cosmos endpoint: {COSMOS_ENDPOINT}")
    
    # Initialize clients
    credential = DefaultAzureCredential()
    
    # Create async token provider
    async def get_token():
        token = await credential.get_token("https://cognitiveservices.azure.com/.default")
        return token.token
    
    openai_client = AsyncAzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        azure_ad_token_provider=get_token,
        api_version="2024-06-01",
    )
    
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential,
    )
    
    cosmos_client = CosmosClient(
        url=COSMOS_ENDPOINT,
        credential=credential,
    )
    database = cosmos_client.get_database_client(COSMOS_DATABASE)
    container = database.get_container_client("documents")
    
    # Process documents
    results = []
    for pdf_path in pdf_files:
        try:
            result = await process_document(
                pdf_path,
                credential,
                openai_client,
                search_client,
                container,
            )
            results.append(result)
        except Exception as e:
            print(f"    ✗ Failed: {pdf_path.name} - {e}")
            results.append({
                "filename": pdf_path.name,
                "status": "failed",
                "reason": str(e),
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("Ingestion Complete")
    print("=" * 60)
    
    success = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]
    
    print(f"\nSuccessful: {len(success)}")
    for r in success:
        print(f"  ✓ {r['filename']}: {r['chunks']} chunks indexed")
    
    if failed:
        print(f"\nFailed: {len(failed)}")
        for r in failed:
            print(f"  ✗ {r['filename']}: {r.get('reason', 'unknown')}")
    
    total_chunks = sum(r.get("chunks", 0) for r in success)
    print(f"\nTotal chunks indexed: {total_chunks}")
    
    await cosmos_client.close()
    await search_client.close()


if __name__ == "__main__":
    asyncio.run(main())
