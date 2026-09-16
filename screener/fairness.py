# Fairness & Ethical AI Guardrails

import re

ACADEMIC_DISCLAIMER = (
    "This is an academic decision-support demonstration and should not be used as the sole basis for employment decisions."
)

# Protected attributes that MUST NOT influence scoring
PROTECTED_PATTERNS = [
    # Gender & Pronouns
    r'\b(gender|sex|male|female|non-binary|he/him|she/her|they/them)\b',
    # Marital & Family Status
    r'\b(marital status|married|single|divorced|widowed|father of|mother of|children)\b',
    # Age & DOB
    r'\b(date of birth|dob|born in|age:\s*\d+|\d+\s*years old)\b',
    # Religion & Ethnicity
    r'\b(religion|caste|race|ethnicity|nationality|citizenship status)\b',
    # Health & Disability
    r'\b(disability|handicap|medical condition|health status)\b'
]

def sanitize_resume_text(text: str) -> str:
    """
    Fairness filter: Strips demographic indicators from raw resume text
    so that downstream similarity and entity extractors only process
    job-relevant skills, professional achievements, and education.
    """
    cleaned = text
    for pattern in PROTECTED_PATTERNS:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    # Collapse multiple whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_fairness_audit():
    """
    Returns fairness verification statements for academic reporting.
    """
    return {
        'policy': 'Blind Merit-Based Evaluation',
        'protected_attributes_excluded': [
            'Race & Ethnicity',
            'Gender & Gender Identity',
            'Age & Date of Birth',
            'Religion & Beliefs',
            'Disability & Health Status',
            'Marital & Parental Status'
        ],
        'evaluated_dimensions': [
            {'dimension': 'Technical & Soft Skills', 'weight': '45%', 'basis': 'Direct taxonomy & synonym matching'},
            {'dimension': 'Semantic Text Similarity', 'weight': '25%', 'basis': 'Cosine similarity on sanitized TF-IDF vectors'},
            {'dimension': 'Relevant Work Experience', 'weight': '20%', 'basis': 'Years of experience & role seniority alignment'},
            {'dimension': 'Education & Credentials', 'weight': '10%', 'basis': 'Recognized degree levels & professional certifications'}
        ],
        'disclaimer': ACADEMIC_DISCLAIMER
    }
