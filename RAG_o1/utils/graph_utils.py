import networkx as nx
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
from loguru import logger
import torch
from sentence_transformers import SentenceTransformer
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # To avoid warnings

class KnowledgeGraph:
    """
    Graph-based knowledge representation for RAG system.
    """
    
    def __init__(self, config: Any):
        """
        Initialize knowledge graph.
        
        Args:
            config: Configuration object containing graph settings
        """
        self.config = config
        self.logger = logger.bind(component="KnowledgeGraph")
        self.graph = nx.Graph()
        
        # Initialize embedding model
        try:
            self.model = SentenceTransformer(
                self.config.embedding.model_name,
                device=self.config.embedding.device
            )
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {str(e)}")
            raise
        
        # Cache for embeddings
        self.embedding_cache = {}
        self.cache_file = self.config.cache_dir / "embeddings_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load embeddings cache from file if it exists."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.embedding_cache = json.load(f)
                self.logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                self.logger.warning(f"Failed to load embeddings cache: {str(e)}")
                self.embedding_cache = {}
    
    def _save_cache(self):
        """Save embeddings cache to file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.embedding_cache, f)
            self.logger.info(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            self.logger.warning(f"Failed to save embeddings cache: {str(e)}")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text, using cache if available.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding
        """
        # Use hash of text as cache key
        cache_key = str(hash(text))
        
        if cache_key in self.embedding_cache:
            return np.array(self.embedding_cache[cache_key])
        
        try:
            with torch.no_grad():
                embedding = self.model.encode(text)
            
            # Cache the embedding
            self.embedding_cache[cache_key] = embedding.tolist()
            self._save_cache()
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Similarity score between 0 and 1
        """
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
    
    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Get embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        # Use cache for texts that are already embedded
        cached_embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        for i, text in enumerate(texts):
            cache_key = str(hash(text))
            if cache_key in self.embedding_cache:
                cached_embeddings.append((i, np.array(self.embedding_cache[cache_key])))
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        if texts_to_embed:
            try:
                with torch.no_grad():
                    batch_embeddings = self.model.encode(
                        texts_to_embed,
                        batch_size=self.config.chunking.batch_size,
                        show_progress_bar=True
                    )
                
                # Cache new embeddings
                for idx, embedding in zip(indices_to_embed, batch_embeddings):
                    cache_key = str(hash(texts[idx]))
                    self.embedding_cache[cache_key] = embedding.tolist()
                
                # Save cache periodically
                if len(self.embedding_cache) % 100 == 0:
                    self._save_cache()
                
            except Exception as e:
                self.logger.error(f"Failed to generate batch embeddings: {str(e)}")
                raise
        
        # Combine cached and new embeddings
        all_embeddings = [None] * len(texts)
        for i, emb in cached_embeddings:
            all_embeddings[i] = emb
        
        if texts_to_embed:
            for idx, emb in zip(indices_to_embed, batch_embeddings):
                all_embeddings[idx] = emb
        
        return all_embeddings

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Add document chunks to knowledge graph.
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
        """
        try:
            # Get embeddings in batches
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.get_embeddings_batch(texts)
            
            # First pass: Add nodes
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                node_id = f"chunk_{i}"
                self.graph.add_node(
                    node_id,
                    text=chunk['text'],
                    metadata=chunk['metadata'],
                    embedding=embedding
                )
            
            # Second pass: Add edges between similar nodes
            nodes = list(self.graph.nodes(data=True))
            for i, (node1, data1) in enumerate(nodes):
                embedding1 = data1['embedding']
                
                # Find similar nodes
                similarities = []
                for node2, data2 in nodes[i+1:]:
                    similarity = self.compute_similarity(embedding1, data2['embedding'])
                    if similarity >= self.config.graph.similarity_threshold:
                        similarities.append((node2, similarity))
                
                # Sort by similarity and keep top K connections
                similarities.sort(key=lambda x: x[1], reverse=True)
                for node2, similarity in similarities[:self.config.graph.max_connections]:
                    self.graph.add_edge(node1, node2, weight=similarity)
            
            self.logger.info(
                f"Added {len(chunks)} chunks to graph. "
                f"Graph now has {self.graph.number_of_nodes()} nodes and "
                f"{self.graph.number_of_edges()} edges"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to add chunks to graph: {str(e)}")
            raise
    
    def find_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
        use_graph_expansion: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find chunks relevant to query using graph structure.
        
        Args:
            query: Search query
            top_k: Number of chunks to return
            use_graph_expansion: Whether to use graph structure for expansion
            
        Returns:
            List of relevant chunks with scores
        """
        try:
            query_embedding = self.get_embedding(query)
            
            # First get direct matches
            similarities = []
            for node, data in self.graph.nodes(data=True):
                similarity = self.compute_similarity(query_embedding, data['embedding'])
                similarities.append((node, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_nodes = similarities[:top_k]
            
            if use_graph_expansion and self.config.graph.enable_graph:
                # Expand using graph structure
                expanded_nodes = set()
                for node, score in top_nodes:
                    # Add neighbors with weight decay
                    for neighbor in self.graph.neighbors(node):
                        if neighbor not in expanded_nodes:
                            edge_weight = self.graph[node][neighbor]['weight']
                            decay = 1.0 - self.config.graph.weight_decay
                            expanded_nodes.add((neighbor, score * edge_weight * decay))
                
                # Combine and sort all nodes
                all_nodes = list(top_nodes) + list(expanded_nodes)
                all_nodes.sort(key=lambda x: x[1], reverse=True)
                top_nodes = all_nodes[:top_k]
            
            # Format results
            results = []
            for node, score in top_nodes:
                data = self.graph.nodes[node]
                results.append({
                    'text': data['text'],
                    'metadata': data['metadata'],
                    'score': float(score)
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to find relevant chunks: {str(e)}")
            raise
    
    def save_graph(self, file_path: Optional[Path] = None):
        """
        Save graph structure to file.
        
        Args:
            file_path: Path to save file (default: config.cache_dir/knowledge_graph.json)
        """
        if file_path is None:
            file_path = self.config.cache_dir / "knowledge_graph.json"
        
        try:
            # Convert graph to serializable format
            graph_data = {
                'nodes': [],
                'edges': []
            }
            
            # Save nodes
            for node, data in self.graph.nodes(data=True):
                node_data = {
                    'id': node,
                    'text': data['text'],
                    'metadata': data['metadata'],
                    'embedding': data['embedding'].tolist()
                }
                graph_data['nodes'].append(node_data)
            
            # Save edges
            for n1, n2, data in self.graph.edges(data=True):
                edge_data = {
                    'source': n1,
                    'target': n2,
                    'weight': data['weight']
                }
                graph_data['edges'].append(edge_data)
            
            # Save to file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(graph_data, f)
            
            self.logger.info(f"Saved knowledge graph to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save graph: {str(e)}")
            raise
    
    def load_graph(self, file_path: Optional[Path] = None):
        """
        Load graph structure from file.
        
        Args:
            file_path: Path to load file (default: config.cache_dir/knowledge_graph.json)
        """
        if file_path is None:
            file_path = self.config.cache_dir / "knowledge_graph.json"
        
        try:
            with open(file_path, 'r') as f:
                graph_data = json.load(f)
            
            # Create new graph
            self.graph = nx.Graph()
            
            # Load nodes
            for node_data in graph_data['nodes']:
                self.graph.add_node(
                    node_data['id'],
                    text=node_data['text'],
                    metadata=node_data['metadata'],
                    embedding=np.array(node_data['embedding'])
                )
            
            # Load edges
            for edge_data in graph_data['edges']:
                self.graph.add_edge(
                    edge_data['source'],
                    edge_data['target'],
                    weight=edge_data['weight']
                )
            
            self.logger.info(
                f"Loaded knowledge graph with {self.graph.number_of_nodes()} nodes and "
                f"{self.graph.number_of_edges()} edges"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load graph: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage
    from RAG_o1.config import RAGConfig
    
    config = RAGConfig()
    graph = KnowledgeGraph(config)
    
    # Test with some example chunks
    test_chunks = [
        {
            'text': 'This is a test chunk about machine learning.',
            'metadata': {'source': 'test1.md'}
        },
        {
            'text': 'Another chunk about AI and machine learning.',
            'metadata': {'source': 'test2.md'}
        }
    ]
    
    graph.add_chunks(test_chunks)
    
    # Test search
    results = graph.find_relevant_chunks('machine learning')
    for result in results:
        print(f"\nScore: {result['score']:.3f}")
        print(f"Text: {result['text']}")
