# Graph-based RAG System for Ceria Research Papers

A robust Retrieval-Augmented Generation (RAG) system specifically designed for processing and querying scientific papers about Ceria synthesis and properties. The system implements a graph-based approach to enhance retrieval accuracy and maintain context relationships between document chunks.

## Features

- 📊 Graph-based document representation
- 🔍 Context-aware chunk retrieval
- 📝 Markdown document processing
- 📈 Detailed error tracking and logging
- 🛠️ Configurable system parameters
- 🔧 Command-line interface
- 💾 State persistence and loading

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd RAG_o1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The system can be configured through:

1. Environment variables
2. Configuration file (JSON)
3. Command-line arguments

### Environment Variables

- `USE_GPU`: Set to "true" to enable GPU acceleration
- `VECTOR_DB_TYPE`: Vector database type (default: "qdrant")
- `EMBEDDING_MODEL`: Embedding model name (default: "sentence-transformers/all-MiniLM-L6-v2")
- `CHUNK_SIZE`: Document chunk size (default: 500)

### Configuration File

Create a `config.json` file:

```json
{
    "vector_db": {
        "db_type": "qdrant",
        "collection_name": "ceria_research",
        "location": ":memory:"
    },
    "embedding": {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "max_length": 512
    },
    "chunking": {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "chunk_type": "hierarchical"
    },
    "graph": {
        "enable_graph": true,
        "similarity_threshold": 0.75,
        "max_connections": 5
    }
}
```

## Usage

### Command Line Interface

1. Process documents:
```bash
python -m RAG_o1.cli process --directory path/to/markdown/files
```

2. Query the system:
```bash
python -m RAG_o1.cli query "What are the synthesis methods for ceria nanoparticles?"
```

### Python API

```python
from RAG_o1 import RAGSystem, RAGConfig

# Initialize system
config = RAGConfig()
rag = RAGSystem(config)

# Process documents
docs_dir = "path/to/markdown/files"
stats = rag.process_documents(docs_dir)

# Query
results = rag.query(
    "What are the synthesis methods for ceria nanoparticles?",
    top_k=5
)

# Save state
rag.save_state("path/to/save/dir")

# Load state
rag.load_state("path/to/save/dir")
```

## System Architecture

### Components

1. **Document Processor**
   - Handles markdown parsing
   - Extracts metadata
   - Implements chunking strategies
   - Cleans and normalizes text

2. **Knowledge Graph**
   - Builds graph representation of documents
   - Manages node connections based on similarity
   - Implements graph-based retrieval
   - Caches embeddings for efficiency

3. **RAG System**
   - Coordinates component interactions
   - Manages system state
   - Handles queries and retrieval
   - Provides error tracking

4. **Logger**
   - Detailed error tracking
   - Component-level logging
   - Error statistics and summaries

### Graph-based Retrieval

The system uses a graph structure where:
- Nodes represent document chunks
- Edges represent semantic relationships
- Edge weights indicate similarity scores
- Graph traversal enhances retrieval context

Benefits:
- Maintains document relationships
- Improves context awareness
- Enables similarity-based expansion
- Reduces information loss

## Error Handling

The system implements comprehensive error handling:

1. **Component-level Tracking**
   - Each component tracks its own errors
   - Detailed error context is preserved
   - Error statistics are maintained

2. **Error Recovery**
   - Graceful failure handling
   - State preservation on errors
   - Detailed error reporting

3. **Logging**
   - Multiple log levels (DEBUG, INFO, ERROR)
   - Rotating log files
   - Structured log format

## Performance Optimization

1. **Embedding Cache**
   - Caches computed embeddings
   - Reduces redundant computations
   - Persists across sessions

2. **Batch Processing**
   - Efficient document batch processing
   - Optimized graph updates
   - Memory-efficient operations

3. **GPU Acceleration**
   - Optional GPU support for embeddings
   - Configurable device selection
   - Automatic fallback to CPU

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Citation

If you use this system in your research, please cite:

```bibtex
@software{rag_system_2024,
    title = {Graph-based RAG System for Ceria Research Papers},
    author = {Cline},
    year = {2024},
    version = {0.1.0}
}
