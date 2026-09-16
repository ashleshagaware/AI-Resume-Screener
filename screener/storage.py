# Local Storage & History Persistence for Screenings

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
STORAGE_FILE = os.path.join(DATA_DIR, 'screenings.json')

def _ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def list_screenings() -> List[Dict[str, Any]]:
    """Returns all past screenings summaries, newest first."""
    _ensure_storage()
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Return summaries
            summaries = []
            for item in data:
                candidates = item.get('candidates', [])
                top_candidate = candidates[0]['candidate_name'] if candidates else "N/A"
                top_score = candidates[0]['overall_score'] if candidates else 0.0
                avg_score = round(sum(c['overall_score'] for c in candidates) / max(len(candidates), 1), 1) if candidates else 0.0
                summaries.append({
                    'id': item.get('id'),
                    'timestamp': item.get('timestamp'),
                    'job_title': item.get('job_title', 'Untitled Position'),
                    'candidate_count': len(candidates),
                    'top_candidate': top_candidate,
                    'top_score': top_score,
                    'average_score': avg_score
                })
            return sorted(summaries, key=lambda x: x.get('timestamp', ''), reverse=True)
    except Exception:
        return []

def get_screening(screening_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full details of a specific screening by ID."""
    _ensure_storage()
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if item.get('id') == screening_id:
                    return item
    except Exception:
        pass
    return None

def save_screening(job_title: str, job_description: str, candidates: List[Dict[str, Any]]) -> str:
    """Saves a new screening session and returns its unique ID."""
    _ensure_storage()
    screening_id = str(uuid.uuid4())[:8]
    record = {
        'id': screening_id,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'job_title': job_title.strip() or "Full-Stack Developer",
        'job_description': job_description.strip(),
        'candidates': candidates
    }
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = []
        
    data.insert(0, record)
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    return screening_id

def delete_screening(screening_id: str) -> bool:
    """Deletes a screening session by ID."""
    _ensure_storage()
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        new_data = [item for item in data if item.get('id') != screening_id]
        if len(new_data) != len(data):
            with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2)
            return True
    except Exception:
        pass
    return False

def clear_all_screenings() -> bool:
    """Clears all stored screening history."""
    _ensure_storage()
    try:
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return True
    except Exception:
        return False
