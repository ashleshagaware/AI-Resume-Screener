# AI Resume Screener (Academic Decision Support)

An explainable, AI-powered resume screening and job matching web application designed for academic decision support and college internship presentation.

---

## 📌 Project Overview

Traditional resume screeners often operate as opaque "black boxes," leaving recruiters and candidates without visibility into why a resume scored high or low. Furthermore, unconstrained AI models risk encoding demographic biases.

**AI Resume Screener** solves this with:
1. **100% Deterministic & Explainable Scoring Model**: Transparent weights for Skills (45%), Text Similarity (25%), Relevant Experience (20%), and Education/Certifications (10%).
2. **Multi-Format Document Parsing**: Real text extraction from PDF (`.pdf`), Microsoft Word (`.docx`), and Plain Text (`.txt`).
3. **Demographic-Blind Ethical AI Guardrails**: Strict sanitization of protected attributes (race, gender, age, religion, marital status, health) before semantic calculation.
4. **Candidate Comparison & Matrix**: Multi-axis radar capability charts and skill gap coverage tables.
5. **Completely Local & Private**: 100% offline execution; requires no external API keys or subscriptions.

---

## ⚖️ Transparent Scoring Formula

$$\text{Overall Match Score} = 0.45 \cdot S_{\text{skills}} + 0.25 \cdot S_{\text{similarity}} + 0.20 \cdot S_{\text{experience}} + 0.10 \cdot S_{\text{education}}$$

| Dimension | Weight | Algorithmic Approach |
| :--- | :---: | :--- |
| **Skills Match** | **45%** | Canonical taxonomy matching with synonym normalization (e.g. `react.js` $\rightarrow$ `React`). Calculates matched vs missing requirements. |
| **Text Similarity** | **25%** | TF-IDF vectorization with unigrams and bigrams, evaluated using Cosine Similarity against the sanitized job requirements. |
| **Relevant Experience** | **20%** | Professional section extraction, date range span computation, leadership seniority identification (Senior, Lead, Staff), and ratio to required years. |
| **Education & Credentials** | **10%** | Academic degree tier weighting (Ph.D., Master's, Bachelor's, Associate's) with bonus scoring for recognized industry certifications (AWS, GCP, CKA, Scrum). |

> **Academic Disclaimer**:
> *"This is an academic decision-support demonstration and should not be used as the sole basis for employment decisions."*

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.14)

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Testing the Complete Flow

1. **Dashboard**: View high-level metrics and score distribution.
2. **New Screening**: Click **"Load Demo Job"** to populate the Senior Frontend / Full-Stack Developer position.
3. Click **"Add Demo Resumes"** to stage 5 diverse fictional candidate profiles (or upload your own PDF/DOCX/TXT files).
4. Click **"Run Decision Analysis"** to launch the step-by-step progress animation.
5. **Results**:
   - Inspect rank order, overall score, matched skills badges, missing skills, and improvement feedback.
   - Click **"Inspect"** on any candidate for deep formula breakdown.
6. **Candidate Comparison**: Compare candidate capability radar charts and inspect the Skills Coverage Matrix.
7. **Screening History**: View persisted records, re-open past runs, and export results to **CSV** or **JSON**.

---

## 📁 Project Architecture

```
ai-resume-screener/
├── run.py                      # Application launcher
├── app.py                      # Flask backend API & route controllers
├── requirements.txt            # Python dependencies (flask, pypdf, python-docx)
├── test_screener.py            # Automated test suite
├── screener/
│   ├── taxonomy.py             # Curated technical & soft skills taxonomy + synonyms
│   ├── fairness.py             # Demographic sanitization & ethics audit
│   ├── parser.py               # Real text extraction for PDF, DOCX, and TXT
│   ├── scoring.py              # Explainable 45/25/20/10 scoring engine
│   ├── storage.py              # Local JSON persistence for screening runs
│   └── demo_data.py            # Fictional Full-Stack job + 5 fictional resumes
├── templates/
│   └── index.html              # Academic dashboard template
├── static/
│   ├── css/style.css           # Styling & print stylesheets
│   └── js/app.js               # Frontend controller, Chart.js radar, upload handlers
├── sample_resumes/             # Pre-generated resume files for upload testing
│   ├── Alex_Rivera_Resume.txt
│   ├── Priya_Sharma_Resume.docx
│   ├── Marcus_Chen_Resume.docx
│   ├── Jordan_Taylor_Resume.txt
│   ├── Samantha_Brooks_Resume.txt
│   └── David_Kim_Resume.pdf
└── data/
    └── screenings.json         # Local screening history database
```
