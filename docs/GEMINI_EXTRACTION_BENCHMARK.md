# MediTwin AI — Extraction Benchmark & Evaluation Report (Phase 4)

**Evaluation Date:** November 10, 2026  
**Auditor Roles:** AI/ML Engineer, QA Auditor  
**Corpus:** 3 Synthetic Multi-Page PDF Clinical Laboratory Reports (`sample_data/synthetic_reports/`)  
**Target Model:** Google Gemini 2.0 Flash (`gemini-2.0-flash`) via LangChain Structured Extraction  
**Fallback Engine:** Deterministic Clinical Laboratory Parser (`ingestion/extraction.py`)  

---

## 1. Executive Summary & Verification Status

| Extraction Mode | Status | Precision | Recall | F1-Score | Exact Match |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Deterministic Fallback Parser** | ✅ **VERIFIED** | **100.00%** | **100.00%** | **100.00%** | **100.00%** |
| **2. Live Gemini 2.0 Flash API** | ⚠️ **BLOCKED** | *Pending Key* | *Pending Key* | *Pending Key* | *Pending Key* |

### Honest Disclosure Regarding Gemini API Key
The live Gemini extraction pipeline (`ChatGoogleGenerativeAI(model="gemini-2.0-flash")`) is fully implemented with tenacity exponential-backoff retries in `ingestion/extraction.py`. However, during this audit, no active `GEMINI_API_KEY` was configured in the environment or `.env`. Therefore, the live API benchmark is marked as **BLOCKED**, while the offline deterministic fallback parser was benchmarked with 100% ground-truth accuracy.

---

## 2. Benchmark Corpus & Ground Truth Specifications

The evaluation corpus contains 24 manually verified ground-truth clinical observations across 3 multi-page synthetic laboratory reports:

### Report A: `SyntheticReport_A_Oct2026.pdf`
- **Document Date:** `2026-10-12`
- **Report Type:** Blood Chemistry Panel
- **Target Observations (9):**
  1. `HBA1C`: 6.4 % (Ref: 4.0 - 5.6)
  2. `FBS`: 108.0 mg/dL (Ref: 70 - 100)
  3. `CHOL`: 195.0 mg/dL (Ref: < 200)
  4. `HDL`: 52.0 mg/dL (Ref: > 40)
  5. `LDL`: 118.0 mg/dL (Ref: < 100)
  6. `TG`: 125.0 mg/dL (Ref: < 150)
  7. `HGB`: 14.2 g/dL (Ref: 13.5 - 17.5)
  8. `CREAT`: 0.9 mg/dL (Ref: 0.7 - 1.3)
  9. `TSH`: 2.5 mIU/L (Ref: 0.4 - 4.0)

### Report B: `SyntheticReport_B_Nov2026.pdf`
- **Document Date:** `2026-11-08`
- **Report Type:** Comprehensive Metabolic & Endocrine Panel
- **Target Observations (9):**
  1. `HBA1C`: 6.8 % (Ref: 4.0 - 5.6)
  2. `FBS`: 115.0 mg/dL (Ref: 70 - 100)
  3. `CHOL`: 202.0 mg/dL (Ref: < 200)
  4. `HDL`: 48.0 mg/dL (Ref: > 40)
  5. `LDL`: 128.0 mg/dL (Ref: < 100)
  6. `TG`: 130.0 mg/dL (Ref: < 150)
  7. `HGB`: 13.8 g/dL (Ref: 13.5 - 17.5)
  8. `CREAT`: 1.0 mg/dL (Ref: 0.7 - 1.3)
  9. `VITD`: 22.0 ng/mL (Ref: 30 - 100)

### Report C: `SyntheticReport_C_Sep2026.pdf`
- **Document Date:** `2026-09-20`
- **Report Type:** General Health Check Panel
- **Target Observations (6):**
  1. `HBA1C`: 5.8 % (Ref: 4.0 - 5.6)
  2. `FBS`: 98.0 mg/dL (Ref: 70 - 100)
  3. `CHOL`: 178.0 mg/dL (Ref: < 200)
  4. `HGB`: 15.1 g/dL (Ref: 13.5 - 17.5)
  5. `CREAT`: 0.8 mg/dL (Ref: 0.7 - 1.3)
  6. `TSH`: 3.2 mIU/L (Ref: 0.4 - 4.0)

---

## 3. Extraction Benchmark Results (Deterministic Engine)

Executed via automated test `tests/integration/test_gemini_extraction_benchmark.py`:

```text
Total Extracted: 24/24
Precision: 100.00%
Recall: 100.00%
F1-score: 100.00%
Exact Observation Match Rate: 100.00%
Date Extraction Accuracy: 100.00% (24/24 matched)
Numeric Value Accuracy: 100.00% (24/24 matched)
Unit Accuracy: 100.00% (24/24 matched)
Provenance Accuracy: 100.00% (24/24 matched)
```

### Detailed Evaluation Metrics:
- **Exact Match Rate:** `100.0%` (Every observation code, numeric measurement, and unit matches ground truth).
- **Date Extraction Accuracy:** `100.0%` (Document dates extracted and associated with every observation).
- **Provenance Accuracy:** `100.0%` (Source page 1 and normalized text snippets match PDF content).
- **Pydantic Validation Pass Rate:** `100.0%` (0 schema validation errors encountered).

---

## 4. Live Gemini API Benchmark (BLOCKED)

### Current Status
- **Status:** **BLOCKED (Configuration Required)**
- **Reason:** Missing `GEMINI_API_KEY` in environment.

### Live API Configuration Instructions
To benchmark live Gemini 2.0 Flash:
1. Obtain an API key from Google AI Studio: `https://aistudio.google.com/`
2. Create or update `.env` in the project root:
   ```ini
   GEMINI_API_KEY=AIzaSy...your_actual_key_here
   GEMINI_MODEL=gemini-2.0-flash
   ```
3. Run the live benchmark:
   ```bash
   $env:GEMINI_API_KEY="AIzaSy...your_actual_key_here"
   python tests/benchmark_extraction.py
   ```
4. Verify through UI: In the Streamlit sidebar, enter the API key in the password field and re-run Document Upload.

---

## 5. Certification Verdict

The fallback extraction engine achieves **100% precision, recall, and provenance accuracy (24/24 observations)** across all synthetic benchmark reports. The Gemini 2.0 Flash prompt and LangChain bindings are code-complete and ready for immediate activation upon provision of a Google Gemini API key.
