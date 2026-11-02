import re
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="SCANORA | CT-RATE", page_icon="🩺", layout="wide")

st.markdown("""
<style>
.stApp {background:#f4f8f6;color:#173a34}
[data-testid="stSidebar"]{background:#102b28}
[data-testid="stSidebar"] *{color:#f3fbf7!important}
.hero{background:linear-gradient(120deg,#102b28,#1e5149,#34786b);
padding:34px 38px;border-radius:20px;color:white;margin-bottom:22px}
.hero h1{color:white;font-size:44px;margin:0}
.hero p{color:#d8eee7;font-size:16px}
.card{background:white;border:1px solid #e1ebe7;border-radius:15px;padding:18px;margin-bottom:12px}
.warning{background:#fff7e5;border:1px solid #efdca5;padding:14px;border-radius:12px;color:#654f18}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>SCANORA</h1>
  <p>Illuminating the invisible · CT report understanding prototype</p>
  <p>Compare an uploaded report with reference reports from the CT-RATE dataset.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("🩺 SCANORA")
page = st.sidebar.radio("NAVIGATION", ["Home", "CT-RATE Report Matching", "About & Limitations"])

# CT-RATE CSV can be stored in either of these locations.
DEFAULT_DATA_PATHS = [
    Path("data/radiology_text_reports/train_reports.csv"),
    Path("data/train_reports.csv"),
    Path("train_reports.csv"),
]

def extract_pdf_text(file):
    reader = PdfReader(BytesIO(file.getvalue()))
    return "\n".join((p.extract_text() or "") for p in reader.pages)

def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()

def detect_report_columns(df):
    # Prefer columns whose names indicate report content.
    preferred = [
        c for c in df.columns
        if any(word in str(c).lower() for word in
               ["report", "finding", "impression", "conclusion", "text"])
    ]
    # If column names are unfamiliar, inspect a sample and select long text columns.
    if not preferred:
        for c in df.select_dtypes(include=["object"]).columns:
            sample = df[c].dropna().astype(str).head(100)
            if len(sample) and sample.str.len().mean() > 80:
                preferred.append(c)
    return preferred

def detect_id_column(df):
    for c in df.columns:
        name = str(c).lower()
        if any(x in name for x in ["volume", "study", "scan", "patient", "id"]):
            return c
    return None

@st.cache_resource(show_spinner="Loading CT-RATE reports and building text search index...")
def build_index(csv_bytes):
    from io import BytesIO
    df = pd.read_csv(BytesIO(csv_bytes), low_memory=False)
    report_cols = detect_report_columns(df)
    if not report_cols:
        raise ValueError(
            "Could not identify report-text columns. Please inspect the CSV headers "
            "and tell me their names."
        )

    df = df.copy()
    df["_scanora_report"] = df[report_cols].fillna("").astype(str).agg(" ".join, axis=1)
    df["_scanora_report"] = df["_scanora_report"].map(clean_text)
    df = df[df["_scanora_report"].str.len() > 20].reset_index(drop=True)

    if df.empty:
        raise ValueError("No usable report text was found in the selected CSV.")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=60000,
        sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(df["_scanora_report"])
    id_col = detect_id_column(df)
    return df, report_cols, id_col, vectorizer, matrix

def get_csv_bytes(uploaded_csv):
    if uploaded_csv is not None:
        return uploaded_csv.getvalue(), uploaded_csv.name

    for path in DEFAULT_DATA_PATHS:
        if path.exists():
            return path.read_bytes(), str(path)

    return None, None

if page == "Home":
    st.subheader("Welcome to Scanora")
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="card"><h3>01 · Upload</h3>Upload a text-based CT report in PDF or TXT format.</div>', unsafe_allow_html=True)
    c2.markdown('<div class="card"><h3>02 · Compare</h3>Search CT-RATE radiology reports for textually similar reference reports.</div>', unsafe_allow_html=True)
    c3.markdown('<div class="card"><h3>03 · Review</h3>Read reference text and discuss your own report with a qualified clinician.</div>', unsafe_allow_html=True)

    st.info("This version uses the CT-RATE radiology text-report CSV. It does not analyse CT image pixels or diagnose disease.")

elif page == "CT-RATE Report Matching":
    st.subheader("Match a report against CT-RATE reference reports")
    st.write("Step 1: Place the official `train_reports.csv` in the project data folder, or select it below.")

    uploaded_csv = st.file_uploader(
        "CT-RATE train_reports.csv",
        type=["csv"],
        key="ctrate_csv"
    )
    csv_bytes, csv_source = get_csv_bytes(uploaded_csv)

    if csv_bytes is None:
        st.warning(
            "CT-RATE report CSV not found. Download `train_reports.csv` from the "
            "official CT-RATE Hugging Face dataset, then place it at "
            "`data/radiology_text_reports/train_reports.csv`."
        )
        st.markdown("Official dataset: https://huggingface.co/datasets/ibrahimhamamci/CT-RATE")
    else:
        st.success(f"Dataset file found: {csv_source}")
        try:
            df, report_cols, id_col, vectorizer, report_matrix = build_index(csv_bytes)
            st.caption(f"Loaded {len(df):,} reports · Text columns: {', '.join(map(str, report_cols))}")
            uploaded_report = st.file_uploader(
                "Step 2: Upload the patient's CT report (PDF or TXT)",
                type=["pdf", "txt"],
                key="patient_report"
            )
            top_k = st.slider("Number of similar reference reports", 1, 10, 5)

            if uploaded_report and st.button("Find similar CT-RATE reports", type="primary"):
                if uploaded_report.name.lower().endswith(".pdf"):
                    query_text = extract_pdf_text(uploaded_report)
                else:
                    query_text = uploaded_report.getvalue().decode("utf-8", errors="replace")

                query_text = clean_text(query_text)
                if len(query_text) < 20:
                    st.error("Could not extract enough text. If this is a scanned PDF, it needs OCR first.")
                else:
                    query_vector = vectorizer.transform([query_text])
                    scores = cosine_similarity(query_vector, report_matrix).ravel()
                    best_indices = scores.argsort()[::-1][:top_k]

                    st.markdown("### Similar reference reports")
                    st.caption(
                        "Similarity is based on TF-IDF word overlap. It is not a clinical "
                        "similarity score and does not mean the cases have the same diagnosis."
                    )

                    for rank, idx in enumerate(best_indices, start=1):
                        row = df.iloc[idx]
                        identifier = str(row[id_col]) if id_col else f"Dataset row {idx + 1}"
                        with st.expander(
                            f"{rank}. {identifier} · text similarity {scores[idx]:.3f}"
                        ):
                            st.write(row["_scanora_report"][:5000])
                            st.caption("Reference text from CT-RATE. Not a diagnosis for the uploaded patient.")

                    st.download_button(
                        "Download extracted uploaded report text",
                        data=query_text,
                        file_name="scanora_uploaded_report_text.txt",
                        mime="text/plain"
                    )
        except Exception as e:
            st.error(f"Could not load or process the CT-RATE CSV: {e}")
            st.write("If you share the CSV column names (not patient records), I can adapt the loader.")

elif page == "About & Limitations":
    st.subheader("How this prototype uses CT-RATE")
    st.write(
        "The official CT-RATE dataset contains paired non-contrast chest CT volumes "
        "and radiology reports, plus labels and metadata. This website version loads "
        "the radiology text-report CSV and retrieves textually similar reference reports."
    )
    st.markdown("""
    **What it does**
    - Loads the CT-RATE `train_reports.csv` file.
    - Extracts text from a user's PDF or TXT report.
    - Builds a TF-IDF index over CT-RATE report text.
    - Retrieves the top matching reference reports using cosine similarity.

    **What it does not do**
    - It does not inspect CT images or DICOM files.
    - It does not predict abnormalities or provide a diagnosis.
    - Text similarity is not clinical similarity.
    - It is not clinically validated and must not be used for treatment decisions.
    """)
    st.markdown('<div class="warning"><b>Privacy:</b> Use de-identified sample reports only. Do not upload identifiable patient information to this student prototype.</div>', unsafe_allow_html=True)
    st.markdown("**Dataset terms:** CT-RATE is released under CC-BY-NC-SA-4.0 and its access terms restrict use to academic/research purposes and prohibit commercial exploitation and redistribution. Read and follow the current dataset terms before use.")

st.markdown("---")
st.caption("SCANORA · Student research prototype · Not for diagnosis or treatment")
