"""
RAG (Retrieval-Augmented Generation) Service for SahakarMitra.
Provides document retrieval and LLM-powered answering with cited sections.
"""

import os
import re
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Pre-indexed knowledge base of Sahakar Mitra (NCDC Scheme on Internship Program & Cooperatives)
KNOWLEDGE_BASE = [
    {
        "section": "Section 1 - Overview & Objectives of Sahakar Mitra Scheme",
        "keywords": ["objective", "overview", "what is", "about", "purpose", "ncdc", "cooperative", "internship", "scheme", "goals"],
        "content": (
            "Sahakar Mitra is a Scheme on Internship Program (SIP) launched by the National Cooperative Development "
            "Corporation (NCDC), Ministry of Cooperation, Government of India. The primary objective is to provide "
            "young professionals with practical experience and hands-on learning in the cooperative sector while "
            "benefiting cooperatives from the innovative ideas and technical expertise of young professionals. It empowers "
            "youth to participate in rural economy and cooperative enterprise development."
        )
    },
    {
        "section": "Section 2 - Eligibility Criteria & Target Candidates",
        "keywords": ["eligibility", "eligible", "qualification", "degree", "agriculture", "who can apply", "criteria", "students", "graduates", "mba", "it"],
        "content": (
            "Candidates eligible for Sahakar Mitra include professional graduates and post-graduates in disciplines such as "
            "Agriculture and Allied sectors, Agri-Business, Dairy, Fisheries, Forestry, Horticulture, Food Processing, "
            "Information Technology, Computer Science, Finance, Law, Management, and MBA. Final year students awaiting final "
            "results may also be nominated by their designated educational institutions / universities."
        )
    },
    {
        "section": "Section 3 - Financial Assistance & Monthly Stipend",
        "keywords": ["stipend", "financial assistance", "salary", "allowance", "payment", "fund", "money", "amount", "monthly", "per month", "remuneration"],
        "content": (
            "Under the Sahakar Mitra Scheme, NCDC provides financial assistance in the form of a monthly stipend. Each "
            "selected intern receives a consolidated stipend of INR 10,000 per month for the duration of the 4-month "
            "internship period (totaling INR 40,000 for the completed internship tenure). No additional TA/DA is provided "
            "unless explicitly authorized by the sponsoring cooperative organization for specific field missions."
        )
    },
    {
        "section": "Section 4 - Internship Duration & Application Procedure",
        "keywords": ["duration", "period", "how to apply", "application", "procedure", "portal", "registration", "timeline", "months", "time"],
        "content": (
            "The standard duration of the Sahakar Mitra internship is four (4) months. Eligible applicants must register "
            "and submit their online applications through the official NCDC Sahakar Mitra web portal (https://www.ncdc.in). "
            "Applications require academic transcripts, recommendation/nomination letters from the university head, "
            "and choice of preferred cooperative operational domain."
        )
    },
    {
        "section": "Section 5 - Roles, Responsibilities & Deliverables",
        "keywords": ["role", "responsibility", "work", "duties", "mentor", "project", "report", "deliverables", "tasks"],
        "content": (
            "Interns are assigned to specific cooperatives, NCDC regional offices, or LINAC centers under the supervision "
            "of a designated mentor. Interns must undertake project work, field visits, market research, or business plan "
            "formulation. Upon completion, the intern must submit a comprehensive Project Report and presentation to NCDC."
        )
    },
    {
        "section": "Section 6 - Certification & Career Opportunities in Cooperatives",
        "keywords": ["certificate", "certification", "career", "job", "future", "completion", "benefits", "placement", "opportunities"],
        "content": (
            "Upon successful evaluation and submission of the project report, NCDC awards an official Sahakar Mitra "
            "Certificate of Internship. The practical experience equips young professionals for careers in primary agricultural "
            "credit societies (PACS), cooperative banks, farmer producer organizations (FPOs), and agri-business enterprises."
        )
    },
    {
        "section": "Section 7 - PACS Computerization & Cooperative Digital Initiatives",
        "keywords": ["pacs", "computerization", "digital", "technology", "software", "banking", "enterprise", "modernization"],
        "content": (
            "Primary Agricultural Credit Societies (PACS) computerization is a flagship national project to bring PACS onto an "
            "ERP-based common national software. Sahakar Mitra interns with IT and Management backgrounds assist PACS in digital "
            "data migration, member onboarding, inventory management, and digital services delivery."
        )
    }
]


def retrieve_relevant_sections(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Score knowledge base sections based on query term overlap and semantic keyword matching.
    """
    cleaned_query = re.sub(r"[^\w\s]", " ", query.lower())
    query_tokens = set(cleaned_query.split())

    scored_sections = []
    for item in KNOWLEDGE_BASE:
        score = 0
        # Keyword matches
        for kw in item["keywords"]:
            if kw in cleaned_query:
                score += 3
            else:
                kw_words = kw.split()
                if any(w in query_tokens for w in kw_words):
                    score += 1
        
        # Content word overlap
        content_words = set(re.sub(r"[^\w\s]", " ", item["content"].lower()).split())
        overlap = len(query_tokens.intersection(content_words))
        score += overlap * 0.5

        scored_sections.append({"item": item, "score": score})

    scored_sections.sort(key=lambda x: x["score"], reverse=True)
    results = [s["item"] for s in scored_sections[:top_k]]
    return results if results else [KNOWLEDGE_BASE[0]]


def answer_question_with_rag(query: str) -> Dict[str, Any]:
    """
    Core retrieval + LLM question-answering logic.
    Reused by both /ask and /voice endpoints.
    
    Returns:
        dict with:
            - question (str)
            - answer (str)
            - cited_section (str)
    """
    if not query or not query.strip():
        return {
            "question": "",
            "answer": "Please provide a valid question regarding Sahakar Mitra or cooperative schemes.",
            "cited_section": "N/A"
        }

    relevant_docs = retrieve_relevant_sections(query, top_k=2)
    top_doc = relevant_docs[0]
    cited_section = top_doc["section"]
    context_text = "\n\n".join([f"[{d['section']}]\n{d['content']}" for d in relevant_docs])

    openai_api_key = os.getenv("OPENAI_API_KEY")

    if openai_api_key and not openai_api_key.startswith("your_openai_"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            
            system_prompt = (
                "You are SahakarMitra AI, an authoritative, helpful assistant for the Sahakar Mitra "
                "Cooperative Internship Scheme (NCDC, Ministry of Cooperation, India).\n"
                "Answer the user's question clearly, concisely, and factually using ONLY the provided context.\n"
                "Explicitly cite the relevant section name in your answer."
            )
            
            user_prompt = (
                f"Context Information:\n{context_text}\n\n"
                f"User Question: {query}\n\n"
                "Provide a direct, accurate answer."
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=350
            )
            
            answer = response.choices[0].message.content.strip()
            return {
                "question": query,
                "answer": answer,
                "cited_section": cited_section
            }
        except Exception as e:
            # Fallback to local contextual synthesis if OpenAI API fails or is unreachable
            print(f"[RAG Service] OpenAI LLM call error: {e}. Falling back to rule-based contextual answer.")

    # High-quality fallback answer generated directly from the top retrieved knowledge base section
    answer = f"{top_doc['content']} (Refer to {cited_section})."
    
    return {
        "question": query,
        "answer": answer,
        "cited_section": cited_section
    }
