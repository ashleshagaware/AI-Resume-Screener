# Deterministic & Explainable AI Resume Scoring Engine

import re
import math
from typing import Dict, List, Set, Any, Tuple
from .taxonomy import SKILL_TAXONOMY, SYNONYMS, DEGREE_LEVELS, CERTIFICATIONS
from .fairness import sanitize_resume_text

# Common English stopwords
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'can\'t', 'cannot',
    'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t', 'down', 'during', 'each',
    'few', 'for', 'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'her',
    'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'its',
    'itself', 'let\'s', 'me', 'more', 'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on',
    'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should',
    'shouldn\'t', 'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then',
    'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was',
    'wasn\'t', 'we', 'were', 'weren\'t', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with',
    'won\'t', 'would', 'wouldn\'t', 'you', 'your', 'yours', 'yourself', 'yourselves', 'will', 'also', 'etc'
}

def normalize_text_tokens(text: str) -> List[str]:
    """Cleans and tokenizes text into lowercase words, removing stopwords."""
    words = re.findall(r'[a-zA-Z0-9\+\#\.\/-]+', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]

def extract_skills_from_text(text: str) -> Set[str]:
    """
    Extracts canonical skills from text using direct taxonomy lookups,
    synonym mappings, and regex word boundary matching.
    """
    text_lower = " " + text.lower() + " "
    found_skills: Set[str] = set()
    
    # 1. Check direct synonyms and normalization
    for phrase, canonical in SYNONYMS.items():
        pattern = r'(?:^|[^a-zA-Z0-9\+\#])' + re.escape(phrase) + r'(?:$|[^a-zA-Z0-9\+\#])'
        if re.search(pattern, text_lower):
            found_skills.add(canonical)
            
    # 2. Check all items in taxonomy
    for category, groups in SKILL_TAXONOMY.items():
        for subcat, skills in groups.items():
            for skill in skills:
                pattern = r'(?:^|[^a-zA-Z0-9\+\#])' + re.escape(skill.lower()) + r'(?:$|[^a-zA-Z0-9\+\#])'
                if re.search(pattern, text_lower):
                    found_skills.add(skill)
                    
    return found_skills

def compute_tfidf_cosine_similarity(text1: str, text2: str) -> float:
    """
    Calculates TF-IDF Cosine Similarity between two documents.
    Produces a normalized 0-100% text similarity score.
    """
    tokens1 = normalize_text_tokens(text1)
    tokens2 = normalize_text_tokens(text2)
    
    if not tokens1 or not tokens2:
        return 0.0

    # Build unigrams and bigrams
    def get_ngrams(tokens):
        ngrams = list(tokens)
        for i in range(len(tokens) - 1):
            ngrams.append(f"{tokens[i]}_{tokens[i+1]}")
        return ngrams

    ng1 = get_ngrams(tokens1)
    ng2 = get_ngrams(tokens2)
    
    # Term frequencies
    tf1 = {}
    for term in ng1:
        tf1[term] = tf1.get(term, 0) + 1
    tf2 = {}
    for term in ng2:
        tf2[term] = tf2.get(term, 0) + 1

    # Vocabulary & Document Frequencies across the 2 documents
    vocab = set(tf1.keys()).union(set(tf2.keys()))
    df = {}
    for term in vocab:
        count = (1 if term in tf1 else 0) + (1 if term in tf2 else 0)
        df[term] = count

    # Compute TF-IDF vectors
    total_docs = 2.0
    vec1 = {}
    vec2 = {}
    for term in vocab:
        idf = math.log((1 + total_docs) / (1 + df[term])) + 1.0
        vec1[term] = (tf1.get(term, 0) / len(ng1)) * idf
        vec2[term] = (tf2.get(term, 0) / len(ng2)) * idf

    # Cosine Similarity
    dot_product = sum(vec1[t] * vec2[t] for t in vocab)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
        
    raw_sim = dot_product / (norm1 * norm2)
    
    # Calibrate raw cosine similarity to intuitive 0-100 scale:
    # Text cosine rarely exceeds 0.6 even for matching texts.
    # Raw 0.05 -> ~15%, Raw 0.25 -> ~65%, Raw 0.45+ -> ~90%+
    calibrated = min(100.0, max(0.0, raw_sim * 210.0))
    return round(calibrated, 1)

