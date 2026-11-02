import re
from io import BytesIO

import pandas as pd
import streamlit as st
from pypdf import PdfReader


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="SCANORA | Medical Report Intelligence",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# WEBSITE DESIGN
# ==================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #f4f7f5;
    color: #183b33;
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: #102e28;
}

[data-testid="stSidebar"] * {
    color: #f1f8f4;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1250px;
}

.hero {
    background: linear-gradient(
        120deg,
        #102e28,
        #1d5145,
        #397b68
    );
    padding: 42px;
    border-radius: 22px;
    color: white;
    margin-bottom: 28px;
}

.hero h1 {
    color: white;
    font-size: 48px;
    font-weight: 800;
}

.hero p {
    color: #dcefe7;
    font-size: 16px;
}

.card {
    background: white;
    padding: 24px;
    border-radius: 17px;
    border: 1px solid #e1ebe5;
    box-shadow: 0 4px 15px rgba(16,46,40,0.04);
    min-height: 145px;
}

.card h3 {
    color: #1d5145;
    font-size: 19px;
}

.card p {
    color: #62766e;
    font-size: 14px;
}

.section-title {
    font-size: 25px;
    font-weight: 700;
    color: #173f35;
    margin-top: 24px;
    margin-bottom: 15px;
}

.info-banner {
    background: #e6f2ec;
    border-left: 5px solid #397b68;
    padding: 17px;
    border-radius: 10px;
    margin: 15px 0;
    color: #244d40;
}

.warning {
    background: #fff6e4;
    border: 1px solid #ead9ad;
    padding: 17px;
    border-radius: 12px;
    color: #76591c;
    margin-top: 18px;
}

.stButton > button {
    background: #1d5145;
    color: white;
    border-radius: 9px;
    border: none;
    padding: 10px 22px;
    font-weight: 600;
}

.stButton > button:hover {
    background: #347b67;
    color: white;
}

[data-testid="stFileUploader"] {
    background: white;
    border-radius: 12px;
    padding: 15px;
    border: 1px dashed #a9c5b7;
}

.footer {
    text-align: center;
    color: #81938b;
    font-size: 13px;
    padding: 25px;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# MEDICAL TERMINOLOGY GLOSSARY
# ==================================================

GLOSSARY = {

    "ground-glass opacity":
        "An area in the lung that appears hazy on a CT scan. "
        "Several causes are possible, including inflammation or infection.",

    "pulmonary nodule":
        "A small spot or growth in the lung. Its significance depends "
        "on its size, appearance and clinical context.",

    "pleural effusion":
        "Fluid collected in the space between the lungs and chest wall.",

    "atelectasis":
        "An area of the lung that is not fully expanded.",

    "lymphadenopathy":
        "Enlarged lymph nodes. This can occur for several reasons.",

    "emphysema":
        "Damage to the air sacs in the lungs.",

    "consolidation":
        "An area of the lung that appears denser than usual.",

    "cardiomegaly":
        "An enlarged-heart appearance on imaging.",

    "coronary artery calcification":
        "Calcium deposits in the arteries that supply blood to the heart.",

    "hepatic steatosis":
        "Fat accumulation in the liver.",

    "fatty liver":
        "A condition in which extra fat builds up in the liver.",

    "renal calculus":
        "A kidney stone.",

    "hydronephrosis":
        "Swelling of a kidney due to a buildup of urine.",

    "mucosal thickening":
        "Thickening of the lining of an organ or passage.",

    "degenerative changes":
        "Wear-and-tear-type changes that may affect bones or joints."

}


# ==================================================
# PDF EXTRACTION
# ==================================================

def extract_pdf_text(uploaded_file):

    reader = PdfReader(
        BytesIO(uploaded_file.getvalue())
    )

    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    return text


# ==================================================
# TEXT CLEANING
# ==================================================

def clean_text(value):

    if pd.isna(value):
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


# ==================================================
# REPORT EXPLANATION
# ==================================================

def explain_report(report_text):

    report_text = clean_text(report_text).lower()

    if not report_text:
        return []

    explanations = []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        report_text
    )

    negation_words = [
        "no ",
        "without ",
        "negative for ",
        "absence of ",
        "absent ",
        "free of ",
        "no evidence of ",
        "not seen ",
        "not identified "
    ]

    for term, meaning in GLOSSARY.items():

        if term not in report_text:
            continue

        matching_sentences = [
            sentence
            for sentence in sentences
            if term in sentence
        ]

        is_negated = False

        for sentence in matching_sentences:

            position = sentence.find(term)

            preceding_text = sentence[
                max(0, position - 60):position
            ]

            if any(
                word in preceding_text
                for word in negation_words
            ):
                is_negated = True
                break

        explanations.append({

            "term": term.title(),

            "meaning": meaning,

            "status": (
                "Reported as absent or not identified"
                if is_negated
                else "Mentioned in report — review context"
            )

        })

    return explanations


# ==================================================
# SIDEBAR LOGO
# ==================================================

st.sidebar.markdown("""
<div style="text-align:center;padding:20px 5px 25px;">
<div style="font-size:42px;">🩺</div>
<h1 style="color:white;font-size:29px;margin:5px;">SCANORA</h1>
<p style="color:#a8c9bb;font-size:12px;">
MEDICAL REPORT INTELLIGENCE
</p>
</div>
""", unsafe_allow_html=True)


