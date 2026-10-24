import os
import logging
from app.services.ingestion_service import ingestion_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("data_ingestion_script")

def run_ingestion():
    """
    Orchestrates the ingestion of all raw CSVs into the vector database.
    """
    raw_data_dir = "data/raw" # This is relative to the project root if run from there
    # If running from inside backend, we need to go up
    if not os.path.exists(raw_data_dir):
        raw_data_dir = "../data/raw"

    if not os.path.exists(raw_data_dir):
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        return

    # Define mapping: filename -> (text_columns, id_column)
    # We base this on our discovery of the reference project's files
    csv_mapping = {
        "maharashtra_obc_schemes_expanded.csv": (["scheme_name", "scheme_details", "eligibility"], "scheme_id"),
        "maharashtra_obc_chatbot_knowledgebase_expanded.csv": (["question", "answer"], "entry_id"),
        "maharashtra_obc_seat_capacity_register.csv": (["college_name", "course", "obc_seats"], "seat_id"),
        "maharashtra_obc_chatbot_source_register.csv": (["source_name", "description"], "source_id"),
    }

    logger.info("Starting Knowledge Base ingestion...")
    ingestion_service.clear_knowledge_base()

    total_indexed = 0
    for filename, config in csv_mapping.items():
        file_path = os.path.join(raw_data_dir, filename)
        if os.path.exists(file_path):
            text_cols, id_col = config
            count = ingestion_service.process_csv(file_path, text_cols, id_col)
            total_indexed += count
            logger.info(f"Indexed {count} records from {filename}")
        else:
            logger.warning(f"File {filename} not found in {raw_data_dir}, skipping.")

    logger.info(f"Ingestion complete. Total records indexed: {total_indexed}")

if __name__ == "__main__":
    run_ingestion()
