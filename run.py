# AI Resume Screener - Application Launcher

import os
import sys

# Set standard output encoding for Windows compatibility
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure local directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "=" * 65)
    print("AI RESUME SCREENER - LOCAL DECISION SUPPORT APPLICATION")
    print(f"Server running locally at: http://127.0.0.1:{port}")
    print("100% Offline & Deterministic - No API Keys Required")
    print("Demographic-Blind Ethical AI Evaluation Model Active")
    print("=" * 65 + "\n")
    app.run(host='127.0.0.1', port=port, debug=False)
