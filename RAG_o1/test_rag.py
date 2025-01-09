"""
Test script to demonstrate the RAG system workflow with Ceria research papers.
"""

import sys
from pathlib import Path
import json
from tqdm import tqdm
from multiprocessing import Pool

from RAG_o1 import RAGSystem, RAGConfig
from RAG_o1.logger import RAGLogger


def process_document_wrapper(doc_path):
    """
    Wrapper to process a single document for multiprocessing.
    Args:
        doc_path (Path): Path to the markdown file.
    Returns:
        dict: Statistics or errors from document processing.
    """
    try:
        rag = RAGSystem(RAGConfig())
        return rag.process_documents([doc_path], save_graph=False)
    except Exception as e:
        return {"document": str(doc_path), "error": str(e)}


def main():
    # Initialize logger
    logger = RAGLogger().get_logger()
    logger.info("Starting RAG system test")

    try:
        # Initialize system with default config
        config = RAGConfig()
        rag = RAGSystem(config)

        # Process markdown papers
        papers_dir = Path(__file__).parent / "data" / "markdown_papers"
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

        # Parallel processing with progress bar
        logger.info("Processing documents in parallel...")
        with Pool(processes=4) as pool:  # Adjust the number of processes based on system resources
            results = list(tqdm(pool.imap(process_document_wrapper, markdown_files), total=len(markdown_files)))

        # Aggregate statistics
        total_documents = len(markdown_files)
        processed_documents = sum(1 for result in results if "errors" not in result)
        total_chunks = sum(result.get("total_chunks", 0) for result in results if "errors" not in result)
        errors = [result for result in results if "errors" in result]

        stats = {
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "total_chunks": total_chunks,
            "errors": errors,
        }
        print("\nProcessing Statistics:")
        print(json.dumps(stats, indent=2))

        if stats["errors"]:
            print("\nErrors occurred during processing:")
            for error in stats["errors"]:
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
            "How does pH affect the synthesis of ceria?",
        ]

        print("\nTesting Queries:")
        for query in test_queries:
            print(f"\nQuery: {query}")
            results = rag.query(query, top_k=3)

            print("\nTop Results:")
            for i, chunk in enumerate(results["chunks"], 1):
                print(f"\n{i}. Score: {chunk['score']:.3f}")
                print(f"Source: {chunk['metadata'].get('file_path', 'Unknown')}")
                print(f"Text: {chunk['text'][:300]}...")

        return 0

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
