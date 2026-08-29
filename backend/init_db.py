import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os

DB_DIR = "./chroma_data"
JSON_FILE = "tnsc_act_sections.json"
COLLECTION_NAME = "tnsc_act"

def main():
    print("Loading data from JSON...")
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found.")
        return
        
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        sections = json.load(f)
        
    print(f"Loaded {len(sections)} sections.")
    
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # Create or get collection
    try:
        collection = client.create_collection(name=COLLECTION_NAME)
        print("Created new collection.")
    except Exception:
        collection = client.get_collection(name=COLLECTION_NAME)
        print("Using existing collection.")
        
    print("Loading sentence transformer model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating embeddings and inserting into ChromaDB...")
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for item in sections:
        sec_id = item["section"]
        text = item["text"]
        
        ids.append(f"sec_{sec_id}")
        documents.append(text)
        metadatas.append({
            "section": sec_id,
            "title": item["title"],
            "chapter": item["chapter"]
        })
        
    # Generate embeddings in batch
    encoded = model.encode(documents).tolist()
    
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=encoded,
        metadatas=metadatas
    )
    
    print(f"Successfully upserted {len(ids)} items into ChromaDB at {DB_DIR}")

if __name__ == "__main__":
    main()
