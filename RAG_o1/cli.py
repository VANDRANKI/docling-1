import argparse
import sys
from pathlib import Path
import json
from typing import List, Optional

from .rag_system import RAGSystem
from .config import RAGConfig
from .logger import RAGLogger

def process_documents(args: argparse.Namespace, config: RAGConfig) -> int:
    """
    Process documents command handler.
    
    Args:
        args: Command line arguments
        config: Configuration object
        
    Returns:
        Exit code
    """
    logger = RAGLogger().get_logger()
    
    try:
        # Initialize RAG system
        rag = RAGSystem(config)
        
        # Get document paths
        if args.directory:
            documents = list(Path(args.directory).glob("*.md"))
            if not documents:
                logger.error(f"No markdown files found in {args.directory}")
                return 1
        else:
            documents = [Path(doc) for doc in args.documents]
        
        # Process documents
        stats = rag.process_documents(documents)
        
        # Print results
        print("\nProcessing Statistics:")
        print(json.dumps(stats, indent=2))
        
        if stats['errors']:
            print("\nErrors occurred during processing:")
            for error in stats['errors']:
                print(f"Document: {error['document']}")
                print(f"Error: {error['error']}\n")
        
        return 0 if stats['processed_documents'] > 0 else 1
        
    except Exception as e:
        logger.error(f"Failed to process documents: {str(e)}")
        return 1

def query_system(args: argparse.Namespace, config: RAGConfig) -> int:
    """
    Query system command handler.
    
    Args:
        args: Command line arguments
        config: Configuration object
        
    Returns:
        Exit code
    """
    logger = RAGLogger().get_logger()
    
    try:
        # Initialize RAG system
        rag = RAGSystem(config)
        
        # Load existing state if available
        if args.load_dir:
            rag.load_state(Path(args.load_dir))
        
        # Process query
        results = rag.query(
            args.query,
            top_k=args.top_k,
            use_graph_expansion=not args.no_graph_expansion
        )
        
        # Print results
        print(f"\nQuery: {results['query']}")
        print(f"Time: {results['timestamp']}")
        print("\nTop Results:")
        
        for i, chunk in enumerate(results['chunks'], 1):
            print(f"\n{i}. Score: {chunk['score']:.3f}")
            print(f"Source: {chunk['metadata'].get('file_path', 'Unknown')}")
            print(f"Text: {chunk['text'][:500]}...")
        
        if 'sources' in results:
            print("\nSources Used:")
            for source, chunks in results['sources'].items():
                print(f"\n{source}:")
                for chunk in chunks:
                    print(f"- Score: {chunk['score']:.3f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        return 1

def main(args: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        args: Optional command line arguments
        
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Graph-based RAG System for Ceria Research Papers"
    )
    
    # Global options
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Process documents command
    process_parser = subparsers.add_parser(
        "process",
        help="Process documents and build knowledge graph"
    )
    doc_group = process_parser.add_mutually_exclusive_group(required=True)
    doc_group.add_argument(
        "--documents",
        nargs="+",
        help="Paths to documents to process"
    )
    doc_group.add_argument(
        "--directory",
        help="Directory containing documents to process"
    )
    process_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save graph after processing"
    )
    
    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the RAG system"
    )
    query_parser.add_argument(
        "query",
        help="Query string"
    )
    query_parser.add_argument(
        "--load-dir",
        help="Directory containing saved state to load"
    )
    query_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return"
    )
    query_parser.add_argument(
        "--no-graph-expansion",
        action="store_true",
        help="Disable graph-based expansion"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Load configuration
    try:
        if parsed_args.config:
            with open(parsed_args.config) as f:
                config_dict = json.load(f)
            config = RAGConfig.from_dict(config_dict)
        else:
            config = RAGConfig()
        
        # Set debug level if requested
        if parsed_args.debug:
            logger = RAGLogger(level="DEBUG")
        
    except Exception as e:
        print(f"Failed to load configuration: {str(e)}", file=sys.stderr)
        return 1
    
    # Execute command
    if parsed_args.command == "process":
        return process_documents(parsed_args, config)
    elif parsed_args.command == "query":
        return query_system(parsed_args, config)
    else:
        print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
