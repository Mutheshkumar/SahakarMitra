"""
SahakarMitra Backend API.
Provides endpoints for text-based Q&A (/ask) and multilingual speech-based Q&A (/voice).
"""

import os
import shutil
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.rag_service import answer_question_with_rag
from services.voice_service import translate_audio_whisper, translate_text

app = FastAPI(
    title="SahakarMitra API",
    description="Multilingual AI Assistant for Sahakar Mitra Scheme and Cooperative Knowledge",
    version="1.0.0"
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Pydantic Request & Response Models
# ==========================================

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        description="The question in English or any language",
        examples=["What is the monthly stipend for the Sahakar Mitra internship?"]
    )


class AskResponse(BaseModel):
    question: str = Field(..., description="The submitted question")
    answer: str = Field(..., description="The factual answer synthesized by retrieval + LLM")
    cited_section: str = Field(..., description="Cited knowledge base section or legal act")


class VoiceResponse(BaseModel):
    question_text: str = Field(..., description="English transcription/translation from audio via Whisper")
    answer: str = Field(..., description="English answer generated from RAG /ask logic")
    cited_section: str = Field(..., description="Cited section name from the scheme documentation")
    translated_answer: str = Field(..., description="Answer translated back into the requested target language")


# ==========================================
# API Endpoints
# ==========================================

@app.get("/", summary="Health Check and API Info")
def root():
    return {
        "app": "SahakarMitra API",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "ask": "POST /ask",
            "voice": "POST /voice"
        }
    }


@app.post("/ask", response_model=AskResponse, summary="Text-based Question Answering")
def ask_question(request: AskRequest):
    """
    Accepts a question text, performs document retrieval across the Sahakar Mitra
    knowledge base, queries the LLM, and returns the answer with cited section.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question field cannot be empty."
        )

    rag_result = answer_question_with_rag(request.question.strip())
    
    return AskResponse(
        question=rag_result["question"],
        answer=rag_result["answer"],
        cited_section=rag_result["cited_section"]
    )


@app.post("/voice", response_model=VoiceResponse, summary="Voice-based Question Answering (Audio -> Whisper -> RAG -> Translation)")
async def voice_endpoint(
    audio: UploadFile = File(..., description="Uploaded audio file (wav, mp3, m4a, webm, ogg, etc.)"),
    lang: str = Form("ta", description="Target output language code (e.g., 'ta' for Tamil, 'hi' for Hindi, 'te' for Telugu)")
):
    """
    Accepts an uploaded audio file (multipart/form-data):
    1. Saves the audio file temporarily to disk.
    2. Runs OpenAI Whisper in 'translate' mode to extract English text.
    3. Reuses the /ask retrieval + LLM logic to generate an answer with citations.
    4. Translates the answer back into the requested language (default 'ta' for Tamil) using deep-translator.
    5. Returns JSON {question_text, answer, cited_section, translated_answer}.
    """
    if not audio.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file uploaded or invalid file name."
        )

    # Determine file extension for temporary file
    _, ext = os.path.splitext(audio.filename)
    if not ext:
        ext = ".wav"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_file_path = temp_file.name

    try:
        # Save uploaded stream to temporary file
        with temp_file as f:
            shutil.copyfileobj(audio.file, f)

        # 1. Transcribe & translate audio to English using OpenAI Whisper
        question_text = translate_audio_whisper(temp_file_path)

        if not question_text or not question_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract audio transcription."
            )

        # 2. Reuse the existing /ask retrieval + LLM logic
        rag_result = answer_question_with_rag(question_text)
        answer = rag_result["answer"]
        cited_section = rag_result["cited_section"]

        # 3. Translate the answer back into the requested language (default 'ta' for Tamil)
        target_language = lang if lang and lang.strip() else "ta"
        translated_answer = translate_text(answer, target_lang=target_language)

        # 4. Return structured JSON response
        return VoiceResponse(
            question_text=question_text,
            answer=answer,
            cited_section=cited_section,
            translated_answer=translated_answer
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing voice request: {str(e)}"
        )
    finally:
        # Safely clean up the temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError as err:
                print(f"[Warning] Failed to delete temporary file {temp_file_path}: {err}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
