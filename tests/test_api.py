"""
Comprehensive test suite for SahakarMitra FastAPI application.
Tests /ask and /voice endpoints and RAG/Voice services.
"""

import io
import os
import pytest
from fastapi.testclient import TestClient
from main import app
from services.rag_service import retrieve_relevant_sections, answer_question_with_rag
from services.voice_service import translate_text, normalize_language_code

client = TestClient(app)


def test_root_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "SahakarMitra API"
    assert data["status"] == "healthy"
    assert "voice" in data["endpoints"]


def test_ask_endpoint_valid_question():
    payload = {"question": "What is the monthly stipend for Sahakar Mitra?"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data
    assert "cited_section" in data
    assert "10,000" in data["answer"] or "Stipend" in data["cited_section"]
    assert "Section 3" in data["cited_section"]


def test_ask_endpoint_empty_question():
    payload = {"question": "   "}
    response = client.post("/ask", json=payload)
    assert response.status_code == 400


def test_voice_endpoint_default_tamil():
    # Simulate an audio file upload (e.g. dummy .wav file)
    dummy_wav_bytes = b"RIFF....WAVEfmt ....data...."
    audio_file = ("test_audio.wav", io.BytesIO(dummy_wav_bytes), "audio/wav")
    
    response = client.post(
        "/voice",
        files={"audio": audio_file}
        # lang omitted, defaults to "ta"
    )
    assert response.status_code == 200
    data = response.json()

    # Validate exact required JSON keys
    assert "question_text" in data
    assert "answer" in data
    assert "cited_section" in data
    assert "translated_answer" in data

    assert len(data["question_text"]) > 0
    assert len(data["answer"]) > 0
    assert len(data["cited_section"]) > 0
    assert len(data["translated_answer"]) > 0


def test_voice_endpoint_custom_language_hindi():
    dummy_mp3_bytes = b"ID3\x03\x00\x00\x00\x00\x00\x00"
    audio_file = ("sample_query.mp3", io.BytesIO(dummy_mp3_bytes), "audio/mpeg")
    
    response = client.post(
        "/voice",
        files={"audio": audio_file},
        data={"lang": "hi"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "question_text" in data
    assert "answer" in data
    assert "cited_section" in data
    assert "translated_answer" in data
    assert len(data["translated_answer"]) > 0


def test_voice_endpoint_english_language():
    dummy_m4a_bytes = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00"
    audio_file = ("query.m4a", io.BytesIO(dummy_m4a_bytes), "audio/m4a")
    
    response = client.post(
        "/voice",
        files={"audio": audio_file},
        data={"lang": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["translated_answer"] == data["answer"]


def test_rag_service_retrieval_and_answer():
    res = answer_question_with_rag("What are the eligibility criteria for students?")
    assert "Section 2" in res["cited_section"]
    assert "eligible" in res["answer"].lower() or "graduates" in res["answer"].lower()


def test_voice_service_normalize_language_code():
    assert normalize_language_code("tamil") == "ta"
    assert normalize_language_code("HINDI") == "hi"
    assert normalize_language_code("ta") == "ta"
    assert normalize_language_code("") == "ta"
