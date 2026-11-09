"""
Benchmark script to evaluate extraction accuracy on all 3 synthetic reports.
"""

import os
import fitz
from ingestion.extraction import extract_from_document

sample_dir = 'sample_data/synthetic_reports'
reports = [
    ('SyntheticReport_A_Oct2026.pdf', 9),
    ('SyntheticReport_B_Nov2026.pdf', 9),
    ('SyntheticReport_C_Sep2026.pdf', 6),
]

total_expected = sum(r[1] for r in reports)
total_extracted = 0

print("=== BENCHMARKING EXTRACTION ACCURACY ACROSS 3 SYNTHETIC REPORTS ===\n")

for fname, expected_count in reports:
    fpath = os.path.join(sample_dir, fname)
    doc = fitz.open(fpath)
    pages_text = [(i + 1, doc[i].get_text()) for i in range(len(doc))]

    result = extract_from_document(pages_text)
    actual_count = len(result.observations)
    total_extracted += actual_count

    print(f"Document: {fname}")
    print(f"  Expected: {expected_count} | Extracted: {actual_count}")
    print(f"  Identified Date: {result.document_date}")
    for obs in result.observations:
        print(f"    - {obs.test_name} ({obs.test_code}): {obs.value_numeric} {obs.unit} (ref: {obs.reference_low} - {obs.reference_high}) | snippet: '{obs.source_snippet}'")
    print()

accuracy = (total_extracted / total_expected) * 100
print(f"TOTAL: {total_extracted}/{total_expected} observations successfully parsed ({accuracy:.1f}% accuracy)")
