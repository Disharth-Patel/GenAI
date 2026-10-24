import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings

logger = logging.getLogger("retrieval_service")

class RetrievalService:
    """
    Service to retrieve relevant context from the vector database for RAG.
    """
    def __init__(self):
        self.vector_db_path = settings.VECTOR_DB_PATH
        self.embedding_model = settings.EMBEDDING_MODEL

        # Initialize ChromaDB Client
        self.client = chromadb.PersistentClient(path=self.vector_db_path)
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

        self.collection_name = "obc_knowledge_base"
        # We use get_collection instead of get_or_create to ensure we only retrieve
        # if the ingestion process has actually run.
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.emb_fn
            )
        except Exception:
            self.collection = None
            logger.warning("Knowledge collection not found. Please run ingestion first.")

    async def retrieve_context(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant document chunks for a given query.
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            # Format results into a list of dictionaries
            retrieved_docs = []
            # results['documents'][0] contains the list of documents for the first (and only) query
            for i in range(len(results['documents'][0])):
                retrieved_docs.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "id": results['ids'][0][i]
                })

            return retrieved_docs
        except Exception as e:
            logger.error(f"Error retrieving context from ChromaDB: {e}")
            return []

retrieval_service = RetrievalService()
