import os
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_astradb import AstraDBVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# --- 1. USER DATA (MongoDB Atlas) ---
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)

# Updated to match the exact names from your Atlas image
user_db = mongo_client["NutritionAgent"]
logs_col = user_db["UserData"] 

# --- 2. RAG KNOWLEDGEBASE (DataStax AstraDB) ---
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

ASTRA_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

vector_store = AstraDBVectorStore(
    collection_name="indb_foods",
    embedding=embeddings,
    api_endpoint=ASTRA_ENDPOINT,
    token=ASTRA_TOKEN,
    namespace="default_keyspace"
)