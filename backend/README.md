# SahakarMitra Backend

A Retrieval-Augmented Generation (RAG) API for querying the Tamil Nadu Cooperative Societies Act.

## Setup

1. **Create Virtual Environment (Optional but recommended)**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Create a `.env` file in the `backend` directory and add your OpenAI API Key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Initialize the Database**
   This script reads `tnsc_act_sections.json`, generates embeddings using `sentence-transformers`, and stores them locally in ChromaDB.
   ```bash
   python init_db.py
   ```

5. **Run the API Server**
   ```bash
   uvicorn main:app --reload
   ```

6. **Test the API**
   In a separate terminal, run the test script:
   ```bash
   python test_api.py
   ```
