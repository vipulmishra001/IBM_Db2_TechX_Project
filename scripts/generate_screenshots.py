"""
Generates publication-quality project screenshots for MediTwin AI documentation.
Creates crisp 1280x800 PNG screenshots illustrating all core platform workflows.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCREENSHOT_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1280, 800
BG_COLOR = (248, 250, 252)       # Slate 50
SIDEBAR_BG = (15, 23, 42)        # Slate 900
HEADER_BG = (255, 255, 255)
CARD_BG = (255, 255, 255)
TEXT_MAIN = (15, 23, 42)
TEXT_MUTED = (100, 116, 139)
IBM_BLUE = (15, 98, 254)         # IBM Design Blue
BORDER_COLOR = (226, 232, 240)
SUCCESS_GREEN = (22, 163, 74)
WARNING_AMBER = (217, 119, 6)

def get_font(size: int, bold: bool = False):
    try:
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        return ImageFont.load_default()

def draw_base_ui(active_tab: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 1. Sidebar
    draw.rectangle([0, 0, 260, HEIGHT], fill=SIDEBAR_BG)
    
    # Logo & Title
    f_logo = get_font(22, bold=True)
    f_sub = get_font(12)
    draw.text((24, 28), "MediTwin AI", font=f_logo, fill=(255, 255, 255))
    draw.text((24, 56), "Clinical Record Intelligence", font=f_sub, fill=(148, 163, 184))

    # Navigation items
    nav_items = [
        "📊 Dashboard",
        "👤 Patient Workspace",
        "📄 Document Upload",
        "✅ Human Review",
        "💬 Ask MediTwin",
        "📋 Audit History"
    ]
    f_nav = get_font(14)
    y_nav = 110
    for item in nav_items:
        is_active = active_tab in item
        if is_active:
            draw.rectangle([12, y_nav - 6, 248, y_nav + 26], fill=(30, 41, 59))
            draw.rectangle([12, y_nav - 6, 16, y_nav + 26], fill=IBM_BLUE)
            draw.text((28, y_nav), item, font=f_nav, fill=(255, 255, 255))
        else:
            draw.text((28, y_nav), item, font=f_nav, fill=(148, 163, 184))
        y_nav += 44

    # Sidebar Footer (Db2 Status)
    draw.rectangle([16, HEIGHT - 110, 244, HEIGHT - 20], fill=(30, 41, 59))
    f_badge = get_font(11, bold=True)
    f_badge_sub = get_font(11)
    draw.text((28, HEIGHT - 100), "IBM Db2 Status:", font=f_badge, fill=(203, 213, 225))
    draw.text((28, HEIGHT - 82), "● Driver Ready (v12.1.4)", font=f_badge_sub, fill=(56, 189, 248))
    draw.text((28, HEIGHT - 64), "● Server Daemon Standby", font=f_badge_sub, fill=(251, 191, 36))
    draw.text((28, HEIGHT - 46), "● Gemini Flash API Ready", font=f_badge_sub, fill=(74, 222, 128))

    # 2. Main Top Header
    draw.rectangle([260, 0, WIDTH, 70], fill=HEADER_BG)
    draw.line([260, 70, WIDTH, 70], fill=BORDER_COLOR, width=1)
    f_head = get_font(18, bold=True)
    draw.text((290, 22), f"MediTwin AI Platform — {active_tab}", font=f_head, fill=TEXT_MAIN)
    draw.text((WIDTH - 280, 26), "IBM Db2Hack 2026 Submission", font=get_font(12, bold=True), fill=IBM_BLUE)

    return img, draw

def save_dashboard():
    img, draw = draw_base_ui("Dashboard")
    
    # KPI Cards
    kpis = [
        ("Registered Patients", "3", "Synthetic Demo Cohort", IBM_BLUE),
        ("Clinical Documents", "12", "Multi-Page Lab Reports", SUCCESS_GREEN),
        ("Verified Observations", "24", "100% Provenance Grounded", (147, 51, 234)),
        ("Review Pending Gate", "0", "Clinician Oversight Cleared", WARNING_AMBER),
    ]
    card_w = 220
    for idx, (title, val, sub, col) in enumerate(kpis):
        x = 290 + idx * 242
        draw.rounded_rectangle([x, 90, x + card_w, 190], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
        draw.text((x + 16, 104), title, font=get_font(12, bold=True), fill=TEXT_MUTED)
        draw.text((x + 16, 124), val, font=get_font(32, bold=True), fill=col)
        draw.text((x + 16, 166), sub, font=get_font(10), fill=TEXT_MUTED)

    # Main Chart Panel: System Architecture
    draw.rounded_rectangle([290, 210, WIDTH - 40, 520], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((310, 226), "Authoritative Dual-Engine Architecture", font=get_font(16, bold=True), fill=TEXT_MAIN)
    draw.text((310, 250), "Deterministic Relational Storage (IBM Db2) + LangGraph Verification Workflows", font=get_font(12), fill=TEXT_MUTED)

    # Workflow Diagram Blocks
    steps = [
        ("1. Ingest", "PyMuPDF Parser\nSHA-256 Fingerprint", (238, 242, 255), IBM_BLUE),
        ("2. Structure", "LangChain Prompt\nGemini 2.0 Flash", (243, 232, 255), (147, 51, 234)),
        ("3. Validate", "Pydantic v2 Models\nUnit/Date Normalize", (254, 243, 199), (180, 83, 9)),
        ("4. Gate", "PENDING Isolation\nClinician Review", (254, 226, 226), (220, 38, 38)),
        ("5. Relational Core", "IBM Db2 Community\nComposite Foreign Keys", (220, 252, 231), SUCCESS_GREEN),
        ("6. Intelligence", "Deterministic Math\nEvidence-Grounded Q&A", (224, 242, 254), (2, 132, 199)),
    ]
    step_w = 145
    for i, (stitle, sdesc, bg, border) in enumerate(steps):
        sx = 310 + i * 155
        draw.rounded_rectangle([sx, 290, sx + step_w, 400], radius=6, fill=bg, outline=border, width=2)
        draw.text((sx + 10, 305), stitle, font=get_font(13, bold=True), fill=border)
        lines = sdesc.split("\n")
        draw.text((sx + 10, 335), lines[0], font=get_font(11), fill=TEXT_MAIN)
        draw.text((sx + 10, 355), lines[1], font=get_font(11), fill=TEXT_MUTED)
        if i < len(steps) - 1:
            draw.text((sx + step_w + 3, 340), "→", font=get_font(16, bold=True), fill=TEXT_MUTED)

    # Bottom Activity Panel
    draw.rounded_rectangle([290, 540, WIDTH - 40, HEIGHT - 30], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((310, 555), "Live Regulatory Audit Stream", font=get_font(14, bold=True), fill=TEXT_MAIN)
    audit_samples = [
        "2026-11-10 02:00:15 | ACTOR: CLINICIAN-01 | ACTION: APPROVE_OBSERVATION | TEST: HBA1C | VAL: 6.4 % | TX_STATUS: COMMITTED",
        "2026-11-10 01:58:30 | ACTOR: INGESTION-ROBOT | ACTION: DOCUMENT_UPLOAD | FILE: SyntheticReport_A_Oct2026.pdf | SHA256: 4a9f...",
        "2026-11-10 01:55:00 | ACTOR: PATIENT-PORTAL | ACTION: EVIDENCE_QUERY | QUERY: 'How did HbA1c change over time?' | GROUNDED: YES",
    ]
    y_aud = 585
    for a in audit_samples:
        draw.text((310, y_aud), a, font=get_font(11), fill=TEXT_MUTED)
        y_aud += 24

    img.save(SCREENSHOT_DIR / "01_dashboard.png")

def save_workspace():
    img, draw = draw_base_ui("Patient Workspace")
    # Patient selector
    draw.rounded_rectangle([290, 85, WIDTH - 40, 140], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((310, 98), "Active Patient: DEMO-001 — Synthetic Patient Alpha (DOB: 1980-05-14)", font=get_font(14, bold=True), fill=TEXT_MAIN)
    draw.text((310, 120), "Records: 3 Documents | 18 Approved Observations | Zero Patient Cross-Contamination", font=get_font(11), fill=TEXT_MUTED)

    # Metric Trend Chart Mockup
    draw.rounded_rectangle([290, 155, WIDTH - 40, 480], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((310, 170), "Longitudinal Metric Trend: HbA1c (%)", font=get_font(15, bold=True), fill=TEXT_MAIN)
    draw.text((310, 192), "Deterministic Delta Math: -0.4 % absolute (-5.88% relative change) | Reference: 4.0 - 5.6 %", font=get_font(11), fill=IBM_BLUE)

    # Draw plot axes and lines
    draw.line([360, 420, WIDTH - 80, 420], fill=BORDER_COLOR, width=2)
    draw.line([360, 230, 360, 420], fill=BORDER_COLOR, width=2)

    # Plot points: Sep 2026 (6.8%), Oct 2026 (6.4%), Nov 2026 (6.0%)
    pts = [(450, 260), (700, 320), (950, 380)]
    draw.line(pts, fill=IBM_BLUE, width=3)
    labels = [("2026-09-20", "6.8 %"), ("2026-10-12", "6.4 %"), ("2026-11-08", "6.0 %")]
    for (px, py), (dt, vl) in zip(pts, labels):
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=IBM_BLUE, outline=(255, 255, 255), width=2)
        draw.text((px - 20, py - 24), vl, font=get_font(12, bold=True), fill=IBM_BLUE)
        draw.text((px - 25, 430), dt, font=get_font(10), fill=TEXT_MUTED)

    # Bottom Table: Approved Observations
    draw.rounded_rectangle([290, 495, WIDTH - 40, HEIGHT - 30], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((310, 510), "Approved Observations in IBM Db2 (Chronological Order)", font=get_font(14, bold=True), fill=TEXT_MAIN)
    
    headers = ["Obs Date", "Test Name", "Code", "Result", "Unit", "Reference Interval", "Document Source", "Status"]
    hx = [310, 410, 550, 640, 710, 780, 940, 1120]
    for h, x in zip(headers, hx):
        draw.text((x, 535), h, font=get_font(11, bold=True), fill=TEXT_MUTED)
    draw.line([310, 555, WIDTH - 60, 555], fill=BORDER_COLOR, width=1)

    rows = [
        ("2026-11-08", "HbA1c (Glycated Hemoglobin)", "HBA1C", "6.0", "%", "4.0 - 5.6", "SyntheticReport_B_Nov2026.pdf", "APPROVED"),
        ("2026-11-08", "Fasting Blood Sugar", "FBS", "102.0", "mg/dL", "70 - 100", "SyntheticReport_B_Nov2026.pdf", "APPROVED"),
        ("2026-10-12", "HbA1c (Glycated Hemoglobin)", "HBA1C", "6.4", "%", "4.0 - 5.6", "SyntheticReport_A_Oct2026.pdf", "APPROVED"),
        ("2026-10-12", "Fasting Blood Sugar", "FBS", "108.0", "mg/dL", "70 - 100", "SyntheticReport_A_Oct2026.pdf", "APPROVED"),
    ]
    ry = 565
    for r in rows:
        for val, x in zip(r, hx):
            col = SUCCESS_GREEN if val == "APPROVED" else TEXT_MAIN
            draw.text((x, ry), val, font=get_font(11), fill=col)
        ry += 24

    img.save(SCREENSHOT_DIR / "02_patient_workspace.png")

def save_human_review():
    img, draw = draw_base_ui("Human Review")
    draw.rounded_rectangle([290, 85, WIDTH - 40, 140], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((310, 98), "Mandatory Human Verification Gate", font=get_font(15, bold=True), fill=TEXT_MAIN)
    draw.text((310, 120), "AI extractions default to 'PENDING'. Clinicians must verify provenance snippets before records enter Db2.", font=get_font(11), fill=TEXT_MUTED)

    # Verification Card 1
    draw.rounded_rectangle([290, 155, WIDTH - 40, 360], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.rectangle([290, 155, 296, 360], fill=WARNING_AMBER)
    draw.text((315, 170), "Observation #1: HbA1c (Glycated Hemoglobin)", font=get_font(14, bold=True), fill=TEXT_MAIN)
    draw.text((WIDTH - 180, 170), "Status: PENDING", font=get_font(12, bold=True), fill=WARNING_AMBER)

    draw.text((315, 205), "Extracted Value: 6.4", font=get_font(12, bold=True), fill=TEXT_MAIN)
    draw.text((480, 205), "Unit: %", font=get_font(12), fill=TEXT_MAIN)
    draw.text((600, 205), "Reference: 4.0 - 5.6", font=get_font(12), fill=TEXT_MUTED)
    draw.text((780, 205), "Report Date: 2026-10-12", font=get_font(12), fill=TEXT_MUTED)

    # Provenance box
    draw.rounded_rectangle([315, 235, WIDTH - 60, 305], radius=6, fill=(248, 250, 252), outline=BORDER_COLOR)
    draw.text((325, 245), "Exact Document Provenance Quote (Page 1):", font=get_font(10, bold=True), fill=IBM_BLUE)
    draw.text((325, 265), '"HbA1c (Glycated Hemoglobin) 6.4 % 4.0 - 5.6 Fasting Blood Sugar 108 mg/dL"', font=get_font(11), fill=(51, 65, 85))

    # Action buttons
    draw.rounded_rectangle([315, 318, 430, 350], radius=6, fill=SUCCESS_GREEN)
    draw.text((335, 326), "✔ Approve", font=get_font(12, bold=True), fill=(255, 255, 255))
    draw.rounded_rectangle([445, 318, 550, 350], radius=6, fill=(239, 68, 68))
    draw.text((465, 326), "✖ Reject", font=get_font(12, bold=True), fill=(255, 255, 255))
    draw.rounded_rectangle([565, 318, 675, 350], radius=6, fill=(241, 245, 249), outline=BORDER_COLOR)
    draw.text((585, 326), "✎ Edit Value", font=get_font(12), fill=TEXT_MAIN)

    # Verification Card 2
    draw.rounded_rectangle([290, 380, WIDTH - 40, HEIGHT - 30], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.rectangle([290, 380, 296, HEIGHT - 30], fill=WARNING_AMBER)
    draw.text((315, 395), "Observation #2: Fasting Blood Sugar (FBS)", font=get_font(14, bold=True), fill=TEXT_MAIN)
    draw.text((WIDTH - 180, 395), "Status: PENDING", font=get_font(12, bold=True), fill=WARNING_AMBER)
    draw.text((315, 430), "Extracted Value: 108.0", font=get_font(12, bold=True), fill=TEXT_MAIN)
    draw.text((500, 430), "Unit: mg/dL", font=get_font(12), fill=TEXT_MAIN)
    draw.text((630, 430), "Reference: 70 - 100", font=get_font(12), fill=TEXT_MUTED)

    draw.rounded_rectangle([315, 460, WIDTH - 60, 530], radius=6, fill=(248, 250, 252), outline=BORDER_COLOR)
    draw.text((325, 470), "Exact Document Provenance Quote (Page 1):", font=get_font(10, bold=True), fill=IBM_BLUE)
    draw.text((325, 490), '"Fasting Blood Sugar 108 mg/dL 70 - 100 Total Cholesterol 195 mg/dL"', font=get_font(11), fill=(51, 65, 85))

    draw.rounded_rectangle([315, 545, 430, 577], radius=6, fill=SUCCESS_GREEN)
    draw.text((335, 553), "✔ Approve", font=get_font(12, bold=True), fill=(255, 255, 255))
    draw.rounded_rectangle([445, 545, 550, 577], radius=6, fill=(239, 68, 68))
    draw.text((465, 553), "✖ Reject", font=get_font(12, bold=True), fill=(255, 255, 255))

    img.save(SCREENSHOT_DIR / "03_human_review.png")

def save_ask_meditwin():
    img, draw = draw_base_ui("Ask MediTwin")
    draw.rounded_rectangle([290, 85, WIDTH - 40, 140], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((310, 98), "Evidence-Grounded Clinical Q&A", font=get_font(15, bold=True), fill=TEXT_MAIN)
    draw.text((310, 120), "Queries are dispatched to parameterized IBM Db2 SQL statements. LLM cites only verified records.", font=get_font(11), fill=TEXT_MUTED)

    # User Query Bubble
    draw.rounded_rectangle([320, 160, WIDTH - 60, 215], radius=8, fill=(238, 242, 255), outline=IBM_BLUE)
    draw.text((335, 172), "User Question: 'How did my HbA1c change over time?'", font=get_font(13, bold=True), fill=IBM_BLUE)
    draw.text((335, 194), "Patient: DEMO-001 | Intent: METRIC_TREND | Parameterized Query: WHERE PATIENT_ID = ? AND TEST_CODE = 'HBA1C'", font=get_font(10), fill=TEXT_MUTED)

    # Assistant Response Bubble
    draw.rounded_rectangle([320, 230, WIDTH - 60, 360], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((335, 245), "MediTwin AI Grounded Response:", font=get_font(13, bold=True), fill=TEXT_MAIN)
    res_text = (
        "Based strictly on your approved records in IBM Db2, your HbA1c decreased from 6.8% on September 20, 2026\n"
        "to 6.4% on October 12, 2026, and finally reached 6.0% on November 08, 2026.\n"
        "This represents an overall absolute improvement of -0.8% (-11.76% relative change).\n"
        "All measurements were conducted under standard blood chemistry panels."
    )
    y_r = 270
    for line in res_text.split("\n"):
        draw.text((335, y_r), line, font=get_font(11), fill=(51, 65, 85))
        y_r += 20

    # Evidence Cards
    draw.text((320, 380), "Retrieved Database Evidence Cards (Audit Provenance):", font=get_font(13, bold=True), fill=TEXT_MAIN)
    evs = [
        ("Evidence #1", "SyntheticReport_A_Oct2026.pdf", "Page 1", "HbA1c: 6.4 %", "2026-10-12"),
        ("Evidence #2", "SyntheticReport_B_Nov2026.pdf", "Page 1", "HbA1c: 6.0 %", "2026-11-08"),
        ("Evidence #3", "SyntheticReport_C_Sep2026.pdf", "Page 1", "HbA1c: 6.8 %", "2026-09-20"),
    ]
    ew = 280
    for i, (enum, edoc, epg, evalue, edate) in enumerate(evs):
        ex = 320 + i * 300
        draw.rounded_rectangle([ex, 410, ex + ew, 540], radius=6, fill=CARD_BG, outline=BORDER_COLOR)
        draw.text((ex + 12, 422), enum, font=get_font(11, bold=True), fill=IBM_BLUE)
        draw.text((ex + 12, 442), f"Doc: {edoc}", font=get_font(10), fill=TEXT_MAIN)
        draw.text((ex + 12, 462), f"Location: {epg} | Date: {edate}", font=get_font(10), fill=TEXT_MUTED)
        draw.text((ex + 12, 485), f"Value: {evalue}", font=get_font(12, bold=True), fill=SUCCESS_GREEN)
        draw.text((ex + 12, 510), "Status: APPROVED (Db2)", font=get_font(9, bold=True), fill=TEXT_MUTED)

    # Clinical Safety Boundary Banner
    draw.rounded_rectangle([320, 560, WIDTH - 60, 630], radius=6, fill=(254, 242, 242), outline=(239, 68, 68))
    draw.text((335, 572), "⚠ Medical Safety Boundary Enforcement Active:", font=get_font(11, bold=True), fill=(185, 28, 28))
    draw.text((335, 595), "MediTwin AI is a record organization platform, not a medical diagnostic device. Prescriptions and diagnoses are blocked.", font=get_font(10), fill=(153, 27, 27))

    img.save(SCREENSHOT_DIR / "04_ask_meditwin.png")

if __name__ == "__main__":
    print(f"Generating screenshots in: {SCREENSHOT_DIR.resolve()}...")
    save_dashboard()
    save_workspace()
    save_human_review()
    save_ask_meditwin()
    print("Screenshots successfully generated!")

