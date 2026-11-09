"""
MediTwin AI — Retrieval Service
Parameterized Db2 query templates for evidence retrieval.
The model NEVER generates arbitrary SQL.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Common test code mappings for question parsing
TEST_CODE_ALIASES = {
    "hba1c": "HBA1C",
    "hemoglobin a1c": "HBA1C",
    "glycated hemoglobin": "HBA1C",
    "haemoglobin": "HGB",
    "hemoglobin": "HGB",
    "hgb": "HGB",
    "fasting blood sugar": "FBS",
    "fbs": "FBS",
    "fasting glucose": "FBS",
    "blood glucose": "FBS",
    "glucose": "FBS",
    "cholesterol": "CHOL",
    "total cholesterol": "CHOL",
    "hdl": "HDL",
    "ldl": "LDL",
    "triglycerides": "TG",
    "triglyceride": "TG",
    "creatinine": "CREAT",
    "urea": "UREA",
    "bun": "BUN",
    "tsh": "TSH",
    "thyroid": "TSH",
    "wbc": "WBC",
    "white blood cell": "WBC",
    "rbc": "RBC",
    "red blood cell": "RBC",
    "platelet": "PLT",
    "platelets": "PLT",
    "blood pressure": "BP",
    "systolic": "BP_SYS",
    "diastolic": "BP_DIA",
    "bmi": "BMI",
    "weight": "WEIGHT",
    "height": "HEIGHT",
    "vitamin d": "VITD",
    "vitamin b12": "VITB12",
    "iron": "IRON",
    "ferritin": "FERR",
    "calcium": "CA",
    "potassium": "K",
    "sodium": "NA",
    "alt": "ALT",
    "ast": "AST",
    "sgpt": "ALT",
    "sgot": "AST",
    "bilirubin": "BILI",
    "albumin": "ALB",
    "uric acid": "URIC",
    "esr": "ESR",
    "crp": "CRP",
}


def identify_test_code(question: str) -> Optional[str]:
    """
    Identify the test code from a natural language question.
    Uses keyword matching — NOT LLM-generated SQL.
    """
    question_lower = question.lower()
    for alias, code in TEST_CODE_ALIASES.items():
        if alias in question_lower:
            return code
    return None


def identify_test_name_keyword(question: str) -> Optional[str]:
    """Extract a potential test name keyword from the question."""
    question_lower = question.lower()
    for alias in TEST_CODE_ALIASES.keys():
        if alias in question_lower:
            return alias
    return None


class RetrievalService:
    """
    Retrieves evidence from Db2 using pre-defined parameterized queries.
    """

    def __init__(self, repository):
        self.repo = repository

    def get_latest_for_metric(self, patient_id: int,
                               test_code: str) -> Dict:
        """Get the most recent approved observation for a metric."""
        obs = self.repo.get_latest_observation(patient_id, test_code)
        if obs:
            return {
                "found": True,
                "observation": obs,
                "summary": (
                    f"Latest {obs.get('TEST_NAME', test_code)}: "
                    f"{obs.get('VALUE_NUMERIC', 'N/A')} {obs.get('UNIT', '')} "
                    f"on {obs.get('OBSERVED_AT', 'unknown date')} "
                    f"(Source: {obs.get('FILE_NAME', 'unknown')})"
                ),
            }
        return {
            "found": False,
            "summary": f"No approved observations found for {test_code}.",
        }

    def get_metric_history(self, patient_id: int, test_code: str,
                           start_date: str = None,
                           end_date: str = None) -> Dict:
        """Get all approved observations for a metric."""
        observations = self.repo.get_approved_observations(
            patient_id=patient_id,
            test_code=test_code,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "found": len(observations) > 0,
            "count": len(observations),
            "observations": observations,
        }

    def search_by_keyword(self, patient_id: int,
                           keyword: str) -> Dict:
        """Search observations by test name keyword."""
        observations = self.repo.search_observations_by_keyword(
            patient_id=patient_id,
            keyword=keyword,
        )
        return {
            "found": len(observations) > 0,
            "count": len(observations),
            "observations": observations,
        }

    def get_all_metrics(self, patient_id: int) -> List[Dict]:
        """Get all distinct test codes for a patient."""
        return self.repo.get_distinct_test_codes(patient_id)

    def retrieve_evidence_for_question(self, patient_id: int,
                                        question: str) -> Dict:
        """
        Main entry point: retrieve Db2 evidence to answer a question.
        Uses keyword matching and parameterized queries — NEVER generated SQL.
        """
        test_code = identify_test_code(question)
        keyword = identify_test_name_keyword(question)

        evidence = {
            "question": question,
            "patient_id": patient_id,
            "test_code_identified": test_code,
            "keyword_identified": keyword,
            "observations": [],
            "source_documents": [],
            "sufficient_evidence": False,
        }

        # Try by test code first
        if test_code:
            result = self.get_metric_history(patient_id, test_code)
            if result["found"]:
                evidence["observations"] = result["observations"]
                evidence["sufficient_evidence"] = True

        # Fallback to keyword search
        if not evidence["sufficient_evidence"] and keyword:
            result = self.search_by_keyword(patient_id, keyword)
            if result["found"]:
                evidence["observations"] = result["observations"]
                evidence["sufficient_evidence"] = True

        # Build source references
        sources_seen = set()
        for obs in evidence["observations"]:
            fname = obs.get("FILE_NAME", "")
            if fname and fname not in sources_seen:
                sources_seen.add(fname)
                evidence["source_documents"].append({
                    "file_name": fname,
                    "page": obs.get("SOURCE_PAGE"),
                    "snippet": obs.get("SOURCE_SNIPPET", ""),
                })

        return evidence

