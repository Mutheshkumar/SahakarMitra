import os
import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

app = FastAPI(title="SahakarMitra API", description="RAG API for TNSC Act")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models and clients
db_client = None
collection = None
embedding_model = None
openai_client = None

DB_DIR = "./chroma_data"
COLLECTION_NAME = "tnsc_act"

class QuestionRequest(BaseModel):
    question: str

class RetrievedSection(BaseModel):
    section: str
    title: str
    chapter: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    cited_section: Optional[str]
    retrieved_sections: List[RetrievedSection]

@app.on_event("startup")
async def startup_event():
    global db_client, collection, embedding_model, openai_client
    
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY environment variable is not set!")
        
    # Using Gemini's OpenAI compatible endpoint since an AI Studio key was provided
    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    print("Initializing ChromaDB client...")
    db_client = chromadb.PersistentClient(path=DB_DIR)
    try:
        collection = db_client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"WARNING: ChromaDB collection '{COLLECTION_NAME}' not found. Did you run init_db.py?")
        
    print("Loading embedding model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Startup complete.")

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(req: QuestionRequest):
    if not collection:
        raise HTTPException(status_code=500, detail="Database collection not initialized.")
        
    # Generate embedding for the question
    query_embedding = embedding_model.encode([req.question]).tolist()
    
    # Retrieve top 3 matching sections
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3
    )
    
    retrieved = []
    context_texts = []
    
    if results and results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            meta = results['metadatas'][0][i]
            text = results['documents'][0][i]
            
            section_info = RetrievedSection(
                section=meta['section'],
                title=meta['title'],
                chapter=meta['chapter'],
                text=text
            )
            retrieved.append(section_info)
            context_texts.append(f"Section {meta['section']} ({meta['title']}): {text}")
            
    context_block = "\n\n".join(context_texts)
    
    system_prompt = f"""
    You are an expert legal assistant for the Tamil Nadu Cooperative Societies Act.
    You will be provided with excerpts from the Act and a user's question.
    
    RULES:
    1. Answer ONLY using the provided sections below.
    2. ALWAYS state the exact section number cited in your answer.
    3. If the provided sections do not contain the answer, you MUST output exactly: "This isn't covered in the Tamil Nadu Cooperative Societies Act."
    
    PROVIDED SECTIONS:
    {context_block}
    """
    
    try:
        completion = openai_client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.question}
            ],
            temperature=0
        )
        answer_text = completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # Attempt to extract cited section roughly for structured JSON
    cited_section = None
    if answer_text != "This isn't covered in the Tamil Nadu Cooperative Societies Act.":
        if retrieved:
             cited_section = retrieved[0].section

    return AnswerResponse(
        answer=answer_text,
        cited_section=cited_section,
        retrieved_sections=retrieved
    )
