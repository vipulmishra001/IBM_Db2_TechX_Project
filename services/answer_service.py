"""
MediTwin AI — Answer Service
Generates evidence-grounded answers using Gemini.
All answers must be backed by retrieved Db2 records.
"""

import os
import json
import logging
from typing import Dict, List, Optional

from services.retrieval_service import RetrievalService, identify_test_code
from services.timeline_service import compute_metric_trend, format_trend_summary

logger = logging.getLogger(__name__)

ANSWER_PROMPT = """You are MediTwin AI, an evidence-based medical record assistant.

IMPORTANT RULES:
1. You are NOT a doctor. You do NOT diagnose diseases or recommend treatments.
2. You ONLY report what is recorded in the provided database evidence.
3. If the evidence is insufficient, say so clearly.
4. Always cite the source document and date for each value you mention.
5. Never invent or assume medical values not present in the evidence.
6. This is a demonstration system using synthetic patient data.

QUESTION: {question}

EVIDENCE FROM DATABASE:
{evidence_text}

TREND ANALYSIS:
{trend_text}

Generate a clear, concise answer based ONLY on the evidence above.
Include:
- The specific values found
- The dates of each measurement
- The source documents
- Any changes or trends (computed deterministically, shown above)

If insufficient evidence exists, respond:
"I could not find sufficient approved records to answer this question."
"""


class AnswerService:
    """Generates evidence-grounded answers to patient questions."""

    def __init__(self, repository, api_key: str = None,
                 model_name: str = "gemini-2.0-flash"):
        self.repo = repository
        self.retrieval = RetrievalService(repository)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = model_name

    def answer_question(self, patient_id: int, question: str) -> Dict:
        """
        Answer a patient question using Db2 evidence + Gemini generation.
        Returns structured response with answer, evidence, and sources.
        """
        # Step 1: Retrieve evidence from Db2
        evidence = self.retrieval.retrieve_evidence_for_question(
            patient_id=patient_id,
            question=question,
        )

        # Step 2: If no evidence, return insufficient evidence response
        if not evidence["sufficient_evidence"]:
            return {
                "answer": "I could not find sufficient approved records to answer this question.",
                "has_evidence": False,
                "evidence_cards": [],
                "sources": [],
                "test_code": evidence.get("test_code_identified"),
            }

        # Step 3: Compute deterministic trend
        test_code = evidence.get("test_code_identified")
        trend = {}
        trend_text = "No trend analysis available."
        if test_code:
            trend = compute_metric_trend(evidence["observations"], test_code)
            trend_text = format_trend_summary(trend)

        # Step 4: Build evidence text
        evidence_text = self._format_evidence_text(evidence["observations"])

        # Step 5: Generate answer with Gemini
        answer = self._generate_answer(question, evidence_text, trend_text)

        # Step 6: Build evidence cards
        evidence_cards = self._build_evidence_cards(evidence["observations"])

        return {
            "answer": answer,
            "has_evidence": True,
            "evidence_cards": evidence_cards,
            "sources": evidence["source_documents"],
            "test_code": test_code,
            "trend": trend,
            "observation_count": len(evidence["observations"]),
        }

    def _format_evidence_text(self, observations: List[Dict]) -> str:
        """Format observations into text for the LLM prompt."""
        if not observations:
            return "No records found."

        lines = []
        for i, obs in enumerate(observations, 1):
            val = obs.get("VALUE_NUMERIC") or obs.get("VALUE_TEXT", "N/A")
            unit = obs.get("UNIT", "")
            date_str = obs.get("OBSERVED_AT", "unknown date")
            source = obs.get("FILE_NAME", "unknown source")
            page = obs.get("SOURCE_PAGE", "")
            snippet = obs.get("SOURCE_SNIPPET", "")

            line = (
                f"Record {i}: {obs.get('TEST_NAME', 'Unknown')} = {val} {unit} "
                f"| Date: {date_str} | Source: {source}"
            )
            if page:
                line += f" (page {page})"
            if snippet:
                line += f' | Snippet: "{snippet}"'
            lines.append(line)

        return "\n".join(lines)

    def _generate_answer(self, question: str, evidence_text: str,
                          trend_text: str) -> str:
        """Generate answer using Gemini."""
        if not self.api_key:
            # Fallback: generate a deterministic answer without LLM
            return self._deterministic_answer(evidence_text, trend_text)

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.2,
            )

            prompt = ANSWER_PROMPT.format(
                question=question,
                evidence_text=evidence_text,
                trend_text=trend_text,
            )

            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content

        except Exception as e:
            logger.error(f"Gemini answer generation failed: {e}")
            return self._deterministic_answer(evidence_text, trend_text)

    def _deterministic_answer(self, evidence_text: str,
                               trend_text: str) -> str:
        """Fallback: return evidence and trend directly without LLM."""
        return (
            f"**Evidence from approved records:**\n\n{evidence_text}\n\n"
            f"**Trend analysis:**\n\n{trend_text}\n\n"
            f"*Note: This answer is based on deterministic analysis of database records. "
            f"Gemini API was not available for natural language generation.*"
        )

    def _build_evidence_cards(self, observations: List[Dict]) -> List[Dict]:
        """Build structured evidence cards for UI display."""
        cards = []
        for obs in observations:
            cards.append({
                "test_name": obs.get("TEST_NAME", "Unknown"),
                "value": obs.get("VALUE_NUMERIC") or obs.get("VALUE_TEXT", "N/A"),
                "unit": obs.get("UNIT", ""),
                "date": str(obs.get("OBSERVED_AT", "")),
                "source_file": obs.get("FILE_NAME", ""),
                "source_page": obs.get("SOURCE_PAGE"),
                "snippet": obs.get("SOURCE_SNIPPET", ""),
                "review_status": obs.get("REVIEW_STATUS", ""),
            })
        return cards

