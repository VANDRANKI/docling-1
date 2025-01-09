from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json
from datetime import datetime

from RAG_o1.utils.document_utils import DocumentProcessor
from RAG_o1.utils.graph_utils import KnowledgeGraph
from RAG_o1.config import RAGConfig
from RAG_o1.logger import RAGLogger, ErrorTracker

class RAGSystem:
    """
    Main RAG system implementation with graph-based retrieval.
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize RAG system.
        
        Args:
            config: Optional configuration object
        """
        self.config = config or RAGConfig()
        self.logger = RAGLogger()
        self.error_tracker = ErrorTracker(self.logger)
        
        # Initialize components
        try:
            self.document_processor = DocumentProcessor(self.config)
            self.knowledge_graph = KnowledgeGraph(self.config)
            
            # Create necessary directories
            self.config.create_directories()
            
        except Exception as e:
            self.error_tracker.record_error(
                error=e,
                component="initialization",
                severity="CRITICAL"
            )
            raise
    
    def process_documents(
        self,
        documents: Union[str, Path, List[Union[str, Path]]],
        save_graph: bool = True
    ) -> Dict[str, Any]:
        """
        Process documents and build knowledge graph.
        
        Args:
            documents: Path(s) to document(s) to process
            save_graph: Whether to save graph after processing
            
        Returns:
            Processing statistics
        """
        try:
            # Convert to list if single path
            if isinstance(documents, (str, Path)):
                documents = [documents]
            
            # Convert to Path objects
            doc_paths = [Path(doc) for doc in documents]
            
            # Validate paths
            invalid_paths = [p for p in doc_paths if not p.exists()]
            if invalid_paths:
                raise ValueError(f"Documents not found: {invalid_paths}")
            
            # Process each document
            all_chunks = []
            stats = {
                'total_documents': len(doc_paths),
                'processed_documents': 0,
                'total_chunks': 0,
                'errors': [],
                'start_time': datetime.now().isoformat()
            }
            
            for doc_path in doc_paths:
                try:
                    self.logger.get_logger().info(f"Processing document: {doc_path}")
                    chunks = self.document_processor.process_document(doc_path)
                    all_chunks.extend(chunks)
                    stats['processed_documents'] += 1
                    stats['total_chunks'] += len(chunks)
                    
                except Exception as e:
                    error_info = {
                        'document': str(doc_path),
                        'error': str(e)
                    }
                    stats['errors'].append(error_info)
                    self.error_tracker.record_error(
                        error=e,
                        component="document_processing",
                        context={'document': str(doc_path)}
                    )
            
            # Build knowledge graph
            if all_chunks:
                self.knowledge_graph.add_chunks(all_chunks)
                if save_graph:
                    self.knowledge_graph.save_graph()
            
            # Update stats
            stats['end_time'] = datetime.now().isoformat()
            stats['graph_nodes'] = self.knowledge_graph.graph.number_of_nodes()
            stats['graph_edges'] = self.knowledge_graph.graph.number_of_edges()
            
            return stats
            
        except Exception as e:
            self.error_tracker.record_error(
                error=e,
                component="document_processing",
                severity="ERROR"
            )
            raise
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        use_graph_expansion: bool = True,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            query: Query string
            top_k: Number of chunks to retrieve
            use_graph_expansion: Whether to use graph-based expansion
            return_sources: Whether to include source documents in response
            
        Returns:
            Query results with relevant chunks and metadata
        """
        try:
            # Find relevant chunks
            chunks = self.knowledge_graph.find_relevant_chunks(
                query,
                top_k=top_k,
                use_graph_expansion=use_graph_expansion
            )
            
            # Format response
            response = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'chunks': chunks
            }
            
            if return_sources:
                # Group chunks by source document
                sources = {}
                for chunk in chunks:
                    source = chunk['metadata'].get('file_path')
                    if source:
                        if source not in sources:
                            sources[source] = []
                        sources[source].append({
                            'text': chunk['text'],
                            'score': chunk['score']
                        })
                
                response['sources'] = sources
            
            return response
            
        except Exception as e:
            self.error_tracker.record_error(
                error=e,
                component="query",
                context={'query': query}
            )
            raise
    
    def save_state(self, directory: Optional[Path] = None):
        """
        Save system state to directory.
        
        Args:
            directory: Directory to save state (default: config.cache_dir)
        """
        try:
            if directory is None:
                directory = self.config.cache_dir
            
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            
            # Save graph
            self.knowledge_graph.save_graph(directory / "knowledge_graph.json")
            
            # Save config
            config_path = directory / "config.json"
            with open(config_path, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            
            # Save error logs
            error_path = directory / "error_summary.json"
            with open(error_path, 'w') as f:
                json.dump(self.error_tracker.get_error_summary(), f, indent=2)
            
            self.logger.get_logger().info(f"Saved system state to {directory}")
            
        except Exception as e:
            self.error_tracker.record_error(
                error=e,
                component="save_state",
                context={'directory': str(directory)}
            )
            raise
    
    def load_state(self, directory: Optional[Path] = None):
        """
        Load system state from directory.
        
        Args:
            directory: Directory to load state from (default: config.cache_dir)
        """
        try:
            if directory is None:
                directory = self.config.cache_dir
            
            directory = Path(directory)
            
            # Load graph
            self.knowledge_graph.load_graph(directory / "knowledge_graph.json")
            
            # Load config
            config_path = directory / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
                self.config = RAGConfig.from_dict(config_dict)
            
            self.logger.get_logger().info(f"Loaded system state from {directory}")
            
        except Exception as e:
            self.error_tracker.record_error(
                error=e,
                component="load_state",
                context={'directory': str(directory)}
            )
            raise

if __name__ == "__main__":
    # Example usage
    config = RAGConfig()
    rag = RAGSystem(config)
    
    # Process documents
    docs_dir = Path("markdown_papers")
    if docs_dir.exists():
        stats = rag.process_documents(list(docs_dir.glob("*.md")))
        print("\nProcessing Stats:")
        print(json.dumps(stats, indent=2))
        
        # Test query
        query = "What are the synthesis methods for ceria nanoparticles?"
        results = rag.query(query)
        print(f"\nQuery: {query}")
        print("\nTop Results:")
        for chunk in results['chunks']:
            print(f"\nScore: {chunk['score']:.3f}")
            print(f"Text: {chunk['text'][:200]}...")
