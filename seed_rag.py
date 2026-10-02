import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_astradb import AstraDBVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

def upload_full_dataset():
    # 1. Initialize the local embedding model
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 2. Connect to AstraDB Cloud
    vector_store = AstraDBVectorStore(
        collection_name="indb_foods",
        embedding=embeddings,
        api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
        token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
        namespace="default_keyspace"
    )
    
    print("Connected to AstraDB. Loading CSV...")

    # 3. Read the dataset and clean empty values
    df = pd.read_csv("indb_full.csv")
    df = df.fillna(0)  # Replaces missing data (NaN) with 0 to prevent math errors later
    
    # 4. Convert rows into LangChain Documents
    documents = []
    for _, row in df.iterrows():
        content = str(row['food_name'])
        meta = row.to_dict()
        documents.append(Document(page_content=content, metadata=meta))

    # 5. Push to the cloud in smaller batches to prevent timeouts
    batch_size = 100
    total_docs = len(documents)
    
    print(f"Uploading {total_docs} highly detailed dishes to AstraDB in batches of {batch_size}...")
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i : i + batch_size]
        print(f"Pushing records {i} to {i + len(batch)}...")
        vector_store.add_documents(batch)
        
    print("Upload complete! Your comprehensive RAG knowledgebase is ready.")

if __name__ == "__main__":
    upload_full_dataset()