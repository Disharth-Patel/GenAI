import logging
from typing import List, Dict, Any
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings

logger = logging.getLogger("ingestion_service")

class IngestionService:
    """
    Service to handle the ingestion of raw CSV data into the vector database.
    """
    def __init__(self):
        self.vector_db_path = settings.VECTOR_DB_PATH
        self.embedding_model = settings.EMBEDDING_MODEL

        # Initialize ChromaDB Client
        self.client = chromadb.PersistentClient(path=self.vector_db_path)

        # Use a multilingual embedding function
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

        # Collection name for OBC schemes
        self.collection_name = "obc_knowledge_base"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.emb_fn
        )

    def process_csv(self, file_path: str, text_columns: List[str], id_column: str) -> int:
        """
        Processes a CSV file, extracts text, and adds it to the vector store.
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Processing {file_path} with {len(df)} records.")

            documents = []
            metadatas = []
            ids = []

            for index, row in df.iterrows():
                # Combine relevant text columns into a single document chunk
                content_parts = [str(row[col]) for col in text_columns if col in df.columns]
                document_text = " ".join(content_parts).strip()

                if not document_text:
                    continue

                # Metadata for citations
                metadata = row.to_dict()
                # Ensure metadata values are simple types (str, int, float, bool) for ChromaDB
                sanitized_metadata = {k: (v if isinstance(v, (str, int, float, bool)) else str(v))
                                     for k, v in metadata.items()}

                # Use the provided ID column or fall back to index
                record_id = str(row[id_column]) if id_column in df.columns else f"id_{index}"

                documents.append(document_text)
                metadatas.append(sanitized_metadata)
                ids.append(record_id)

            # Batch add to ChromaDB
            # ChromaDB handles batching internally but we'll do it in chunks of 100 for safety
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                self.collection.add(
                    documents=documents[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                    ids=ids[i : i + batch_size]
                )

            logger.info(f"Successfully indexed {len(documents)} records from {file_path}.")
            return len(documents)

        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            return 0

    def clear_knowledge_base(self):
        """Deletes the existing collection to allow for a clean re-index."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.emb_fn
            )
            logger.info("Knowledge base cleared successfully.")
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")

ingestion_service = IngestionService()