def extract_years_required(job_text: str) -> int:
    """Extracts required years of experience from job description text."""
    match = re.search(r'(\d+)\+?\s*(?:-\s*\d+)?\s*(?:years|yrs)\b', job_text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 3  # Default expectation if unspecified

def analyze_experience(resume_text: str, required_years: int) -> Tuple[float, float, str, List[str]]:
    """
    Analyzes work experience in candidate resume:
    Returns: (experience_score, estimated_years, experience_summary, seniority_indicators)
    """
    # Isolate experience section if present, removing education section
    exp_text = resume_text
    
    # Split out sections if common headers exist
    sections = re.split(r'\n\s*(?:EDUCATION|ACADEMIC BACKGROUND|CERTIFICATIONS|PROJECTS|SKILLS)\b', resume_text, flags=re.IGNORECASE)
    if sections:
        # Check sections that mention experience
        exp_candidates = [s for s in sections if re.search(r'\b(EXPERIENCE|WORK HISTORY|EMPLOYMENT)\b', s, flags=re.IGNORECASE)]
        if exp_candidates:
            exp_text = "\n".join(exp_candidates)

    # 1. Detect year numbers / ranges (e.g. 2018 - 2023, 2021-Present)
    year_spans = re.findall(r'\b(200[5-9]|201[0-9]|202[0-6])\s*(?:-|–|to)\s*(200[5-9]|201[0-9]|202[0-6]|present|current)\b', exp_text, flags=re.IGNORECASE)
    
    calculated_years = 0.0
    for start, end in year_spans:
        s = int(start)
        e = 2026 if end.lower() in ['present', 'current'] else int(end)
        diff = max(0, e - s)
        calculated_years += min(diff, 10)  # avoid overlapping double counts exceeding bounds
    
    # Check explicit mentions: e.g. "5+ years of experience"
    explicit_matches = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)(?:\s+of)?\s+(?:experience|background|work)', resume_text, flags=re.IGNORECASE)
    if explicit_matches:
        explicit_years = max(float(m) for m in explicit_matches)
        estimated_years = max(calculated_years, explicit_years)
    else:
        estimated_years = calculated_years

    # If no explicit years detected, check overall role counts as fallback
    if estimated_years == 0:
        role_mentions = len(re.findall(r'\b(developer|engineer|analyst|consultant|manager|intern|specialist)\b', exp_text, flags=re.IGNORECASE))
        estimated_years = min(role_mentions * 0.8, 4.0)

    # 2. Detect Seniority and Role Relevance
    seniority_terms = []
    senior_patterns = ['Senior', 'Lead', 'Staff', 'Principal', 'Architect', 'Director', 'Head of']
    for term in senior_patterns:
        if re.search(r'\b' + re.escape(term) + r'\b', resume_text, flags=re.IGNORECASE):
            seniority_terms.append(term)
            
    junior_terms = []
    for term in ['Junior', 'Associate', 'Intern', 'Apprentice', 'Entry-level']:
        if re.search(r'\b' + re.escape(term) + r'\b', resume_text, flags=re.IGNORECASE):
            junior_terms.append(term)

    # Calculate Experience Score (0 - 100)
    ratio = estimated_years / max(required_years, 1)
    base_score = min(100.0, ratio * 85.0)
    
    # Bonuses / adjustments for seniority
    if seniority_terms:
        base_score += min(15.0, len(seniority_terms) * 5.0)
    elif junior_terms and ratio < 0.6:
        # Cap for junior roles with short tenure
        base_score = min(base_score, 50.0)
        
    exp_score = min(100.0, max(15.0, round(base_score, 1)))
    
    # Experience summary description
    if estimated_years >= required_years:
        exp_summary = f"Detected ~{estimated_years:.1f} years of professional experience, meeting or exceeding the {required_years}+ years target."
    elif estimated_years > 0:
        exp_summary = f"Detected ~{estimated_years:.1f} years of experience, below the targeted {required_years}+ years."
    else:
        exp_summary = "Early career profile or minimal verifiable timeline entries detected."
        
    return exp_score, estimated_years, exp_summary, seniority_terms

def analyze_education(resume_text: str) -> Tuple[float, str, List[str]]:
    """
    Evaluates degrees, academic qualifications, and professional certifications.
    Returns: (education_score, highest_degree, certifications_found)
    """
    highest_degree = "Practical / Self-Taught Experience"
    degree_score = 65.0  # Fair default base for tech roles
    
    text_lower = " " + resume_text.lower() + " "
    
    # Check degree levels
    for level, data in DEGREE_LEVELS.items():
        found = False
        for kw in data['keywords']:
            pattern = r'(?:^|[^a-zA-Z0-9])' + re.escape(kw) + r'(?:$|[^a-zA-Z0-9])'
            if re.search(pattern, text_lower):
                highest_degree = data['label']
                degree_score = data['weight']
                found = True
                break
        if found:
            break
            
    # Check certifications
    found_certs = []
    for cert in CERTIFICATIONS:
        if cert.lower() in text_lower:
            found_certs.append(cert)
            
    # Cert bonus: up to +20 pts
    cert_bonus = min(20.0, len(found_certs) * 10.0)
    final_edu_score = min(100.0, degree_score + cert_bonus)
    
    return round(final_edu_score, 1), highest_degree, found_certs

