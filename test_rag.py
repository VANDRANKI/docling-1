"""
Test script to demonstrate the RAG system workflow with Ceria research papers.
"""

import sys
from pathlib import Path
import json
import logging
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
print(f"Added to Python path: {project_root}")
print(f"Current Python path: {sys.path}")

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting imports...")
try:
    from RAG_o1.rag_system import RAGSystem
    logger.debug("Imported RAGSystem")
    from RAG_o1.config import RAGConfig
    logger.debug("Imported RAGConfig")
    from RAG_o1.logger import RAGLogger
    logger.debug("Imported RAGLogger")
except Exception as e:
    logger.error(f"Import error: {str(e)}")
    raise

def main():
    # Initialize logger
    logger = RAGLogger().get_logger()
    logger.info("Starting RAG system test")
    
    try:
        # Initialize system with default config
        config = RAGConfig()
        rag = RAGSystem(config)
        
        # Process markdown papers
        papers_dir = Path("RAG_o1/data/markdown_papers")
        if not papers_dir.exists():
            logger.error(f"Papers directory not found: {papers_dir}")
            logger.info("Make sure you're running the script from the correct directory")
            return 1
        
        # Get all markdown files
        markdown_files = list(papers_dir.glob("*.md"))
        if not markdown_files:
            logger.error("No markdown files found")
            return 1
        
        logger.info(f"Found {len(markdown_files)} markdown files")
        
        # Process documents
        stats = rag.process_documents(markdown_files)
        print("\nProcessing Statistics:")
        print(json.dumps(stats, indent=2))
        
        if stats['errors']:
            print("\nErrors occurred during processing:")
            for error in stats['errors']:
                print(f"Document: {error['document']}")
                print(f"Error: {error['error']}\n")
        
        # Save the system state
        rag.save_state()
        
        # Test queries
        test_queries = [
            "What are the different synthesis methods for ceria nanoparticles?",
            "How does particle size affect the properties of ceria?",
            "What are the applications of ceria in chemical mechanical planarization?",
            "What characterization techniques are used to analyze ceria nanoparticles?",
            "How does pH affect the synthesis of ceria?"
        ]
        
        print("\nTesting Queries:")
        for query in test_queries:
            print(f"\nQuery: {query}")
            results = rag.query(query, top_k=3)
            
            print("\nTop Results:")
            for i, chunk in enumerate(results['chunks'], 1):
                print(f"\n{i}. Score: {chunk['score']:.3f}")
                print(f"Source: {chunk['metadata'].get('file_path', 'Unknown')}")
                print(f"Text: {chunk['text'][:300]}...")
        
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
