# SCANORA + CT-RATE (report-text retrieval prototype)

## 1. Download the CT-RATE report CSV
Use the official gated dataset page:
https://huggingface.co/datasets/ibrahimhamamci/CT-RATE

You previously received access. Sign in to the same Hugging Face account, make sure you accepted the dataset terms, then download:
`dataset/radiology_text_reports/train_reports.csv`

For this first website integration, download the report CSV only. You do not need the multi-terabyte 3D CT image volumes.

## 2. Put the file in this exact location
Create/copy the downloaded file to:
`data/radiology_text_reports/train_reports.csv`

The app also lets you select the CSV from the browser upload control if you prefer.

## 3. Install and run
Open this folder in VS Code, then open Terminal:

Windows:
```powershell
py -m venv .venv
.venv\Scripts\activate
```

Install packages:
```bash
python -m pip install -r requirements.txt
```

Run:
```bash
python -m streamlit run app.py
```

## 4. Use the website
1. Open `http://localhost:8501`.
2. Select **CT-RATE Report Matching**.
3. Confirm the CT-RATE CSV is loaded.
4. Upload a de-identified text-based CT report in PDF or TXT.
5. Click **Find similar CT-RATE reports**.

## What this integration actually does
It builds a TF-IDF text index from the CT-RATE radiology reports and retrieves reference reports with similar word patterns. It does not analyse image voxels, predict abnormalities, or diagnose a patient. Similarity is not clinical equivalence.

## Next stage for CT images
The actual 3D chest CT volumes are a separate, much larger component. A genuine image-analysis path requires loading NIfTI volumes, matching them to labels/metadata, using a suitable 3D model or CT-CLIP pipeline, and evaluating it carefully. Do not claim the current report-search prototype performs CT image analysis.

## Dataset use
Follow the CT-RATE access terms and CC-BY-NC-SA-4.0 licence. It is for academic/research use; commercial exploitation and redistribution are restricted. Cite the dataset/paper in your project report.