def screen_candidate(candidate_name: str, resume_raw_text: str, job_title: str, job_description: str) -> Dict[str, Any]:
    """
    Main evaluation pipeline for a candidate against a job description.
    Enforces the exact required weighting:
    - Skills: 45%
    - Text Similarity: 25%
    - Relevant Experience: 20%
    - Education / Certifications: 10%
    """
    # 1. Fairness Sanitization (Strips demographic identifiers)
    clean_resume = sanitize_resume_text(resume_raw_text)
    clean_job = sanitize_resume_text(job_description)
    
    # 2. Extract Skills
    required_skills = extract_skills_from_text(job_description)
    if not required_skills:
        # Fallback if job description is very brief
        required_skills = {'JavaScript', 'React', 'Node.js', 'Git/GitHub', 'Problem Solving'}
        
    candidate_skills = extract_skills_from_text(clean_resume)
    
    matched_skills = sorted(list(required_skills.intersection(candidate_skills)))
    missing_skills = sorted(list(required_skills.difference(candidate_skills)))
    additional_skills = sorted(list(candidate_skills.difference(required_skills)))
    
    # Skills score (45% weight)
    skills_score = round((len(matched_skills) / max(len(required_skills), 1)) * 100, 1)
    skills_score = min(100.0, skills_score)
    
    # 3. Text Similarity (25% weight)
    similarity_score = compute_tfidf_cosine_similarity(clean_job, clean_resume)
    
    # 4. Relevant Experience (20% weight)
    required_years = extract_years_required(job_description)
    exp_score, est_years, exp_summary, seniority_indicators = analyze_experience(clean_resume, required_years)
    
    # 5. Education & Certifications (10% weight)
    edu_score, highest_degree, certs = analyze_education(clean_resume)
    
    # 6. Overall Weighted Score Calculation
    overall_score = round(
        (0.45 * skills_score) +
        (0.25 * similarity_score) +
        (0.20 * exp_score) +
        (0.10 * edu_score),
        1
    )
    overall_score = min(100.0, max(0.0, overall_score))
    
    # 7. Generate Explainable Strengths & Areas for Improvement
    strengths = []
    areas_for_improvement = []
    
    # Skill insights
    if skills_score >= 80:
        strengths.append(f"Exceptional skills alignment ({len(matched_skills)}/{len(required_skills)} required competencies covered).")
    elif skills_score >= 50:
        strengths.append(f"Solid coverage of core technical requirements including {', '.join(matched_skills[:3])}.")
    else:
        areas_for_improvement.append(f"Limited technical match ({len(matched_skills)}/{len(required_skills)} skills detected).")
        
    if missing_skills:
        if len(missing_skills) <= 3:
            areas_for_improvement.append(f"Missing a few secondary requirements: {', '.join(missing_skills)}.")
        else:
            areas_for_improvement.append(f"Key required skills not evident in resume: {', '.join(missing_skills[:4])}.")
            
    # Experience insights
    if est_years >= required_years:
        strengths.append(f"Demonstrates sufficient industry tenure ({est_years:.1f} years vs {required_years}+ required).")
    else:
        areas_for_improvement.append(f"Experience level ({est_years:.1f} yrs) is under the preferred {required_years}+ years.")
        
    if seniority_indicators:
        strengths.append(f"Demonstrates leadership capacity with titles: {', '.join(seniority_indicators)}.")
        
    # Education & certs insights
    if certs:
        strengths.append(f"Holds industry credentials: {', '.join(certs)}.")
    if highest_degree and highest_degree != "Practical / Self-Taught Experience":
        strengths.append(f"Academic foundation in {highest_degree}.")
    elif not certs:
        areas_for_improvement.append("Could benefit from formal cloud or domain certifications (e.g. AWS, Scrum).")
        
    # Recommendation tier
    if overall_score >= 80.0:
        recommendation = "Strong Match - High Priority Interview"
        badge_class = "success"
    elif overall_score >= 65.0:
        recommendation = "Good Match - Recommended for Technical Screening"
        badge_class = "primary"
    elif overall_score >= 50.0:
        recommendation = "Moderate Match - Additional Assessment Advised"
        badge_class = "warning"
    else:
        recommendation = "Low Alignment - Foundational Skill Gaps"
        badge_class = "danger"

    return {
        'candidate_name': candidate_name,
        'overall_score': overall_score,
        'recommendation': recommendation,
        'badge_class': badge_class,
        'breakdown': {
            'skills': {
                'score': skills_score,
                'weight': '45%',
                'weighted_contribution': round(0.45 * skills_score, 1),
                'matched_count': len(matched_skills),
                'total_required': len(required_skills)
            },
            'text_similarity': {
                'score': similarity_score,
                'weight': '25%',
                'weighted_contribution': round(0.25 * similarity_score, 1),
                'method': 'TF-IDF Vector Cosine Similarity'
            },
            'relevant_experience': {
                'score': exp_score,
                'weight': '20%',
                'weighted_contribution': round(0.20 * exp_score, 1),
                'estimated_years': est_years,
                'required_years': required_years,
                'summary': exp_summary,
                'seniority': seniority_indicators
            },
            'education': {
                'score': edu_score,
                'weight': '10%',
                'weighted_contribution': round(0.10 * edu_score, 1),
                'highest_degree': highest_degree,
                'certifications': certs
            }
        },
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'additional_skills': additional_skills,
        'strengths': strengths,
        'areas_for_improvement': areas_for_improvement
    }
