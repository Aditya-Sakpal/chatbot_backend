import os
import tempfile
import traceback
from typing import List, Tuple
import uuid
import PyPDF2
import docx
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from fastapi import UploadFile

from utils.logger import logger
from utils.data_upload_utils import get_chunks
from utils.openai_funcs import get_embeddings
from utils.pinecone_funcs import upsert_chunks

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {traceback.format_exc()}")
        raise e

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {traceback.format_exc()}")
        raise e

def extract_text_from_epub(file_path: str) -> str:
    """Extract text from EPUB file"""
    try:
        book = epub.read_epub(file_path)
        text = ""
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from EPUB: {traceback.format_exc()}")
        raise e

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error extracting text from TXT: {traceback.format_exc()}")
        raise e

def process_document(file_path: str, file_name: str) -> Tuple[str, List[dict]]:
    """
    Process a document and return its text content and chunks
    
    Args:
        file_path (str): Path to the document file
        file_name (str): Name of the document
        
    Returns:
        Tuple[str, List[dict]]: Tuple containing (text_content, chunks)
    """
    try:
        # Determine file type and extract text
        file_extension = os.path.splitext(file_name)[1].lower()
        if file_extension == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            text = extract_text_from_docx(file_path)
        elif file_extension == '.epub':
            text = extract_text_from_epub(file_path)
        elif file_extension == '.txt':
            text = extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
        # Generate chunks and embeddings
        chunks = get_chunks(text)
        vectors = []
        for chunk in chunks:
            vector = get_embeddings(chunk)
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": vector,
                "metadata": {
                    "text": chunk,
                    "source": file_name
                }
            })
            
        return text, vectors
    except Exception as e:
        logger.error(f"Error processing document {file_name}: {traceback.format_exc()}")
        raise e

async def process_and_upsert_documents(files: List[UploadFile], user_id: str) -> List[str]:
    """
    Process multiple documents and upsert their chunks to Pinecone
    
    Args:
        files (List[UploadFile]): List of uploaded files
        user_id (str): User ID
        
    Returns:
        List[str]: List of successfully processed document names
    """
    processed_docs = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        for file in files:
            # Save uploaded file temporarily
            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, 'wb') as buffer:
                content = await file.read()
                buffer.write(content)
                
            # Process document
            text, vectors = process_document(temp_path, file.filename)
            
            # Upsert chunks to Pinecone
            result = upsert_chunks(vectors, user_id)
            if result:
                processed_docs.append(file.filename)
                
            # Clean up temporary file
            os.remove(temp_path)
            
    except Exception as e:
        logger.error(f"Error processing documents: {traceback.format_exc()}")
        raise e
    finally:
        # Clean up temporary directory
        os.rmdir(temp_dir)
        
    return processed_docs 