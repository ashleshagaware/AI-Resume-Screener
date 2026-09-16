# AI Resume Screener - Flask Web Application

import os
import io
import csv
import json
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from werkzeug.utils import secure_filename

from screener.parser import parse_resume_file
from screener.scoring import screen_candidate
from screener.storage import save_screening, list_screenings, get_screening, delete_screening, clear_all_screenings
from screener.fairness import get_fairness_audit, ACADEMIC_DISCLAIMER
from screener.demo_data import DEMO_JOB, DEMO_CANDIDATES

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload limit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, 'sample_resumes')

@app.route('/')
def index():
    return render_template('index.html', disclaimer=ACADEMIC_DISCLAIMER)

@app.route('/api/demo-data', methods=['GET'])
def get_demo_data():
    """Returns the pre-configured job description and fictional candidate resumes."""
    # List sample files available on disk
    sample_files = []
    if os.path.exists(SAMPLE_DIR):
        sample_files = os.listdir(SAMPLE_DIR)
        
    return jsonify({
        'job': DEMO_JOB,
        'candidates': DEMO_CANDIDATES,
        'sample_files': sample_files
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_resumes():
    """
    Analyzes submitted resumes against the job description.
    Supports uploaded files (PDF, DOCX, TXT) and/or bundled demo candidates.
    """
    job_title = request.form.get('job_title', 'Full-Stack Developer').strip()
    job_description = request.form.get('job_description', '').strip()
    include_demos = request.form.get('include_demos', 'false').lower() == 'true'
    
    if not job_description:
        return jsonify({'error': 'Job description is required.'}), 400

    candidates_to_process = []

    # 1. Process uploaded files
    uploaded_files = request.files.getlist('files')
    for file_storage in uploaded_files:
        if file_storage and file_storage.filename:
            fname = secure_filename(file_storage.filename)
            try:
                content_bytes = file_storage.read()
                if not content_bytes:
                    continue
                cand_name, extracted_text, err = parse_resume_file(fname, content_bytes)
                if err:
                    return jsonify({'error': f"Error parsing {fname}: {err}"}), 400
                candidates_to_process.append({
                    'name': cand_name,
                    'text': extracted_text,
                    'filename': fname
                })
            except Exception as e:
                return jsonify({'error': f"Failed reading {fname}: {str(e)}"}), 500

    # 2. Process demo candidates if requested or if no files uploaded
    if include_demos or not candidates_to_process:
        # Check if selected demo names were provided
        selected_demos_raw = request.form.get('selected_demos')
        if selected_demos_raw:
            try:
                selected_demos = json.loads(selected_demos_raw)
                for dc in DEMO_CANDIDATES:
                    if dc['name'] in selected_demos:
                        candidates_to_process.append(dc)
            except Exception:
                candidates_to_process.extend(DEMO_CANDIDATES)
        elif not candidates_to_process:
            candidates_to_process.extend(DEMO_CANDIDATES)

    if not candidates_to_process:
        return jsonify({'error': 'No resumes were provided for analysis.'}), 400

    # 3. Evaluate each candidate through explainable scoring engine
    results = []
    for cand in candidates_to_process:
        res = screen_candidate(
            candidate_name=cand['name'],
            resume_raw_text=cand['text'],
            job_title=job_title,
            job_description=job_description
        )
        res['source_filename'] = cand.get('filename', f"{cand['name'].replace(' ', '_')}.txt")
        results.append(res)

    # Sort results descending by overall score
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # Assign ranking ranks
    for idx, cand in enumerate(results, 1):
        cand['rank'] = idx

    # Save to local storage
    screening_id = save_screening(job_title, job_description, results)

    return jsonify({
        'status': 'success',
        'screening_id': screening_id,
        'job_title': job_title,
        'candidate_count': len(results),
        'results': results,
        'fairness_audit': get_fairness_audit()
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Retrieves list of past screenings."""
    screenings = list_screenings()
    return jsonify({'screenings': screenings})

@app.route('/api/history/<screening_id>', methods=['GET'])
def get_history_detail(screening_id):
    """Retrieves full details of a saved screening."""
    detail = get_screening(screening_id)
    if not detail:
        return jsonify({'error': 'Screening record not found.'}), 404
    return jsonify(detail)

@app.route('/api/history/<screening_id>', methods=['DELETE'])
def delete_history_item(screening_id):
    """Deletes a specific screening."""
    success = delete_screening(screening_id)
    if not success:
        return jsonify({'error': 'Could not delete screening.'}), 404
    return jsonify({'status': 'deleted', 'id': screening_id})

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clears all screening history."""
    clear_all_screenings()
    return jsonify({'status': 'cleared'})

@app.route('/api/fairness-audit', methods=['GET'])
def fairness_audit():
    """Returns the ethical AI audit policies and dimensions."""
    return jsonify(get_fairness_audit())

@app.route('/api/export/<screening_id>/<format_type>', methods=['GET'])
def export_results(screening_id, format_type):
    """Exports screening results as JSON or CSV."""
    detail = get_screening(screening_id)
    if not detail:
        return jsonify({'error': 'Screening not found.'}), 404

    candidates = detail.get('candidates', [])
    clean_title = detail.get('job_title', 'screening').replace(' ', '_').lower()

    if format_type.lower() == 'json':
        return Response(
            json.dumps(detail, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename=screening_{clean_title}_{screening_id}.json'}
        )
    elif format_type.lower() == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        # CSV Headers
        writer.writerow([
            'Rank', 'Candidate Name', 'Overall Match Score (%)', 'Recommendation',
            'Skills Score (45%)', 'Text Similarity Score (25%)', 'Relevant Experience Score (20%)',
            'Education Score (10%)', 'Matched Skills Count', 'Missing Skills Count',
            'Matched Skills', 'Missing Skills', 'Estimated Experience Years', 'Highest Degree'
        ])
        for c in candidates:
            b = c.get('breakdown', {})
            writer.writerow([
                c.get('rank', ''),
                c.get('candidate_name', ''),
                c.get('overall_score', ''),
                c.get('recommendation', ''),
                b.get('skills', {}).get('score', ''),
                b.get('text_similarity', {}).get('score', ''),
                b.get('relevant_experience', {}).get('score', ''),
                b.get('education', {}).get('score', ''),
                len(c.get('matched_skills', [])),
                len(c.get('missing_skills', [])),
                "; ".join(c.get('matched_skills', [])),
                "; ".join(c.get('missing_skills', [])),
                b.get('relevant_experience', {}).get('estimated_years', ''),
                b.get('education', {}).get('highest_degree', '')
            ])
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=screening_{clean_title}_{screening_id}.csv'}
        )
    else:
        return jsonify({'error': 'Supported export formats are json and csv.'}), 400

@app.route('/sample_resumes/<filename>')
def download_sample(filename):
    """Serves sample resume files for user testing."""
    return send_from_directory(SAMPLE_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    print("=" * 60)
    print("AI RESUME SCREENER - LOCAL SERVER STARTING")
    print("Access application at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
