"""
Knowledge processing module for the Data Flywheel Chatbot.

This module handles text extraction from uploaded files and provides
simple keyword-based retrieval for the chat system.
"""

import os
import re
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from .models import KnowledgeFile
from .utils import setup_logging

logger = setup_logging()


class KnowledgeProcessor:
    """
    Simple knowledge processor that extracts text from files and provides
    keyword-based search functionality.
    """
    
    def __init__(self, uploads_dir: str = "uploads"):
        """
        Initialize the knowledge processor.
        
        Args:
            uploads_dir: Directory where uploaded files are stored
        """
        self.uploads_dir = uploads_dir
    
    def extract_text_from_file(self, file_path: str, content_type: str) -> str:
        """
        Extract text content from a file based on its content type.
        
        Args:
            file_path: Path to the file
            content_type: MIME type of the file
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            if content_type == "text/plain":
                return self._extract_from_txt(file_path)
            elif content_type == "application/pdf":
                return self._extract_from_pdf(file_path)
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self._extract_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {str(e)}")
            raise
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from a TXT file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using basic text extraction.
        
        Note: This is a simplified implementation. For production,
        consider using libraries like PyPDF2 or pdfplumber.
        """
        try:
            # Try to import PyPDF2 if available
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            # Fallback: treat as binary and extract readable text
            logger.warning("PyPDF2 not available, using basic text extraction for PDF")
            with open(file_path, 'rb') as f:
                content = f.read()
                # Extract readable ASCII text from binary content
                text = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', content.decode('utf-8', errors='ignore'))
                # Clean up multiple spaces and empty lines
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
    
    def _extract_from_docx(self, file_path: str) -> str:
        """
        Extract text from a DOCX file.
        
        Note: This is a simplified implementation. For production,
        consider using python-docx library.
        """
        try:
            # Try to import python-docx if available
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            # Fallback: basic text extraction from DOCX (which is a ZIP file)
            logger.warning("python-docx not available, using basic text extraction for DOCX")
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                try:
                    # Extract text from document.xml
                    xml_content = zip_file.read('word/document.xml').decode('utf-8')
                    # Remove XML tags and extract text
                    text = re.sub(r'<[^>]+>', ' ', xml_content)
                    text = re.sub(r'\s+', ' ', text)
                    return text.strip()
                except:
                    return "Could not extract text from DOCX file"
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + chunk_size // 2:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def search_knowledge(self, query: str, db: Session, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Search for relevant knowledge snippets using keyword matching.
        
        Args:
            query: Search query
            db: Database session
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant snippets with metadata
        """
        try:
            # Get all knowledge files from database
            knowledge_files = db.query(KnowledgeFile).all()
            
            if not knowledge_files:
                logger.info("No knowledge files found in database")
                return []
            
            results = []
            query_words = set(query.lower().split())
            
            for file_record in knowledge_files:
                try:
                    # Construct file path
                    safe_filename = f"{file_record.sha256[:16]}_{file_record.filename}"
                    file_path = os.path.join(self.uploads_dir, safe_filename)
                    
                    if not os.path.exists(file_path):
                        logger.warning(f"File not found: {file_path}")
                        continue
                    
                    # Extract text from file
                    text = self.extract_text_from_file(file_path, file_record.content_type)
                    
                    # Chunk the text
                    chunks = self.chunk_text(text)
                    
                    # Score each chunk based on keyword matches
                    for chunk in chunks:
                        chunk_lower = chunk.lower()
                        matches = sum(1 for word in query_words if word in chunk_lower)
                        
                        if matches > 0:
                            # Calculate relevance score
                            score = matches / len(query_words)
                            
                            results.append({
                                'filename': file_record.filename,
                                'content': chunk,
                                'score': score,
                                'file_id': file_record.id
                            })
                
                except Exception as e:
                    logger.error(f"Error processing file {file_record.filename}: {str(e)}")
                    continue
            
            # Sort by relevance score and return top results
            results.sort(key=lambda x: x['score'], reverse=True)

            # Safety caps: limit to max 3 results and cap total context length
            max_results = min(max_results, 3)  # Hard cap at 3 results
            top_results = results[:max_results]

            # Cap total context to ~2-3k characters
            total_chars = 0
            capped_results = []
            for result in top_results:
                content_length = len(result['content'])
                if total_chars + content_length <= 2500:  # Leave room for other context
                    capped_results.append(result)
                    total_chars += content_length
                    logger.info(f"Knowledge source used: {result['filename']} (score: {result['score']:.2f})")
                else:
                    logger.info(f"Knowledge source skipped due to context limit: {result['filename']}")
                    break

            return capped_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
