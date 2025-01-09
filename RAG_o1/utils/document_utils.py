import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
import markdown
from loguru import logger

os.environ["TOKENIZERS_PARALLELISM"] = "false"  # To avoid warnings

class DocumentProcessor:
    """
    Utility class for processing and cleaning documents.
    """
    
    def __init__(self, config: Any):
        """
        Initialize document processor with configuration.
        
        Args:
            config: Configuration object containing processing settings
        """
        self.config = config
        self.logger = logger.bind(component="DocumentProcessor")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Replace multiple newlines with single newline
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Fix common OCR errors
        text = text.replace('|', 'I')  # Common OCR error
        text = text.replace('0', 'O')  # Common OCR error in academic papers
        
        # Remove special characters but keep essential punctuation
        text = re.sub(r'[^\w\s\.,;:!?\(\)\[\]\{\}\"\'`-]', ' ', text)
        
        return text.strip()
    
    def remove_citations(self, text: str) -> str:
        """
        Remove citation patterns from text.
        
        Args:
            text: Text containing citations
            
        Returns:
            Text with citations removed
        """
        # Remove numbered citations [1], [2,3], etc.
        text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
        
        # Remove author-year citations (Smith et al., 2020)
        text = re.sub(r'\([A-Za-z\s]+(?:et al\.)?(?:,\s*\d{4})+\)', '', text)
        
        return text
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from document text.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Try to extract title
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1)
        
        # Try to extract authors
        author_match = re.search(r'(?:Author|Authors):\s*(.+?)(?:\n|$)', text)
        if author_match:
            authors = [a.strip() for a in author_match.group(1).split(',')]
            metadata['authors'] = authors
        
        # Try to extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            metadata['year'] = int(year_match.group(0))
        
        # Try to extract abstract
        abstract_match = re.search(r'(?:Abstract|ABSTRACT)\s*\n+(.+?)(?:\n\n|$)', text, re.DOTALL)
        if abstract_match:
            metadata['abstract'] = abstract_match.group(1).strip()
        
        return metadata
    
    def process_markdown(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Process markdown file and extract content and metadata.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            Tuple of (processed_text, metadata)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = self.extract_metadata(content)
            
            # Convert markdown to plain text
            html = markdown.markdown(content)
            text = BeautifulSoup(html, 'html.parser').get_text()
            
            # Clean text
            if self.config.processing.clean_whitespace:
                text = self.clean_text(text)
            
            # Remove citations if configured
            if self.config.processing.remove_citations:
                text = self.remove_citations(text)
            
            return text, metadata
            
        except Exception as e:
            self.logger.error(f"Error processing markdown file {file_path}: {str(e)}")
            raise
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks while preserving context.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = []
        chunk_size = self.config.chunking.chunk_size
        overlap = self.config.chunking.chunk_overlap
        
        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > chunk_size and current_chunk:
                # Create chunk with metadata
                chunk_text = ' '.join(current_chunk)
                chunk_dict = {
                    'text': chunk_text,
                    'metadata': metadata or {},
                    'length': len(chunk_text)
                }
                chunks.append(chunk_dict)
                
                # Keep overlap for next chunk
                overlap_tokens = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_chunk = overlap_tokens
                current_length = sum(len(t) for t in overlap_tokens)
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk if it exists
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_dict = {
                'text': chunk_text,
                'metadata': metadata or {},
                'length': len(chunk_text)
            }
            chunks.append(chunk_dict)
        
        return chunks
    
    def process_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process a document file and return chunks with metadata.
        
        Args:
            file_path: Path to document file
            
        Returns:
            List of chunk dictionaries
        """
        try:
            # Process based on file type
            if file_path.suffix.lower() == '.md':
                text, metadata = self.process_markdown(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # Add file metadata
            metadata['file_path'] = str(file_path)
            metadata['file_name'] = file_path.name
            
            # Chunk the document
            chunks = self.chunk_text(text, metadata)
            
            # Filter chunks by minimum length if configured
            if self.config.processing.min_chunk_length:
                chunks = [
                    c for c in chunks 
                    if c['length'] >= self.config.processing.min_chunk_length
                ]
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage
    from RAG_o1.config import RAGConfig
    
    config = RAGConfig()
    processor = DocumentProcessor(config)
    
    # Test with a markdown file
    test_file = Path("path/to/test.md")
    if test_file.exists():
        chunks = processor.process_document(test_file)
        print(f"Generated {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i+1}:")
            print(f"Length: {chunk['length']}")
            print(f"Text: {chunk['text'][:100]}...")
