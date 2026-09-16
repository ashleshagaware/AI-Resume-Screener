# Unit Test Verification Script for AI Resume Screener

import sys
from screener.demo_data import DEMO_JOB, DEMO_CANDIDATES
from screener.scoring import screen_candidate
from screener.storage import save_screening, list_screenings, get_screening, delete_screening
from screener.fairness import get_fairness_audit

def run_tests():
    print("=" * 65)
    print("RUNNING AUTOMATED SCREENER VERIFICATION")
    print("=" * 65)

    results = []
    for c in DEMO_CANDIDATES:
        res = screen_candidate(c['name'], c['text'], DEMO_JOB['title'], DEMO_JOB['description'])
        results.append(res)
        
        # Verify 45/25/20/10 math
        b = res['breakdown']
        expected_overall = round(
            0.45 * b['skills']['score'] +
            0.25 * b['text_similarity']['score'] +
            0.20 * b['relevant_experience']['score'] +
            0.10 * b['education']['score'],
            1
        )
        assert abs(res['overall_score'] - expected_overall) < 0.2, f"Score mismatch: {res['overall_score']} vs {expected_overall}"
        
        print(f"Candidate: {res['candidate_name']:<18} Overall: {res['overall_score']:>5.1f}%  [Skills: {b['skills']['score']:>4.1f}% (45%), Sim: {b['text_similarity']['score']:>4.1f}% (25%), Exp: {b['relevant_experience']['score']:>4.1f}% (20%), Edu: {b['education']['score']:>4.1f}% (10%)]")
        print(f"   -> Recommendation: {res['recommendation']}")
        print(f"   -> Matched Skills ({len(res['matched_skills'])}): {', '.join(res['matched_skills'][:5])}...")
        print(f"   -> Missing Skills ({len(res['missing_skills'])}): {', '.join(res['missing_skills'][:4])}...")
        print()

    # Verify ranking
    assert results[0]['overall_score'] > results[1]['overall_score'], "Alex should outrank Priya"
    assert results[1]['overall_score'] > results[2]['overall_score'], "Priya should outrank Marcus for Frontend role"
    assert results[2]['overall_score'] > results[3]['overall_score'], "Marcus should outrank Jordan"
    assert results[3]['overall_score'] > results[4]['overall_score'], "Jordan should outrank Samantha"

    # Test storage persistence
    screening_id = save_screening(DEMO_JOB['title'], DEMO_JOB['description'], results)
    print(f"Saved screening with ID: {screening_id}")
    
    screenings = list_screenings()
    assert len(screenings) >= 1, "Storage list should have at least 1 screening"
    
    loaded = get_screening(screening_id)
    assert loaded is not None, "Failed to load saved screening"
    assert loaded['job_title'] == DEMO_JOB['title']
    assert len(loaded['candidates']) == 5
    print("Storage verification passed!")

    # Test fairness audit
    audit = get_fairness_audit()
    assert 'policy' in audit
    assert len(audit['protected_attributes_excluded']) == 6
    print("Fairness audit passed!")

    print("=" * 65)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()
