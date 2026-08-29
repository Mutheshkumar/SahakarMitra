# SahakarMitra Backend API

A FastAPI backend powering multilingual AI assistance for the Sahakar Mitra scheme and cooperative advisory.

---

## Features

- **`POST /ask`**: Text-based Question & Answering with RAG retrieval over Sahakar Mitra scheme guidelines and cited section references.
- **`POST /voice`**: Voice-based Question & Answering:
  1. Accepts uploaded audio (`multipart/form-data`) along with an optional `lang` parameter (defaults to `"ta"` for Tamil).
  2. Saves the audio temporarily.
  3. Uses **OpenAI Whisper** in `translate` mode to transcribe and translate spoken speech directly into English.
  4. Reuses the `/ask` retrieval + LLM logic to query the knowledge base and synthesize answers.
  5. Translates the answer back into the requested language using **`deep-translator`** (`GoogleTranslator`).
  6. Safely cleans up temporary files and returns `{question_text, answer, cited_section, translated_answer}`.
- **`GET /`**: Health check and API information endpoint.

---

## Installation & Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Add your OpenAI API key in `.env`:
   ```env
   OPENAI_API_KEY=sk-...
   ```

3. **Start the API Server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## API Endpoints

### 1. `POST /voice` (Audio File Upload)

- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `audio` *(file, required)*: Uploaded audio file (`.wav`, `.mp3`, `.m4a`, `.ogg`, `.webm`, etc.)
  - `lang` *(form string, optional)*: Target output language code (default: `"ta"` for Tamil, `"hi"` for Hindi, `"te"` for Telugu, `"en"` for English, etc.)

#### Example `curl` Request:
```bash
curl -X POST "http://localhost:8000/voice" \
  -F "audio=@sample_query.wav;type=audio/wav" \
  -F "lang=ta"
```

#### Example JSON Response:
```json
{
  "question_text": "What is the monthly stipend for the Sahakar Mitra internship?",
  "answer": "Under the Sahakar Mitra Scheme, NCDC provides financial assistance in the form of a monthly stipend. Each selected intern receives a consolidated stipend of INR 10,000 per month for 4 months (totaling INR 40,000). (Refer to Section 3 - Financial Assistance & Monthly Stipend).",
  "cited_section": "Section 3 - Financial Assistance & Monthly Stipend",
  "translated_answer": "சககர் மித்ரா திட்டத்தின் கீழ், என்சிடிசி மாதாந்திர உதவித்தொகை வடிவில் நிதி உதவியை வழங்குகிறது. தேர்ந்தெடுக்கப்பட்ட ஒவ்வொரு பயிற்சிக்கும் 4 மாத காலத்திற்கு மாதத்திற்கு INR 10,000 ஒருங்கிணைந்த உதவித்தொகை வழங்கப்படுகிறது (மொத்தம் INR 40,000)."
}
```

---

### 2. `POST /ask` (Text-based Q&A)

- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "question": "What is the eligibility criteria for students?"
  }
  ```

#### Example JSON Response:
```json
{
  "question": "What is the eligibility criteria for students?",
  "answer": "Candidates eligible for Sahakar Mitra include professional graduates and post-graduates in disciplines such as Agriculture and Allied sectors, Agri-Business, Dairy, Fisheries, Forestry, Horticulture, Food Processing, IT, Management, and MBA.",
  "cited_section": "Section 2 - Eligibility Criteria & Target Candidates"
}
```

---

## Running Tests

Run the automated test suite with `pytest`:
```bash
pytest -v tests/
```
