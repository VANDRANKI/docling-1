import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    db_type: str = Field(
        default="qdrant",
        description="Type of vector database to use (qdrant, milvus, etc.)"
    )
    collection_name: str = Field(
        default="ceria_research",
        description="Name of the vector collection"
    )
    location: str = Field(
        default=":memory:",
        description="Database location (use :memory: for testing)"
    )
    distance_func: str = Field(
        default="Cosine",
        description="Distance function for similarity search"
    )

class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""
    model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Name of the embedding model"
    )
    device: str = Field(
        default="cuda" if os.environ.get("USE_GPU", "false").lower() == "true" else "cpu",
        description="Device to run embeddings on"
    )
    max_length: int = Field(
        default=512,
        description="Maximum sequence length"
    )

class ChunkingConfig(BaseModel):
    """Document chunking configuration."""
    chunk_size: int = Field(
        default=1000,  # Increased chunk size
        description="Size of text chunks"
    )
    chunk_overlap: int = Field(
        default=100,  # Adjusted overlap
        description="Overlap between chunks"
    )
    batch_size: int = Field(
        default=32,  # Added batch size for processing
        description="Batch size for processing chunks"
    )
    chunk_type: str = Field(
        default="hierarchical",
        description="Chunking strategy (hierarchical, sentence, fixed)"
    )

class ProcessingConfig(BaseModel):
    """Document processing configuration."""
    max_docs: Optional[int] = Field(
        default=None,
        description="Maximum number of documents to process"
    )
    file_types: list = Field(
        default=["md", "pdf"],
        description="File types to process"
    )
    min_chunk_length: int = Field(
        default=50,
        description="Minimum length for valid chunks"
    )
    remove_citations: bool = Field(
        default=True,
        description="Whether to remove citations from text"
    )
    clean_whitespace: bool = Field(
        default=True,
        description="Whether to clean excessive whitespace"
    )

class GraphConfig(BaseModel):
    """Graph-based RAG configuration."""
    enable_graph: bool = Field(
        default=True,
        description="Whether to enable graph-based RAG"
    )
    similarity_threshold: float = Field(
        default=0.85,  # Increased threshold for more selective connections
        description="Threshold for connecting nodes in the graph"
    )
    max_connections: int = Field(
        default=3,  # Reduced max connections
        description="Maximum connections per node"
    )
    weight_decay: float = Field(
        default=0.1,
        description="Weight decay for distant connections"
    )

class RAGConfig(BaseModel):
    """Main configuration class for the RAG system."""
    project_dir: Path = Field(
        default=Path(__file__).parent,
        description="Project root directory"
    )
    data_dir: Path = Field(
        default=Path(__file__).parent / "data",
        description="Data directory"
    )
    cache_dir: Path = Field(
        default=Path(__file__).parent / "cache",
        description="Cache directory"
    )
    vector_db: VectorDBConfig = Field(
        default_factory=VectorDBConfig,
        description="Vector database configuration"
    )
    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig,
        description="Embedding model configuration"
    )
    chunking: ChunkingConfig = Field(
        default_factory=ChunkingConfig,
        description="Chunking configuration"
    )
    processing: ProcessingConfig = Field(
        default_factory=ProcessingConfig,
        description="Document processing configuration"
    )
    graph: GraphConfig = Field(
        default_factory=GraphConfig,
        description="Graph-based RAG configuration"
    )
    
    def create_directories(self):
        """Create necessary project directories."""
        for directory in [self.data_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RAGConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()
    
    @classmethod
    def load_from_env(cls) -> 'RAGConfig':
        """Load configuration from environment variables."""
        config_dict = {}
        
        # Map environment variables to config
        env_mapping = {
            "VECTOR_DB_TYPE": ("vector_db", "db_type"),
            "EMBEDDING_MODEL": ("embedding", "model_name"),
            "CHUNK_SIZE": ("chunking", "chunk_size"),
            "USE_GRAPH_RAG": ("graph", "enable_graph"),
        }
        
        for env_var, (section, key) in env_mapping.items():
            if env_var in os.environ:
                if section not in config_dict:
                    config_dict[section] = {}
                config_dict[section][key] = os.environ[env_var]
        
        return cls.from_dict(config_dict)

# Default configuration instance
default_config = RAGConfig()

if __name__ == "__main__":
    # Example usage
    config = RAGConfig()
    config.create_directories()
    print(f"Project directory: {config.project_dir}")
    print(f"Vector DB type: {config.vector_db.db_type}")
    print(f"Embedding model: {config.embedding.model_name}")
