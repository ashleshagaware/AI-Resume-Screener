# End-to-End Flow Verification for AI Resume Screener

import urllib.request
import urllib.parse
import json
import os
import mimetypes
import uuid

BASE_URL = "http://127.0.0.1:5000"

def test_get(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200, f"Failed GET {endpoint}: {response.status}"
        return response.read()

def test_full_flow():
    print("\n" + "=" * 65)
    print("STARTING FULL END-TO-END FLOW TEST")
    print("=" * 65)

    # 1. Test Home / Dashboard Page
    print("\n[Step 1] Verifying Dashboard & Web UI (GET /)...")
    html = test_get("/").decode("utf-8")
    assert "AI Resume Screener" in html
    assert "Dashboard / Overview" in html
    assert "New Screening" in html
    assert "Candidate Comparison" in html
    assert "Screening History" in html
    assert "Methodology / About" in html
    assert "Academic Decision-Support Prototype" in html
    print("  -> Dashboard and all 6 views present in HTML.")

    # 2. Test Demo Data API
    print("\n[Step 2] Verifying Demo Data API (GET /api/demo-data)...")
    demo_data_bytes = test_get("/api/demo-data")
    demo_data = json.loads(demo_data_bytes.decode("utf-8"))
    assert "job" in demo_data
    assert "candidates" in demo_data
    assert len(demo_data["candidates"]) == 5
    print(f"  -> Successfully loaded Demo Job: '{demo_data['job']['title']}' with {len(demo_data['candidates'])} demo candidates.")

    # 3. Test Running Decision Analysis with Demo Job + Demo Resumes
    print("\n[Step 3] Testing Analysis: Load Demo Job -> Add Demo Resumes -> Run Decision Analysis...")
    form_data = urllib.parse.urlencode({
        "job_title": demo_data["job"]["title"],
        "job_description": demo_data["job"]["description"],
        "include_demos": "true",
        "selected_demos": json.dumps([c["name"] for c in demo_data["candidates"]])
    }).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}/api/analyze", data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        analysis_result = json.loads(resp.read().decode("utf-8"))

    screening_id = analysis_result["screening_id"]
    candidates = analysis_result["results"]
    print(f"  -> Analysis completed successfully!")
    print(f"  -> Screening ID: {screening_id}")
    print(f"  -> Candidates evaluated: {len(candidates)}")

    top = candidates[0]
    print(f"  -> Top Ranked: {top['candidate_name']} ({top['overall_score']}%) - {top['recommendation']}")
    b = top['breakdown']
    print(f"     [Skills: {b['skills']['score']}% (45%), Sim: {b['text_similarity']['score']}% (25%), Exp: {b['relevant_experience']['score']}% (20%), Edu: {b['education']['score']}% (10%)]")
    assert top["overall_score"] > 80.0, "Alex Rivera should score >80%"
    assert len(top["matched_skills"]) > 10, "Should detect multiple matched skills"
    assert "strengths" in top and len(top["strengths"]) > 0

    # 4. Test Multi-Part Real File Upload (PDF & DOCX)
    print("\n[Step 4] Testing Real Document File Upload (PDF & DOCX)...")
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_resumes")
    pdf_path = os.path.join(sample_dir, "David_Kim_Resume.pdf")
    docx_path = os.path.join(sample_dir, "Priya_Sharma_Resume.docx")

    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()

    def add_field(name, value):
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(f"{value}\r\n".encode())

    def add_file(name, filepath):
        filename = os.path.basename(filepath)
        mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
        with open(filepath, "rb") as f:
            body.extend(f.read())
        body.extend(b"\r\n")

    add_field("job_title", "Frontend Software Engineer")
    add_field("job_description", "Requirements: React, TypeScript, Node.js, SQL, Git, 3+ years experience, Bachelor degree.")
    add_file("files", pdf_path)
    add_file("files", docx_path)
    body.extend(f"--{boundary}--\r\n".encode())

    req_upload = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req_upload) as resp_upload:
        assert resp_upload.status == 200
        upload_result = json.loads(resp_upload.read().decode("utf-8"))
        print(f"  -> Upload analysis succeeded! Processed {len(upload_result['results'])} uploaded documents.")
        for uc in upload_result["results"]:
            print(f"     Candidate from file: {uc['candidate_name']} ({uc['overall_score']}%)")

    # 5. Test History Persistence API
    print("\n[Step 5] Verifying Screening History API (GET /api/history)...")
    history_data = json.loads(test_get("/api/history").decode("utf-8"))
    screenings = history_data.get("screenings", [])
    assert len(screenings) >= 2, "History should contain recorded runs"
    print(f"  -> Found {len(screenings)} persisted screening sessions in history.")

    # 6. Test History Detail & Export
    print("\n[Step 6] Testing History Detail & Export (CSV and JSON)...")
    detail = json.loads(test_get(f"/api/history/{screening_id}").decode("utf-8"))
    assert detail["id"] == screening_id
    print(f"  -> Detail for {screening_id} loaded successfully.")

    csv_data = test_get(f"/api/export/{screening_id}/csv").decode("utf-8")
    assert "Overall Match Score (%)" in csv_data
    assert "Alex Rivera" in csv_data
    print("  -> CSV export generated with correct schema.")

    json_data = json.loads(test_get(f"/api/export/{screening_id}/json").decode("utf-8"))
    assert json_data["id"] == screening_id
    print("  -> JSON export verified.")

    # 7. Test Fairness Audit API
    print("\n[Step 7] Testing Fairness & Ethical AI Endpoint (GET /api/fairness-audit)...")
    fairness = json.loads(test_get("/api/fairness-audit").decode("utf-8"))
    assert len(fairness["protected_attributes_excluded"]) == 6
    print("  -> Fairness audit verified: all 6 protected dimensions excluded.")

    print("\n" + "=" * 65)
    print("ALL END-TO-END FLOW TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    test_full_flow()
