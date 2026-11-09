"""
MediTwin AI — LangChain Structured Extraction
Uses LangChain with Gemini to extract medical observations from text.
"""

import os
import logging
from typing import List, Optional

from ingestion.validation import ExtractedObservation, ExtractionResult

logger = logging.getLogger(__name__)

# Extraction prompt template
EXTRACTION_PROMPT = """You are a medical document data extraction assistant.

Your task is to extract structured medical observations from the provided clinical document text.

RULES:
1. Extract ONLY information that is explicitly present in the text.
2. Do NOT invent, guess, or fabricate any medical values.
3. If a date cannot be determined, set observed_at to null.
4. If a unit cannot be determined, set unit to null.
5. If a reference range is mentioned, extract reference_low and reference_high.
6. Include the exact source snippet where each observation was found.
7. Set confidence between 0.0 and 1.0 based on how clearly the value was stated.
8. For test_code, use standard abbreviations if recognizable (e.g., HBA1C, FBS, CBC, HDL, LDL, TSH).

DOCUMENT TEXT (Page {page_number}):
---
{text}
---

Extract all medical test results and observations found in this text.
Return them as a JSON array of observation objects.
Each observation should have:
- test_name: Full name of the test
- test_code: Standard abbreviation (or null)
- value_numeric: Numeric value (or null if text-only)
- value_text: Text value (or null if numeric)
- unit: Unit of measurement (or null)
- reference_low: Lower reference range (or null)
- reference_high: Upper reference range (or null)
- observed_at: Date in YYYY-MM-DD format (or null)
- source_page: {page_number}
- source_snippet: The exact text snippet containing this result
- confidence: Your confidence in this extraction (0.0-1.0)

If the text contains no medical observations, return an empty array.
"""


def extract_observations_with_langchain(
    text: str,
    page_number: int = 1,
    document_date: str = None,
    api_key: str = None,
    model_name: str = "gemini-2.0-flash",
) -> ExtractionResult:
    """
    Extract structured medical observations from text using LangChain + Gemini.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        logger.error("No Gemini API key available.")
        return ExtractionResult(
            observations=[],
            extraction_notes="Extraction skipped: No Gemini API key configured."
        )

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        import json

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,  # Low temperature for factual extraction
        )

        prompt = EXTRACTION_PROMPT.format(
            text=text,
            page_number=page_number,
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        # Parse JSON from response
        # Try to find JSON array in the response
        observations = []
        try:
            # Look for JSON array
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                raw_obs = json.loads(json_str)
                for raw in raw_obs:
                    try:
                        obs = ExtractedObservation(**raw)
                        # If document_date is known and observation has no date
                        if obs.observed_at is None and document_date:
                            obs.observed_at = document_date
                        observations.append(obs)
                    except Exception as e:
                        logger.warning(f"Skipping invalid observation: {e}")
            else:
                logger.warning("No JSON array found in LLM response.")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")

        return ExtractionResult(
            observations=observations,
            document_date=document_date,
            extraction_notes=f"Extracted {len(observations)} observations from page {page_number}."
        )

    except Exception as e:
        logger.error(f"LangChain extraction error: {e}")
        return ExtractionResult(
            observations=[],
            extraction_notes=f"Extraction failed: {str(e)}"
        )


def extract_from_document(
    pages_text: list,
    document_date: str = None,
    api_key: str = None,
    model_name: str = "gemini-2.0-flash",
) -> ExtractionResult:
    """
    Extract observations from all pages of a document.

    Args:
        pages_text: List of (page_number, text) tuples
        document_date: Overall document date if known
        api_key: Gemini API key
        model_name: Gemini model to use
    """
    all_observations = []
    notes = []

    for page_num, text in pages_text:
        if not text or len(text.strip()) < 10:
            continue  # Skip empty/near-empty pages

        result = extract_observations_with_langchain(
            text=text,
            page_number=page_num,
            document_date=document_date,
            api_key=api_key,
            model_name=model_name,
        )
        all_observations.extend(result.observations)
        if result.extraction_notes:
            notes.append(result.extraction_notes)

    return ExtractionResult(
        observations=all_observations,
        document_date=document_date,
        extraction_notes=" | ".join(notes) if notes else None,
    )

