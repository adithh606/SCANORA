```python
import re
from io import BytesIO

import streamlit as st
from pypdf import PdfReader
from PIL import Image
import pytesseract


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="SCANORA",
    page_icon="🩺",
    layout="wide"
)


# ==========================================
# CUSTOM STYLING
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #f5f8f5;
    color: #183b2b;
}

[data-testid="stSidebar"] {
    background-color: #173d2b;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.hero {
    background: linear-gradient(120deg, #173d2b, #397653);
    padding: 35px;
    border-radius: 18px;
    color: white;
    margin-bottom: 25px;
}

.hero h1, .hero p {
    color: white;
}

.result-card {
    background: white;
    border-left: 5px solid #397653;
    padding: 18px;
    border-radius: 10px;
    margin: 12px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# MEDICAL GLOSSARY
# ==========================================

GLOSSARY = {

    "ground-glass opacity":
    "An area in the lung that appears hazy on a CT scan. It may have several causes.",

    "pulmonary nodule":
    "A small rounded spot in the lung. Many are benign, but medical follow-up may be recommended.",

    "pleural effusion":
    "Fluid collected in the space between the lung and chest wall.",

    "atelectasis":
    "Partial or complete collapse of a small area of the lung.",

    "lymphadenopathy":
    "Enlarged lymph nodes. Its significance depends on the clinical context.",

    "emphysema":
    "A lung condition in which air sacs are damaged.",

    "consolidation":
    "An area of lung where air spaces are filled with fluid or other material.",

    "cardiomegaly":
    "An enlargement of the heart.",

    "coronary artery calcification":
    "Calcium deposits in the arteries that supply blood to the heart.",

    "hepatic steatosis":
    "Fat accumulation in the liver, commonly called fatty liver.",

    "fatty liver":
    "Fat accumulation in the liver.",

    "renal calculus":
    "A kidney stone.",

    "hydronephrosis":
    "Swelling of a kidney due to a build-up of urine.",

    "mucosal thickening":
    "Thickening of the lining of a hollow organ or cavity.",

    "degenerative changes":
    "Wear-and-tear changes in joints, bones, or discs."
}


# ==========================================
# FILE EXTRACTION FUNCTIONS
# ==========================================

def extract_pdf_text(file_bytes):

    reader = PdfReader(BytesIO(file_bytes))

    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


def extract_image_text(image_bytes):

    image = Image.open(BytesIO(image_bytes))

    image = image.convert("RGB")

    extracted_text = pytesseract.image_to_string(image)

    return extracted_text


def clean_text(text):

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ==========================================
# MEDICAL TERM EXPLANATION
# ==========================================

NEGATION_CUES = [
    "no ",
    "not seen",
    "without ",
    "negative for",
    "absence of",
    "no evidence of",
    "there is no"
]


def is_negated(text, term):

    lower_text = text.lower()

    start = lower_text.find(term.lower())

    if start == -1:
        return False

    nearby_text = lower_text[max(0, start - 65):start]

    return any(
        cue in nearby_text
        for cue in NEGATION_CUES
    )


def explain_report(report_text):

    lower_text = report_text.lower()

    findings = []

    for term, explanation in GLOSSARY.items():

        if term in lower_text:

            findings.append({
                "term": term,
                "explanation": explanation,
                "negated": is_negated(report_text, term)
            })

    return findings


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

st.sidebar.markdown("# 🩺 SCANORA")

st.sidebar.caption("MEDICAL REPORT INTELLIGENCE")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Upload CT Report",
        "About SCANORA"
    ]
)


# ==========================================
# HOME PAGE
# ==========================================

if page == "Home":

    st.markdown("""
    <div class="hero">

        <h1>Welcome to SCANORA 🩺</h1>

        <p>
        Understand medical language in your CT reports
        with simple explanations.
        </p>

    </div>
    """, unsafe_allow_html=True)

    st.subheader("Making medical reports easier to understand")

    st.write("""
    SCANORA is an educational prototype designed to
    simplify selected medical terms found in radiology reports.

    Upload your report in PDF, TXT, JPG, JPEG or PNG format
    and view explanations of selected medical terms.
    """)

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("### 📄 Document Upload")

        st.write("Upload PDF or TXT reports.")

    with col2:

        st.markdown("### 🖼️ Image Upload")

        st.write("Upload JPG, JPEG or PNG report images.")

    with col3:

        st.markdown("### 💡 Simple Explanations")

        st.write("Understand selected medical terms easily.")

    st.info("Select Upload CT Report from the sidebar to begin.")


# ==========================================
# UPLOAD CT REPORT PAGE
# ==========================================

elif page == "Upload CT Report":

    st.title("📤 Upload Your CT Report")

    st.write("""
    Upload your CT report as a PDF, TXT or image file.
    SCANORA will extract the text and explain selected medical terms.
    """)

    uploaded_file = st.file_uploader(
        "Choose your report",
        type=[
            "pdf",
            "txt",
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if uploaded_file is not None:

        file_name = uploaded_file.name.lower()

        try:

            # PDF EXTRACTION

            if file_name.endswith(".pdf"):

                report_text = extract_pdf_text(
                    uploaded_file.read()
                )

            # TXT EXTRACTION

            elif file_name.endswith(".txt"):

                report_text = uploaded_file.read().decode(
                    "utf-8",
                    errors="ignore"
                )

            # IMAGE OCR EXTRACTION

            else:

                image_bytes = uploaded_file.read()

                st.subheader("Uploaded Report Image")

                st.image(
                    image_bytes,
                    caption="Uploaded medical report",
                    use_container_width=True
                )

                with st.spinner("Extracting text from image..."):

                    report_text = extract_image_text(image_bytes)

            report_text = clean_text(report_text)

            # CHECK EXTRACTED TEXT

            if not report_text:

                st.warning("""
                No readable text was found.

                Please upload a clearer image or a text-based PDF.
                """)

            else:

                st.success("Report text extracted successfully!")

                # SHOW EXTRACTED TEXT

                with st.expander("View Extracted Report Text"):

                    st.write(report_text)

                # FIND MEDICAL TERMS

                st.subheader("💡 Simplified Medical Explanations")

                findings = explain_report(report_text)

                if findings:

                    for item in findings:

                        if item["negated"]:

                            st.markdown(
                                f"""
                                <div class="result-card">

                                <h4>{item['term'].title()}</h4>

                                <p><b>Possible report context:</b>
                                This term appears near wording that may
                                indicate it is absent.</p>

                                <p>{item['explanation']}</p>

                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        else:

                            st.markdown(
                                f"""
                                <div class="result-card">

                                <h4>{item['term'].title()}</h4>

                                <p>{item['explanation']}</p>

                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                else:

                    st.info("""
                    No terms from the current SCANORA glossary
                    were identified.

                    This does not mean that the report is normal.
                    """)

                st.warning("""
                IMPORTANT:

                SCANORA provides general educational explanations only.
                It does not diagnose diseases or recommend treatment.

                The glossary and simple negation check have limitations.
                Always consult a qualified healthcare professional
                for interpretation of your complete report.
                """)

        except Exception as error:

            st.error(f"Unable to process this file: {error}")


# ==========================================
# ABOUT SCANORA PAGE
# ==========================================

elif page == "About SCANORA":

    st.title("ℹ️ About SCANORA")

    st.write("""
    SCANORA is an educational prototype developed to
    make selected medical terms in radiology reports
    easier to understand.
    """)

    st.subheader("How SCANORA Works")

    st.write("""
    1. The user uploads a medical report.
    2. The system extracts text from the uploaded file.
    3. OCR is used to extract text from report images.
    4. The system searches for selected medical terms.
    5. Simple explanations are displayed to the user.
    """)

    st.subheader("Supported File Formats")

    st.write("""
    - PDF documents
    - TXT documents
    - JPG images
    - JPEG images
    - PNG images
    """)

    st.subheader("Important Limitations")

    st.write("""
    - SCANORA does not analyse CT scan pixels or DICOM images.
    - It does not generate a medical diagnosis.
    - It uses a predefined medical glossary.
    - OCR may make mistakes when images are blurry or unclear.
    - Its simple negation check may misunderstand sentence context.
    - It has not been clinically validated.
    """)

    st.info("""
    SCANORA is an educational prototype.
    It is not a substitute for professional medical advice,
    diagnosis or treatment.
    """)


# ==========================================
# FOOTER
# ==========================================

st.sidebar.markdown("---")

st.sidebar.caption("SCANORA | Educational Prototype")
```
