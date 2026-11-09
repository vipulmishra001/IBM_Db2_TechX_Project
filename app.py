"""
MediTwin AI — Complete Agentic Healthcare Record Intelligence Platform
IBM Db2Hack 2026 Submission
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Load settings
from config.settings import app_settings, DISCLAIMER, gemini_settings
from db.connection import get_db2_connection, test_connection
from db.repository import Db2Repository
from db.seed_demo_data import seed_patients
from ingestion.pdf_parser import parse_document, validate_file
from ingestion.extraction import extract_from_document
from ingestion.validation import ExtractedObservation
from services.timeline_service import build_patient_timeline, compute_metric_trend, format_trend_summary
from services.retrieval_service import RetrievalService
from services.answer_service import AnswerService
from services.audit_service import AuditService

# Page configuration
st.set_page_config(
    page_title="MediTwin AI — Healthcare Record Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for medical technology styling
st.markdown("""
<style>
    /* Professional Medical Tech Theme */
    :root {
        --primary: #0A2540;
        --secondary: #0066CC;
        --accent: #00A3A6;
        --background: #F8FAFC;
        --card-bg: #FFFFFF;
        --text-primary: #1A202C;
        --text-secondary: #4A5568;
        --border: #E2E8F0;
        --success: #38A169;
        --warning: #DD6B20;
        --danger: #E53E3E;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    h1, h2, h3 {
        color: #0A2540 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Metric card */
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0066CC;
        margin: 0.3rem 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #4A5568;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Evidence card */
    .evidence-card {
        background: white;
        border-left: 4px solid #0066CC;
        border: 1px solid #E2E8F0;
        border-left-width: 4px;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    /* Status badge */
    .badge-approved {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-pending {
        background-color: #FEF08A;
        color: #713F12;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-rejected {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Disclaimer banner */
    .disclaimer-banner {
        background: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #92400E;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def get_repo():
    """Get or initialize repository."""
    conn = get_db2_connection()
    return Db2Repository(conn)


def get_audit():
    return AuditService(get_repo())


def get_answer_svc():
    return AnswerService(get_repo(), api_key=gemini_settings.api_key)


# Initialize DB connection on start
if "db_connected" not in st.session_state:
    conn = get_db2_connection()
    st.session_state.db_connected = conn.connect()
    if st.session_state.db_connected:
        schema_path = os.path.join(os.path.dirname(__file__), "db", "schema.sql")
        conn.initialize_schema(schema_path)
        seed_patients(Db2Repository(conn))


# ================================================================
# SIDEBAR
# ================================================================

with st.sidebar:
    st.markdown("### 🧬 MediTwin AI")
    st.markdown("**Healthcare Record Intelligence**")
    st.caption("IBM Db2Hack 2026 Submission")

    st.markdown("---")

    # Connection Status
    conn = get_db2_connection()
    if conn.is_connected:
        st.success("🟢 IBM Db2: Connected")
        info = conn.get_server_info()
        st.caption(f"Server: {info.get('dbms_name', 'Db2')} {info.get('dbms_ver', '')}")
    else:
        st.error("🔴 IBM Db2: Disconnected")
        if st.button("Reconnect Db2"):
            st.session_state.db_connected = conn.connect()
            st.rerun()

    # Gemini Status
    if gemini_settings.api_key:
        st.success("🟢 Gemini API: Configured")
    else:
        st.warning("🟡 Gemini API: Not Configured")
        api_key_input = st.text_input("Enter Gemini API Key", type="password")
        if api_key_input:
            gemini_settings.api_key = api_key_input
            os.environ["GEMINI_API_KEY"] = api_key_input
            st.rerun()

    st.markdown("---")

    # Patient Selector
    repo = get_repo()
    try:
        patients = repo.list_patients()
    except Exception:
        patients = []

    patient_options = {p["PATIENT_ID"]: f"{p['DISPLAY_NAME']} ({p['DEMO_CODE']})"
                       for p in patients}

    if patient_options:
        selected_pid = st.selectbox(
            "Selected Patient",
            options=list(patient_options.keys()),
            format_func=lambda x: patient_options[x],
            key="current_patient_id",
        )
    else:
        st.info("No patients found. Seed demo data first.")
        selected_pid = None

    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "👤 Patient Workspace",
            "📄 Document Upload",
            "✅ Human Review",
            "💬 Ask MediTwin",
            "📋 Audit History",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem; color:#718096; text-align:center;'>"
        "Synthetic Data Demonstration<br>Not a Medical Device"
        "</div>",
        unsafe_allow_html=True,
    )


# ================================================================
# DISCLAIMER BANNER
# ================================================================
st.markdown(f'<div class="disclaimer-banner">⚠️ {DISCLAIMER}</div>',
            unsafe_allow_html=True)


# ================================================================
# PAGE 1: DASHBOARD
# ================================================================
if page == "📊 Dashboard":
    st.markdown("## System Dashboard")
    st.caption("Overview of the MediTwin AI healthcare record intelligence platform")

    repo = get_repo()
    stats = repo.get_dashboard_stats() if conn.is_connected else {}

    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Synthetic Patients</div>'
            f'<div class="metric-value">{stats.get("total_patients", 0)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Documents Ingested</div>'
            f'<div class="metric-value">{stats.get("total_documents", 0)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Approved Observations</div>'
            f'<div class="metric-value">{stats.get("total_observations", 0)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c4:
        pending = stats.get("pending_reviews", 0)
        color = "#DD6B20" if pending > 0 else "#38A169"
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Pending Reviews</div>'
            f'<div class="metric-value" style="color:{color}">{pending}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # System Status & Quick Actions
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### System Architecture Status")
        arch_data = {
            "Component": ["IBM Db2", "LangChain", "LangGraph", "Gemini API", "PyMuPDF"],
            "Role": ["System of Record", "Extraction & Generation", "Workflow Orchestration", "Language Model", "PDF Extraction"],
            "Status": [
                "Connected" if conn.is_connected else "Disconnected",
                "Available",
                "Available",
                "Configured" if gemini_settings.api_key else "Needs Key",
                "Available",
            ],
        }
        st.dataframe(pd.DataFrame(arch_data), use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### Quick Actions")
        if st.button("🌱 Seed Demo Data", use_container_width=True):
            if conn.is_connected:
                seed_patients(repo)
                st.success("Demo data seeded successfully.")
                st.rerun()
            else:
                st.error("Cannot seed: Db2 not connected.")

        if st.button("🔄 Refresh Statistics", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Recent Activity
    st.markdown("### Recent System Activity")
    try:
        activity = repo.get_audit_log(limit=10)
        if activity:
            activity_data = []
            for a in activity:
                activity_data.append({
                    "Time": str(a.get("LOGGED_AT", ""))[:19],
                    "Action": a.get("ACTION", ""),
                    "Entity": f"{a.get('ENTITY_TYPE', '')} #{a.get('ENTITY_ID', '')}",
                    "Actor": a.get("ACTOR_ID", ""),
                })
            st.dataframe(pd.DataFrame(activity_data), use_container_width=True, hide_index=True)
        else:
            st.info("No activity recorded yet.")
    except Exception as e:
        st.info("Activity log unavailable.")


# ================================================================
# PAGE 2: PATIENT WORKSPACE
# ================================================================
elif page == "👤 Patient Workspace":
    st.markdown("## Patient Longitudinal Workspace")

    if not selected_pid:
        st.warning("Please select a patient from the sidebar.")
    else:
        repo = get_repo()
        patient = repo.get_patient(selected_pid)

        if patient:
            # Patient Header
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Name:** {patient.get('DISPLAY_NAME', '')}")
            with c2:
                st.markdown(f"**Code:** `{patient.get('DEMO_CODE', '')}`")
            with c3:
                by = patient.get('BIRTH_YEAR', '')
                st.markdown(f"**Birth Year:** {by if by else 'Not recorded'}")

            st.markdown("---")

            # Approved Observations for this patient
            approved_obs = repo.get_approved_observations(selected_pid)

            if not approved_obs:
                st.info("No approved observations found for this patient. "
                        "Upload and approve medical documents to build the patient timeline.")
            else:
                # Metric Filter & Trend Chart
                distinct_tests = repo.get_distinct_test_codes(selected_pid)
                test_codes = [t.get("TEST_CODE") for t in distinct_tests if t.get("TEST_CODE")]

                if test_codes:
                    st.markdown("### Metric Trend Analysis")
                    selected_metric = st.selectbox(
                        "Select Metric to Analyze",
                        options=test_codes,
                        index=0,
                    )

                    trend = compute_metric_trend(approved_obs, selected_metric)

                    if trend.get("count", 0) > 0:
                        # Metric Summary Cards
                        sc1, sc2, sc3, sc4 = st.columns(4)
                        with sc1:
                            st.metric("First Value", f"{trend['first_value']} {trend['unit']}",
                                      trend['first_date'])
                        with sc2:
                            st.metric("Latest Value", f"{trend['latest_value']} {trend['unit']}",
                                      trend['latest_date'])
                        with sc3:
                            chg = trend['absolute_change']
                            st.metric("Absolute Change", f"{chg:+.4g} {trend['unit']}")
                        with sc4:
                            pct = trend['percentage_change']
                            st.metric("Percentage Change", f"{pct:+.2f}%" if pct is not None else "N/A")

                        # Plotly Chart
                        chart_data = pd.DataFrame(trend["all_values"])
                        fig = px.line(
                            chart_data,
                            x="date",
                            y="value",
                            markers=True,
                            title=f"{trend.get('test_name', selected_metric)} Over Time",
                            labels={"date": "Observation Date", "value": f"Value ({trend['unit']})"},
                        )
                        fig.update_traces(line_color="#0066CC", marker=dict(size=8, color="#0A2540"))
                        fig.update_layout(
                            plot_bgcolor="white",
                            paper_bgcolor="white",
                            xaxis=dict(showgrid=True, gridcolor="#E2E8F0"),
                            yaxis=dict(showgrid=True, gridcolor="#E2E8F0"),
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown(f"**Evidence Summary:** {format_trend_summary(trend)}")

                st.markdown("---")

                # Chronological Timeline
                st.markdown("### Chronological Observation History")
                docs = repo.list_documents(selected_pid)
                timeline = build_patient_timeline(approved_obs, docs)

                timeline_data = []
                for item in timeline:
                    if item["type"] == "observation":
                        timeline_data.append({
                            "Date": item["date_str"],
                            "Test Name": item["title"],
                            "Value": f"{item['value']} {item['unit']}" if item['value'] is not None else item.get('value_text', ''),
                            "Source Document": item["source"],
                            "Page": item.get("page", ""),
                            "Source Snippet": item.get("snippet", "")[:60] + "..." if item.get("snippet") else "",
                        })

                if timeline_data:
                    st.dataframe(pd.DataFrame(timeline_data), use_container_width=True, hide_index=True)


# ================================================================
# PAGE 3: DOCUMENT UPLOAD
# ================================================================
elif page == "📄 Document Upload":
    st.markdown("## Ingest Synthetic Medical Document")
    st.caption("Pipeline A: Upload → Validate → Parse → LangChain Extraction → Review Gate")

    if not selected_pid:
        st.warning("Please select a patient from the sidebar first.")
    else:
        repo = get_repo()
        patient = repo.get_patient(selected_pid)
        st.info(f"Target Patient: **{patient.get('DISPLAY_NAME')}** (`{patient.get('DEMO_CODE')}`)")

        # Upload control
        uploaded_file = st.file_uploader(
            "Choose a synthetic medical report (PDF or TXT)",
            type=["pdf", "txt"],
            help="Maximum file size: 10 MB. Only synthetic documents allowed.",
        )

        # Quick sample loader
        sample_dir = os.path.join(os.path.dirname(__file__), "sample_data", "synthetic_reports")
        sample_files = [f for f in os.listdir(sample_dir) if f.endswith(".pdf")] if os.path.exists(sample_dir) else []

        if sample_files:
            st.markdown("---")
            st.markdown("**Or select a pre-generated synthetic sample report:**")
            selected_sample = st.selectbox("Sample Reports", options=sample_files)
            load_sample = st.button("Load Selected Sample Report")
        else:
            load_sample = False
            selected_sample = None

        file_bytes = None
        file_name = None

        if uploaded_file:
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
        elif load_sample and selected_sample:
            sample_path = os.path.join(sample_dir, selected_sample)
            with open(sample_path, "rb") as f:
                file_bytes = f.read()
            file_name = selected_sample

        if file_bytes and file_name:
            st.markdown("---")
            st.markdown(f"### Processing: `{file_name}`")

            # Step 1: Validate file
            with st.spinner("Validating document..."):
                is_valid, err = validate_file(file_name, file_bytes)

            if not is_valid:
                st.error(f"Validation failed: {err}")
            else:
                st.success("✅ File format and size validated.")

                # Step 2: Parse document
                with st.spinner("Extracting text and mapping pages..."):
                    parsed_doc = parse_document(file_name, file_bytes)

                if parsed_doc.parse_status != "PARSED":
                    st.error(f"Parsing failed: {parsed_doc.error_message}")
                else:
                    st.success(f"✅ Extracted {parsed_doc.total_pages} page(s), "
                               f"{len(parsed_doc.full_text)} characters.")

                    # Show page tabs
                    page_tabs = st.tabs([f"Page {p.page_number}" for p in parsed_doc.pages])
                    for i, tab in enumerate(page_tabs):
                        with tab:
                            st.text_area(f"Page {i+1} Content",
                                         value=parsed_doc.pages[i].text,
                                         height=200, disabled=True)

                    # Step 3: Insert Document record into Db2
                    if conn.is_connected:
                        try:
                            doc_id = repo.create_document(
                                patient_id=selected_pid,
                                file_name=file_name,
                                document_type="LAB_REPORT",
                                extracted_text=parsed_doc.full_text,
                                source_hash=parsed_doc.source_hash,
                            )
                            repo.update_document_status(doc_id, "PARSED")
                            get_audit().log_upload(doc_id, file_name, selected_pid)
                            st.success(f"✅ Document registered in Db2 (ID: {doc_id})")
                        except Exception as e:
                            st.error(f"Failed to register document in Db2: {e}")
                            doc_id = None
                    else:
                        st.warning("Db2 not connected. Document not saved to database.")
                        doc_id = None

                    # Step 4: Extract Observations
                    st.markdown("---")
                    st.markdown("### Structured Observation Extraction")

                    if st.button("🚀 Extract Observations with LangChain + Gemini", type="primary"):
                        if not gemini_settings.api_key:
                            st.error("Gemini API key is required for extraction. "
                                     "Please configure it in the sidebar.")
                        else:
                            with st.spinner("Running LangChain structured extraction..."):
                                pages_text = [(p.page_number, p.text) for p in parsed_doc.pages]
                                result = extract_from_document(
                                    pages_text=pages_text,
                                    api_key=gemini_settings.api_key,
                                    model_name=gemini_settings.model,
                                )

                            if result.observations:
                                st.success(f"✅ Extracted {len(result.observations)} observations.")

                                # Display extracted observations in editable form
                                obs_data = []
                                for obs in result.observations:
                                    obs_dict = obs.model_dump()
                                    obs_dict["needs_review"] = obs.needs_review
                                    obs_dict["reasons"] = ", ".join(obs.review_reasons)
                                    obs_data.append(obs_dict)

                                st.dataframe(pd.DataFrame(obs_data), use_container_width=True)

                                # Save observations as PENDING in Db2
                                if doc_id and conn.is_connected:
                                    saved_count = 0
                                    for obs in result.observations:
                                        try:
                                            repo.create_observation(
                                                patient_id=selected_pid,
                                                document_id=doc_id,
                                                test_name=obs.test_name,
                                                test_code=obs.test_code,
                                                value_numeric=obs.value_numeric,
                                                value_text=obs.value_text,
                                                unit=obs.unit,
                                                reference_low=obs.reference_low,
                                                reference_high=obs.reference_high,
                                                observed_at=obs.observed_at,
                                                source_page=obs.source_page,
                                                source_snippet=obs.source_snippet,
                                                extraction_confidence=obs.confidence,
                                            )
                                            saved_count += 1
                                        except Exception as e:
                                            st.error(f"Error saving observation: {e}")

                                    repo.connection.commit()
                                    get_audit().log_extraction(doc_id, saved_count)
                                    st.success(f"✅ {saved_count} observations saved as PENDING in Db2. "
                                               f"Go to **Human Review** to approve them.")
                            else:
                                st.warning("No observations could be extracted from this document.")


# ================================================================
# PAGE 4: HUMAN REVIEW
# ================================================================
elif page == "✅ Human Review":
    st.markdown("## Human Verification Gate")
    st.caption("Mandatory review: Extracted observations default to PENDING. "
               "Only APPROVED observations enter the trusted timeline.")

    repo = get_repo()
    audit = get_audit()

    if not selected_pid:
        st.warning("Please select a patient from the sidebar.")
    else:
        pending_obs = repo.get_pending_observations(selected_pid)

        if not pending_obs:
            st.success("🎉 No observations pending review for this patient.")
        else:
            st.info(f"**{len(pending_obs)}** observation(s) awaiting your review.")

            for i, obs in enumerate(pending_obs):
                obs_id = obs.get("OBSERVATION_ID")
                with st.expander(
                    f"Observation #{obs_id}: **{obs.get('TEST_NAME')}** = "
                    f"{obs.get('VALUE_NUMERIC')} {obs.get('UNIT', '')} "
                    f"({obs.get('FILE_NAME')})",
                    expanded=True,
                ):
                    c1, c2 = st.columns([2, 1])

                    with c1:
                        # Editable fields
                        col_val, col_unit = st.columns(2)
                        with col_val:
                            val = obs.get("VALUE_NUMERIC")
                            new_val = st.number_input(
                                "Numeric Value",
                                value=float(val) if val is not None else 0.0,
                                key=f"val_{obs_id}",
                            )
                        with col_unit:
                            unit = obs.get("UNIT") or ""
                            new_unit = st.text_input(
                                "Unit",
                                value=unit,
                                key=f"unit_{obs_id}",
                            )

                        col_date, col_code = st.columns(2)
                        with col_date:
                            dt = obs.get("OBSERVED_AT") or ""
                            new_date = st.text_input(
                                "Observation Date (YYYY-MM-DD)",
                                value=str(dt) if dt else "",
                                key=f"date_{obs_id}",
                            )
                        with col_code:
                            code = obs.get("TEST_CODE") or ""
                            new_code = st.text_input(
                                "Test Code",
                                value=code,
                                key=f"code_{obs_id}",
                            )

                    with c2:
                        st.markdown("**Source Provenance:**")
                        st.markdown(f"• **Document:** {obs.get('FILE_NAME')}")
                        st.markdown(f"• **Page:** {obs.get('SOURCE_PAGE', 'N/A')}")
                        conf = obs.get("EXTRACTION_CONFIDENCE")
                        if conf:
                            st.markdown(f"• **Confidence:** {float(conf):.0%}")
                        snippet = obs.get("SOURCE_SNIPPET")
                        if snippet:
                            st.markdown(f"• **Snippet:** *\"{snippet}\"*")

                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
                    with btn_col1:
                        if st.button("✅ Approve", key=f"app_{obs_id}", type="primary"):
                            repo.update_observation_review(
                                observation_id=obs_id,
                                status="APPROVED",
                                reviewed_by="CLINICAL_REVIEWER",
                                value_numeric=new_val if new_val != 0.0 else None,
                                unit=new_unit if new_unit else None,
                                observed_at=new_date if new_date else None,
                            )
                            audit.log_approval(
                                observation_id=obs_id,
                                reviewer="CLINICAL_REVIEWER",
                                original_value=float(val) if val else None,
                                corrected_value=new_val,
                            )
                            st.success(f"Approved observation #{obs_id}.")
                            st.rerun()

                    with btn_col2:
                        if st.button("❌ Reject", key=f"rej_{obs_id}"):
                            repo.update_observation_review(
                                observation_id=obs_id,
                                status="REJECTED",
                                reviewed_by="CLINICAL_REVIEWER",
                            )
                            audit.log_rejection(
                                observation_id=obs_id,
                                reviewer="CLINICAL_REVIEWER",
                            )
                            st.warning(f"Rejected observation #{obs_id}.")
                            st.rerun()

            # Bulk Actions
            st.markdown("---")
            if st.button("✅ Approve All Pending Observations", type="secondary"):
                for obs in pending_obs:
                    obs_id = obs.get("OBSERVATION_ID")
                    repo.update_observation_review(
                        observation_id=obs_id,
                        status="APPROVED",
                        reviewed_by="CLINICAL_REVIEWER",
                    )
                    audit.log_approval(obs_id, "CLINICAL_REVIEWER")
                st.success(f"Approved all {len(pending_obs)} observations.")
                st.rerun()


# ================================================================
# PAGE 5: ASK MEDITWIN
# ================================================================
elif page == "💬 Ask MediTwin":
    st.markdown("## Ask MediTwin — Evidence-Grounded Q&A")
    st.caption("Answers are generated ONLY from approved Db2 evidence. "
               "No arbitrary SQL. Full source provenance.")

    if not selected_pid:
        st.warning("Please select a patient from the sidebar.")
    else:
        repo = get_repo()
        patient = repo.get_patient(selected_pid)
        answer_svc = get_answer_svc()
        audit = get_audit()

        st.info(f"Answering for: **{patient.get('DISPLAY_NAME')}** (`{patient.get('DEMO_CODE')}`)")

        # Example Questions
        st.markdown("**Example supported questions:**")
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            q1 = st.button("How did HbA1c change over time?")
            q2 = st.button("What was the latest fasting blood sugar?")
        with ex_col2:
            q3 = st.button("Show all cholesterol measurements")
            q4 = st.button("What is the latest hemoglobin?")

        # Question input
        user_question = st.text_input(
            "Ask a question about this patient's medical history:",
            placeholder="e.g., How has HbA1c changed over the recorded period?",
            key="qa_input",
        )

        active_question = None
        if q1:
            active_question = "How did HbA1c change over time?"
        elif q2:
            active_question = "What was the latest fasting blood sugar?"
        elif q3:
            active_question = "Show all cholesterol measurements"
        elif q4:
            active_question = "What is the latest hemoglobin?"
        elif user_question:
            active_question = user_question

        if active_question:
            st.markdown("---")
            st.markdown(f"**Question:** *{active_question}*")

            with st.spinner("Retrieving Db2 evidence and generating grounded response..."):
                result = answer_svc.answer_question(
                    patient_id=selected_pid,
                    question=active_question,
                )

            # Log Q&A in audit
            audit.log_question(
                patient_id=selected_pid,
                question=active_question,
                had_evidence=result.get("has_evidence", False),
            )

            # Display Answer
            st.markdown("### Answer")
            st.markdown(result["answer"])

            # Display Evidence Cards
            if result.get("has_evidence") and result.get("evidence_cards"):
                st.markdown("---")
                st.markdown(f"### Supporting Evidence ({result.get('observation_count', 0)} records)")

                for card in result["evidence_cards"]:
                    st.markdown(
                        f'<div class="evidence-card">'
                        f'<strong>{card["test_name"]}</strong>: {card["value"]} {card["unit"]}<br>'
                        f'<span style="font-size:0.85rem; color:#4A5568;">'
                        f'Date: {card["date"]} | Source: {card["source_file"]} (p. {card.get("source_page", 1)})<br>'
                        f'<em>"{card["snippet"]}"</em>'
                        f'</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Display Sources
            if result.get("sources"):
                st.markdown("---")
                st.markdown("### Source Documents Cited")
                for src in result["sources"]:
                    st.markdown(f"• `{src['file_name']}` (Page {src.get('page', 1)})")


# ================================================================
# PAGE 6: AUDIT HISTORY
# ================================================================
elif page == "📋 Audit History":
    st.markdown("## Audit & Compliance Log")
    st.caption("Immutable append-only record of all system events for traceability")

    repo = get_repo()

    c1, c2 = st.columns([3, 1])
    with c1:
        entity_filter = st.selectbox(
            "Filter by Entity Type",
            options=["ALL", "PATIENT", "DOCUMENT", "OBSERVATION"],
        )
    with c2:
        log_limit = st.selectbox("Rows to Show", options=[20, 50, 100], index=1)

    try:
        filter_type = None if entity_filter == "ALL" else entity_filter
        logs = repo.get_audit_log(entity_type=filter_type, limit=log_limit)

        if logs:
            log_data = []
            for l in logs:
                log_data.append({
                    "Audit ID": l.get("AUDIT_ID"),
                    "Timestamp": str(l.get("LOGGED_AT", ""))[:19],
                    "Actor": l.get("ACTOR_ID"),
                    "Action": l.get("ACTION"),
                    "Entity Type": l.get("ENTITY_TYPE"),
                    "Entity ID": l.get("ENTITY_ID"),
                    "Details": l.get("DETAILS_JSON", "")[:80] if l.get("DETAILS_JSON") else "",
                })
            st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
        else:
            st.info("No audit logs found.")
    except Exception as e:
        st.error(f"Error reading audit log: {e}")
