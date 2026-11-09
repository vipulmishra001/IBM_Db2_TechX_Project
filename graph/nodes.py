"""
MediTwin AI — LangGraph Workflow Nodes
Each function is a node in the LangGraph state machine.
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

from graph.state import MediTwinState
from ingestion.pdf_parser import parse_document, validate_file
from ingestion.extraction import extract_from_document
from ingestion.validation import ExtractedObservation

logger = logging.getLogger(__name__)


def classify_request(state: dict) -> dict:
    """Node 1: Classify the incoming request as upload or question."""
    s = state.copy()
    raw = s.get("raw_input", "")

    if s.get("file_bytes") is not None:
        s["request_type"] = "upload"
    elif raw.strip():
        s["request_type"] = "question"
        s["question"] = raw
    else:
        s["request_type"] = "unknown"
        s["error"] = "No input provided."

    s["current_node"] = "classify_request"
    s["completed_nodes"] = s.get("completed_nodes", []) + ["classify_request"]
    return s


def parse_document_node(state: dict) -> dict:
    """Node 2: Parse uploaded document (PDF/TXT)."""
    s = state.copy()
    s["current_node"] = "parse_document"

    file_name = s.get("file_name", "unknown")
    file_bytes = s.get("file_bytes")

    if not file_bytes:
        s["error"] = "No file data to parse."
        s["parse_status"] = "FAILED"
        return s

    # Validate file
    is_valid, err = validate_file(file_name, file_bytes)
    if not is_valid:
        s["error"] = err
        s["parse_status"] = "FAILED"
        return s

    # Parse document
    result = parse_document(file_name, file_bytes)
    s["parsed_text"] = result.full_text
    s["pages"] = [{"page_number": p.page_number, "text": p.text, "char_count": p.char_count}
                  for p in result.pages]
    s["parse_status"] = result.parse_status
    if result.error_message:
        s["parse_error"] = result.error_message

    s["completed_nodes"] = s.get("completed_nodes", []) + ["parse_document"]
    # Remove file_bytes from state to reduce memory
    s["file_bytes"] = None
    return s


def extract_observations_node(state: dict) -> dict:
    """Node 3: Extract structured observations using LangChain + Gemini."""
    s = state.copy()
    s["current_node"] = "extract_observations"

    if s.get("parse_status") != "PARSED":
        s["error"] = f"Cannot extract: document parse status is {s.get('parse_status')}"
        return s

    pages = s.get("pages", [])
    if not pages:
        s["error"] = "No pages to extract from."
        return s

    pages_text = [(p["page_number"], p["text"]) for p in pages]

    api_key = os.environ.get("GEMINI_API_KEY", "")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    result = extract_from_document(
        pages_text=pages_text,
        api_key=api_key,
        model_name=model_name,
    )

    s["extracted_observations"] = [obs.model_dump() for obs in result.observations]
    s["extraction_notes"] = result.extraction_notes

    s["completed_nodes"] = s.get("completed_nodes", []) + ["extract_observations"]
    return s


def validate_extraction_node(state: dict) -> dict:
    """Node 4: Validate extracted observations and flag issues."""
    s = state.copy()
    s["current_node"] = "validate_extraction"

    observations = s.get("extracted_observations", [])
    validation_errors = []

    for i, obs_dict in enumerate(observations):
        try:
            obs = ExtractedObservation(**obs_dict)
            if obs.needs_review:
                for reason in obs.review_reasons:
                    validation_errors.append(f"Observation {i+1} ({obs.test_name}): {reason}")
        except Exception as e:
            validation_errors.append(f"Observation {i+1}: Validation error - {str(e)}")

    s["validation_errors"] = validation_errors
    s["awaiting_review"] = True  # Always require human review
    s["completed_nodes"] = s.get("completed_nodes", []) + ["validate_extraction"]
    return s


def human_review_gate(state: dict) -> dict:
    """Node 5: Human review checkpoint. Marks state as awaiting review."""
    s = state.copy()
    s["current_node"] = "human_review_gate"
    s["awaiting_review"] = True
    s["completed_nodes"] = s.get("completed_nodes", []) + ["human_review_gate"]
    return s


def persist_to_db2_node(state: dict) -> dict:
    """Node 6: Save approved observations to IBM Db2."""
    s = state.copy()
    s["current_node"] = "persist_to_db2"

    # This node is called after human review
    review_decisions = s.get("review_decisions", [])
    saved_count = 0

    # In the actual workflow, this is handled by the UI layer
    # which calls the repository directly after review
    s["observations_saved"] = saved_count
    s["completed_nodes"] = s.get("completed_nodes", []) + ["persist_to_db2"]
    return s


def retrieve_patient_records(state: dict) -> dict:
    """Node 7: Retrieve patient records from Db2 for Q&A."""
    s = state.copy()
    s["current_node"] = "retrieve_patient_records"
    # Record retrieval is handled by the retrieval service
    s["completed_nodes"] = s.get("completed_nodes", []) + ["retrieve_patient_records"]
    return s


def build_timeline_node(state: dict) -> dict:
    """Node 8: Build patient timeline from approved observations."""
    s = state.copy()
    s["current_node"] = "build_timeline"
    s["completed_nodes"] = s.get("completed_nodes", []) + ["build_timeline"]
    return s


def retrieve_evidence_node(state: dict) -> dict:
    """Node 9: Retrieve evidence for answering a question."""
    s = state.copy()
    s["current_node"] = "retrieve_evidence"
    s["completed_nodes"] = s.get("completed_nodes", []) + ["retrieve_evidence"]
    return s


def generate_answer_node(state: dict) -> dict:
    """Node 10: Generate an evidence-grounded answer using Gemini."""
    s = state.copy()
    s["current_node"] = "generate_answer"
    s["completed_nodes"] = s.get("completed_nodes", []) + ["generate_answer"]
    return s


def safety_check_node(state: dict) -> dict:
    """Node 11: Safety check on generated response."""
    s = state.copy()
    s["current_node"] = "safety_check"

    answer = s.get("generated_answer", "")
    safety_issues = []

    # Check for diagnostic language
    diagnostic_terms = [
        "you have", "you are diagnosed", "your diagnosis is",
        "you should take", "I recommend", "prescription",
        "you need treatment", "you must see a doctor"
    ]
    for term in diagnostic_terms:
        if term.lower() in answer.lower():
            safety_issues.append(f"Response contains potentially diagnostic language: '{term}'")

    if safety_issues:
        s["safety_passed"] = False
        s["safety_notes"] = "; ".join(safety_issues)
        # Add disclaimer
        s["generated_answer"] = (
            answer +
            "\n\n⚠️ **Note:** This is a demonstration system using synthetic data. "
            "It does not provide medical diagnosis or treatment advice."
        )
    else:
        s["safety_passed"] = True

    s["completed_nodes"] = s.get("completed_nodes", []) + ["safety_check"]
    return s


def finalize_response_node(state: dict) -> dict:
    """Node 12: Finalize the response."""
    s = state.copy()
    s["current_node"] = "finalize_response"

    if s.get("error"):
        s["final_response"] = f"Error: {s['error']}"
    elif s.get("request_type") == "upload":
        obs_count = len(s.get("extracted_observations", []))
        s["final_response"] = (
            f"Document processed. {obs_count} observations extracted. "
            f"Please review and approve observations."
        )
    elif s.get("request_type") == "question":
        s["final_response"] = s.get("generated_answer", "No answer generated.")
    else:
        s["final_response"] = "Request could not be processed."

    s["completed_nodes"] = s.get("completed_nodes", []) + ["finalize_response"]
    return s