# ==================================================
# NAVIGATION
# ==================================================

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "🏠 Home",
        "📤 Upload CT Report",
        "ℹ️ About SCANORA"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown("""
<div style="background:#1c443a;padding:15px;border-radius:12px;">
<p style="font-size:13px;color:#c5e0d3;">
PROJECT STATUS
</p>
<h4 style="color:white;">Research Prototype</h4>
<p style="font-size:12px;color:#a8c9bb;">
Educational use only. Not intended for clinical diagnosis.
</p>
</div>
""", unsafe_allow_html=True)


# ==================================================
# HOME PAGE
# ==================================================

if page == "🏠 Home":

    st.markdown("""
    <div class="hero">
        <p>WELCOME TO SCANORA</p>
        <h1>Understand Your CT Report.</h1>
        <p>
            A student research prototype for exploring
            radiology report terminology and understanding
            medical terms in simple language.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Platform Overview</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown("""
        <div class="card">
            <h3>📤 Report Upload</h3>
            <p>Upload CT radiology reports in PDF or TXT format.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:

        st.markdown("""
        <div class="card">
            <h3>🩺 Report Understanding</h3>
            <p>Explore selected medical terms and their simple explanations.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:

        st.markdown("""
        <div class="card">
            <h3>📖 Simple Explanations</h3>
            <p>Understand selected medical terminology in simple language.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">How SCANORA Works</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="info-banner">
        <b>01 — Upload</b><br>
        Upload a text-based CT report.
        <br><br>
        <b>02 — Process</b><br>
        Extract report text and identify selected medical terminology.
        <br><br>
        <b>03 — Understand</b><br>
        View simple educational explanations.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="warning">
        <b>Important Medical Notice</b><br>
        SCANORA is an educational research prototype.
        It does not diagnose diseases, analyse CT image
        pixels or replace professional medical advice.
    </div>
    """, unsafe_allow_html=True)


# ==================================================
# UPLOAD CT REPORT PAGE
# ==================================================

elif page == "📤 Upload CT Report":

    st.markdown(
        '<div class="section-title">'
        'Patient-Friendly Report Explanation'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Upload your CT report to identify selected medical "
        "terms and view their simple explanations."
    )

    uploaded_report = st.file_uploader(
        "Upload CT Report",
        type=["pdf", "txt"],
        key="explanation_report"
    )

    if uploaded_report:

        try:

            if uploaded_report.name.lower().endswith(".pdf"):

                report_text = extract_pdf_text(
                    uploaded_report
                )

            else:

                report_text = uploaded_report.getvalue().decode(
                    "utf-8",
                    errors="replace"
                )

            report_text = clean_text(report_text)

            if len(report_text) < 20:

                st.error(
                    "Unable to extract sufficient report text. "
                    "A scanned PDF may require OCR."
                )

            else:

                st.success("Report uploaded successfully.")

                with st.expander("View Original Report Text"):
                    st.write(report_text)

                if st.button(
                    "Explain My CT Report",
                    type="primary"
                ):

                    explanations = explain_report(report_text)

                    st.markdown(
                        '<div class="section-title">'
                        'Explanation Results'
                        '</div>',
                        unsafe_allow_html=True
                    )

                    if explanations:

                        for item in explanations:

                            st.markdown(f"""
                            <div class="card" style="margin-bottom:15px;">
                                <h3>{item['term']}</h3>
                                <p>{item['meaning']}</p>
                                <p><b>Status:</b> {item['status']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    else:

                        st.info(
                            "No terms from the current glossary "
                            "were identified in this report."
                        )

                    st.markdown("""
                    <div class="warning">
                        <b>Medical Disclaimer</b><br>
                        These explanations are educational.
                        They do not interpret the complete report
                        or provide a diagnosis. Always consult
                        a qualified healthcare professional.
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as error:

            st.error(
                f"Unable to process the uploaded report: {error}"
            )


# ==================================================
# ABOUT SCANORA PAGE
# ==================================================

elif page == "ℹ️ About SCANORA":

    st.markdown(
        '<div class="section-title">About SCANORA</div>',
        unsafe_allow_html=True
    )

    st.write(
        "SCANORA is a student research prototype designed "
        "to explore ways of making radiology report information "
        "easier to understand."
    )

    st.markdown("""
    <div class="card">
        <h3>Our Objective</h3>
        <p>
            To develop an educational platform that helps
            users understand selected medical terminology
            found in radiology reports.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Limitations</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    - The prototype processes radiology report text.
    - It does not analyse CT image pixels.
    - The glossary covers only selected medical terms.
    - Its explanations are not clinically validated.
    - It must not be used for diagnosis or treatment decisions.
    """)

    st.markdown("""
    <div class="warning">
        <b>Privacy and Safety</b><br>
        Use only de-identified sample reports.
        Do not upload reports containing personal
        or identifiable patient information.
    </div>
    """, unsafe_allow_html=True)


# ==================================================
# FOOTER
# ==================================================

st.markdown("---")

st.markdown("""
<div class="footer">
    <b>SCANORA</b> · Illuminating the Invisible
    <br>
    Student Research Prototype · 2026–2027
    <br><br>
    Not intended for clinical diagnosis or treatment.
</div>
""", unsafe_allow_html=True)
