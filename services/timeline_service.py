"""
MediTwin AI — Timeline Service
Builds chronological patient timelines and computes metric trends.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def build_patient_timeline(observations: List[Dict],
                            documents: List[Dict] = None) -> List[Dict]:
    """
    Build a chronological timeline from approved observations and documents.
    Returns sorted list of timeline events.
    """
    timeline = []

    # Add observation events
    for obs in observations:
        observed_at = obs.get("OBSERVED_AT") or obs.get("observed_at")
        if observed_at:
            if isinstance(observed_at, str):
                try:
                    dt = datetime.strptime(observed_at, "%Y-%m-%d")
                except ValueError:
                    dt = datetime.now()
            else:
                dt = observed_at

            timeline.append({
                "date": dt,
                "date_str": dt.strftime("%Y-%m-%d") if isinstance(dt, datetime) else str(observed_at),
                "type": "observation",
                "title": obs.get("TEST_NAME") or obs.get("test_name", "Unknown Test"),
                "value": obs.get("VALUE_NUMERIC") or obs.get("value_numeric"),
                "value_text": obs.get("VALUE_TEXT") or obs.get("value_text"),
                "unit": obs.get("UNIT") or obs.get("unit", ""),
                "source": obs.get("FILE_NAME") or obs.get("file_name", ""),
                "page": obs.get("SOURCE_PAGE") or obs.get("source_page"),
                "snippet": obs.get("SOURCE_SNIPPET") or obs.get("source_snippet", ""),
                "observation_id": obs.get("OBSERVATION_ID") or obs.get("observation_id"),
            })

    # Add document upload events
    if documents:
        for doc in documents:
            uploaded_at = doc.get("UPLOADED_AT") or doc.get("uploaded_at")
            if uploaded_at:
                if isinstance(uploaded_at, str):
                    try:
                        dt = datetime.strptime(uploaded_at[:19], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt = datetime.now()
                else:
                    dt = uploaded_at

                timeline.append({
                    "date": dt,
                    "date_str": dt.strftime("%Y-%m-%d"),
                    "type": "document_upload",
                    "title": f"Document: {doc.get('FILE_NAME') or doc.get('file_name', 'Unknown')}",
                    "value": None,
                    "unit": "",
                    "source": doc.get("FILE_NAME") or doc.get("file_name", ""),
                    "page": None,
                    "snippet": "",
                })

    # Sort chronologically
    timeline.sort(key=lambda x: x["date"], reverse=True)
    return timeline


def compute_metric_trend(observations: List[Dict],
                          test_code: str) -> Dict:
    """
    Compute trend statistics for a specific metric.
    Only uses approved observations with compatible units.
    """
    # Filter to matching test code
    matching = [
        obs for obs in observations
        if (obs.get("TEST_CODE") or obs.get("test_code", "")).upper() == test_code.upper()
        and (obs.get("VALUE_NUMERIC") or obs.get("value_numeric")) is not None
    ]

    if not matching:
        return {
            "test_code": test_code,
            "count": 0,
            "message": "No approved observations found for this metric."
        }

    # Sort by date
    matching.sort(key=lambda x: str(x.get("OBSERVED_AT") or x.get("observed_at", "")))

    # Check unit compatibility
    units = set()
    for obs in matching:
        unit = obs.get("UNIT") or obs.get("unit")
        if unit:
            units.add(unit.strip())

    if len(units) > 1:
        return {
            "test_code": test_code,
            "count": len(matching),
            "message": f"Cannot compare: incompatible units found ({', '.join(units)}).",
            "units": list(units),
        }

    # Compute statistics
    values = [float(obs.get("VALUE_NUMERIC") or obs.get("value_numeric")) for obs in matching]
    unit = units.pop() if units else ""

    first_obs = matching[0]
    last_obs = matching[-1]
    first_val = values[0]
    last_val = values[-1]

    abs_diff = last_val - first_val
    pct_diff = None
    if first_val != 0:
        pct_diff = round((abs_diff / first_val) * 100, 2)

    return {
        "test_code": test_code,
        "test_name": first_obs.get("TEST_NAME") or first_obs.get("test_name", test_code),
        "count": len(matching),
        "unit": unit,
        "first_value": first_val,
        "first_date": str(first_obs.get("OBSERVED_AT") or first_obs.get("observed_at", "")),
        "first_source": first_obs.get("FILE_NAME") or first_obs.get("file_name", ""),
        "latest_value": last_val,
        "latest_date": str(last_obs.get("OBSERVED_AT") or last_obs.get("observed_at", "")),
        "latest_source": last_obs.get("FILE_NAME") or last_obs.get("file_name", ""),
        "absolute_change": round(abs_diff, 4),
        "percentage_change": pct_diff,
        "min_value": min(values),
        "max_value": max(values),
        "all_values": [
            {
                "date": str(obs.get("OBSERVED_AT") or obs.get("observed_at", "")),
                "value": float(obs.get("VALUE_NUMERIC") or obs.get("value_numeric")),
                "source": obs.get("FILE_NAME") or obs.get("file_name", ""),
                "page": obs.get("SOURCE_PAGE") or obs.get("source_page"),
            }
            for obs in matching
        ],
    }


def format_trend_summary(trend: Dict) -> str:
    """Format a trend analysis into a human-readable summary."""
    if trend.get("count", 0) == 0:
        return trend.get("message", "No data available.")

    if "message" in trend and "incompatible" in trend.get("message", "").lower():
        return trend["message"]

    name = trend.get("test_name", trend["test_code"])
    unit = trend.get("unit", "")
    count = trend["count"]

    if count == 1:
        return (
            f"Only one approved {name} observation found: "
            f"{trend['first_value']} {unit} on {trend['first_date']} "
            f"(Source: {trend['first_source']})"
        )

    parts = [
        f"**{name}** — {count} approved observations",
        f"• First recorded: {trend['first_value']} {unit} on {trend['first_date']} ({trend['first_source']})",
        f"• Latest recorded: {trend['latest_value']} {unit} on {trend['latest_date']} ({trend['latest_source']})",
        f"• Absolute change: {trend['absolute_change']:+.4g} {unit}",
    ]
    if trend.get("percentage_change") is not None:
        parts.append(f"• Percentage change: {trend['percentage_change']:+.2f}%")
    if count > 2:
        parts.append(f"• Range: {trend['min_value']} – {trend['max_value']} {unit}")

    return "\n".join(parts)

