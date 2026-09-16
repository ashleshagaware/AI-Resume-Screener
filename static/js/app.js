// AI Resume Screener - Frontend Interactive Controller

let state = {
  currentView: 'dashboard',
  demoData: null,
  stagedFiles: [], // File objects
  stagedDemoCandidates: [], // Names of demo candidates added
  currentScreening: null, // Full screening result object
  selectedForComparison: new Set(),
  dashboardChartInstance: null,
  comparisonRadarInstance: null
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupDropZone();
  setupFormHandlers();
  await fetchDemoData();
  await loadHistory();
  
  // Hash routing
  const initialHash = window.location.hash.replace('#', '') || 'dashboard';
  switchView(initialHash);
  
  lucide.createIcons();
});

// --- API Calls ---
async function fetchDemoData() {
  try {
    const res = await fetch('/api/demo-data');
    if (res.ok) {
      state.demoData = await res.json();
    }
  } catch (err) {
    console.error('Failed to load demo data:', err);
  }
}

// --- Navigation & Views ---
function setupNavigation() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const view = link.getAttribute('data-view');
      switchView(view);
    });
  });

  document.querySelectorAll('.nav-link-trigger').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const target = trigger.getAttribute('data-target');
      switchView(target);
    });
  });

  // Quick demo button in header
  const quickDemoBtn = document.getElementById('btn-quick-demo');
  if (quickDemoBtn) {
    quickDemoBtn.addEventListener('click', () => loadDemoScreening());
  }

  // Export dropdown
  const exportBtn = document.getElementById('btn-export-dropdown');
  const exportMenu = document.getElementById('export-menu');
  if (exportBtn && exportMenu) {
    exportBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      exportMenu.classList.toggle('hidden');
    });
    document.addEventListener('click', () => exportMenu.classList.add('hidden'));
  }
}

function switchView(viewName) {
  state.currentView = viewName;
  window.location.hash = viewName;

  // Update Nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-view') === viewName) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Toggle Panels
  document.querySelectorAll('.view-panel').forEach(panel => {
    panel.classList.add('hidden');
  });

  const targetPanel = document.getElementById(`view-${viewName}`);
  if (targetPanel) {
    targetPanel.classList.remove('hidden');
  }

  // Update Header title
  const titles = {
    'dashboard': 'Dashboard / Overview',
    'new-screening': 'New Candidate Screening',
    'results': 'Candidate Screening Results',
    'comparison': 'Candidate Comparison Matrix',
    'history': 'Screening History & Audit',
    'about': 'Methodology & Explainable AI'
  };
  document.getElementById('current-view-title').innerText = titles[viewName] || 'AI Screener';

  // Refresh icons
  lucide.createIcons();

  // View specific refreshes
  if (viewName === 'dashboard') {
    updateDashboardUI();
  } else if (viewName === 'comparison') {
    renderComparisonView();
  } else if (viewName === 'history') {
    loadHistory();
  }
}

// --- Drag and Drop File Handling ---
function setupDropZone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('border-indigo-500', 'bg-indigo-50/50');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-indigo-500', 'bg-indigo-50/50');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleAddedFiles(e.dataTransfer.files);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
      handleAddedFiles(fileInput.files);
    }
  });
}

function handleAddedFiles(files) {
  const validExts = ['.pdf', '.docx', '.doc', '.txt'];
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (validExts.includes(ext)) {
      state.stagedFiles.push(file);
    } else {
      alert(`Skipped ${file.name}: unsupported file type. Use PDF, DOCX, or TXT.`);
    }
  }
  renderStagedResumes();
}

function renderStagedResumes() {
  const container = document.getElementById('staged-resumes-container');
  const counter = document.getElementById('selected-files-counter');
  container.innerHTML = '';

  const totalCount = state.stagedFiles.length + state.stagedDemoCandidates.length;
  counter.innerText = `${totalCount} candidate(s) staged`;

  // Render demo candidates
  state.stagedDemoCandidates.forEach((candName, idx) => {
    const row = document.createElement('div');
    row.className = 'flex items-center justify-between p-2.5 bg-indigo-50/60 border border-indigo-200 rounded-lg text-xs';
    row.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="p-1 rounded bg-indigo-100 text-indigo-700 font-bold text-[10px]">DEMO</span>
        <span class="font-semibold text-slate-800">${candName}</span>
        <span class="text-slate-500 text-[11px]">(Fictional Full-Stack Candidate)</span>
      </div>
      <button type="button" onclick="removeDemoCandidate(${idx})" class="text-slate-400 hover:text-rose-600 p-1">
        <i data-lucide="x" class="w-4 h-4"></i>
      </button>
    `;
    container.appendChild(row);
  });

  // Render uploaded files
  state.stagedFiles.forEach((file, idx) => {
    const ext = file.name.split('.').pop().toUpperCase();
    const sizeKB = (file.size / 1024).toFixed(1);
    const row = document.createElement('div');
    row.className = 'flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg text-xs';
    row.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="p-1 rounded bg-slate-100 text-slate-700 font-bold text-[10px]">${ext}</span>
        <span class="font-semibold text-slate-800">${file.name}</span>
        <span class="text-slate-500 text-[11px]">(${sizeKB} KB)</span>
      </div>
      <button type="button" onclick="removeUploadedFile(${idx})" class="text-slate-400 hover:text-rose-600 p-1">
        <i data-lucide="x" class="w-4 h-4"></i>
      </button>
    `;
    container.appendChild(row);
  });

  lucide.createIcons();
}

function removeUploadedFile(index) {
  state.stagedFiles.splice(index, 1);
  renderStagedResumes();
}

function removeDemoCandidate(index) {
  state.stagedDemoCandidates.splice(index, 1);
  renderStagedResumes();
}

function resetNewScreeningForm() {
  document.getElementById('form-screening').reset();
  state.stagedFiles = [];
  state.stagedDemoCandidates = [];
  renderStagedResumes();
}

// --- Setup Form Handlers ---
function setupFormHandlers() {
  // "Load Demo Job" button
  document.getElementById('btn-load-demo-job').addEventListener('click', () => {
    if (!state.demoData) return;
    document.getElementById('input-job-title').value = state.demoData.job.title;
    document.getElementById('input-job-description').value = state.demoData.job.description;
  });

  // "Add Demo Resumes" button
  document.getElementById('btn-add-demo-resumes').addEventListener('click', () => {
    if (!state.demoData) return;
    state.stagedDemoCandidates = state.demoData.candidates.map(c => c.name);
    renderStagedResumes();
  });

  // Form Submit
  const form = document.getElementById('form-screening');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const jobTitle = document.getElementById('input-job-title').value.trim();
    const jobDesc = document.getElementById('input-job-description').value.trim();

    if (!jobDesc) {
      alert('Please provide a job description.');
      return;
    }

    if (state.stagedFiles.length === 0 && state.stagedDemoCandidates.length === 0) {
      alert('Please upload at least one resume or click "Add Demo Resumes".');
      return;
    }

    await runScreeningAnalysis(jobTitle, jobDesc);
  });

  // Filter and Sort in Results view
  document.getElementById('filter-tier-select').addEventListener('change', () => renderResultsCards());
  document.getElementById('sort-by-select').addEventListener('change', () => renderResultsCards());

  // Compare Selected Button
  document.getElementById('btn-compare-selected').addEventListener('click', () => {
    if (state.selectedForComparison.size === 0) {
      // Auto select top 2 or 3 candidates
      if (state.currentScreening && state.currentScreening.candidates.length > 0) {
        state.selectedForComparison.clear();
        state.currentScreening.candidates.slice(0, 3).forEach(c => state.selectedForComparison.add(c.candidate_name));
      }
    }
    switchView('comparison');
  });
}

// --- Run Decision Analysis ---
async function runScreeningAnalysis(jobTitle, jobDesc) {
  const loadingModal = document.getElementById('modal-loading');
  const stepText = document.getElementById('loading-step-text');
  const progressBar = document.getElementById('loading-progress-bar');
  loadingModal.classList.remove('hidden');

  // Animation Steps
  const steps = [
    { text: 'Extracting text from resumes (PDF/DOCX/TXT)...', width: '25%' },
    { text: 'Applying demographic-blind fairness sanitization...', width: '45%' },
    { text: 'Matching technical & soft skills taxonomy (45%)...', width: '65%' },
    { text: 'Computing TF-IDF vector text similarity (25%)...', width: '80%' },
    { text: 'Analyzing experience timelines & degree credentials...', width: '95%' }
  ];

  let stepIdx = 0;
  const interval = setInterval(() => {
    if (stepIdx < steps.length) {
      stepText.innerText = steps[stepIdx].text;
      progressBar.style.width = steps[stepIdx].width;
      stepIdx++;
    }
  }, 250);

  try {
    const formData = new FormData();
    formData.append('job_title', jobTitle);
    formData.append('job_description', jobDesc);

    // Append uploaded files
    state.stagedFiles.forEach(file => {
      formData.append('files', file);
    });

    // Append selected demo candidates
    if (state.stagedDemoCandidates.length > 0) {
      formData.append('include_demos', 'true');
      formData.append('selected_demos', JSON.stringify(state.stagedDemoCandidates));
    }

    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData
    });

    clearInterval(interval);
    progressBar.style.width = '100%';

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to complete analysis.');
    }

    // Set current screening state
    state.currentScreening = {
      id: data.screening_id,
      job_title: data.job_title,
      candidates: data.results,
      fairness_audit: data.fairness_audit
    };

    // Auto select top 3 candidates for comparison
    state.selectedForComparison.clear();
    data.results.slice(0, 3).forEach(c => state.selectedForComparison.add(c.candidate_name));

    // Update results UI
    renderResultsView();
    await loadHistory();

    setTimeout(() => {
      loadingModal.classList.add('hidden');
      switchView('results');
    }, 400);

  } catch (err) {
    clearInterval(interval);
    loadingModal.classList.add('hidden');
    alert(`Error: ${err.message}`);
  }
}

// Quick trigger for Demo Screening
async function loadDemoScreening() {
  if (!state.demoData) {
    await fetchDemoData();
  }
  state.stagedFiles = [];
  state.stagedDemoCandidates = state.demoData.candidates.map(c => c.name);
  await runScreeningAnalysis(state.demoData.job.title, state.demoData.job.description);
}

// --- Results View Rendering ---
function renderResultsView() {
  if (!state.currentScreening) return;

  const { id, job_title, candidates } = state.currentScreening;

  document.getElementById('results-job-title').innerText = job_title;
  document.getElementById('results-meta-text').innerText = `Screening ID: ${id} • Candidates Evaluated: ${candidates.length} • Weighted Academic Model`;
  
  // Badge on nav
  const navBadge = document.getElementById('nav-candidate-badge');
  navBadge.innerText = candidates.length;
  navBadge.classList.remove('hidden');

  // Export links
  document.getElementById('export-csv-link').href = `/api/export/${id}/csv`;
  document.getElementById('export-json-link').href = `/api/export/${id}/json`;

  renderResultsCards();
}

function renderResultsCards() {
  if (!state.currentScreening) return;

  const container = document.getElementById('results-cards-container');
  container.innerHTML = '';

  const tierFilter = document.getElementById('filter-tier-select').value;
  const sortBy = document.getElementById('sort-by-select').value;

  let candidates = [...state.currentScreening.candidates];

  // Filtering
  if (tierFilter !== 'all') {
    candidates = candidates.filter(c => c.badge_class === tierFilter);
  }

  // Sorting
  candidates.sort((a, b) => {
    if (sortBy === 'skills') return b.breakdown.skills.score - a.breakdown.skills.score;
    if (sortBy === 'similarity') return b.breakdown.text_similarity.score - a.breakdown.text_similarity.score;
    if (sortBy === 'experience') return b.breakdown.relevant_experience.score - a.breakdown.relevant_experience.score;
    if (sortBy === 'education') return b.breakdown.education.score - a.breakdown.education.score;
    return b.overall_score - a.overall_score;
  });

  updateCompareBadge();

  if (candidates.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500">
        No candidates match the selected filter tier.
      </div>
    `;
    return;
  }

  candidates.forEach((cand) => {
    const isChecked = state.selectedForComparison.has(cand.candidate_name);
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition p-5 space-y-4';

    // Badge styling
    const badgeColors = {
      'success': 'bg-emerald-50 text-emerald-700 border-emerald-200',
      'primary': 'bg-indigo-50 text-indigo-700 border-indigo-200',
      'warning': 'bg-amber-50 text-amber-800 border-amber-200',
      'danger': 'bg-rose-50 text-rose-700 border-rose-200'
    };
    const badgeStyle = badgeColors[cand.badge_class] || 'bg-slate-100 text-slate-800';

    // Render Matched Skills pills (up to 8)
    const matchedPills = cand.matched_skills.slice(0, 8).map(s => 
      `<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-medium">${s}</span>`
    ).join(' ');
    const matchedMore = cand.matched_skills.length > 8 ? `<span class="text-[11px] text-slate-400 font-medium">+${cand.matched_skills.length - 8} more</span>` : '';

    // Render Missing Skills pills (up to 5)
    const missingPills = cand.missing_skills.slice(0, 5).map(s => 
      `<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-medium">${s}</span>`
    ).join(' ');
    const missingMore = cand.missing_skills.length > 5 ? `<span class="text-[11px] text-slate-400 font-medium">+${cand.missing_skills.length - 5} more</span>` : '';

    card.innerHTML = `
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div class="flex items-center gap-3">
          <span class="w-7 h-7 rounded-lg bg-slate-900 text-white font-bold text-xs flex items-center justify-center flex-shrink-0">
            #${cand.rank || 1}
          </span>
          <div>
            <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
              ${cand.candidate_name}
              <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full border ${badgeStyle}">
                ${cand.recommendation}
              </span>
            </h3>
            <p class="text-xs text-slate-400 mt-0.5">Source: ${cand.source_filename || 'Uploaded Resume'}</p>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <div class="text-right">
            <span class="text-xs text-slate-500 block">Overall Match</span>
            <span class="text-2xl font-black text-indigo-600">${cand.overall_score}%</span>
          </div>
          <div class="flex items-center gap-2 pl-3 border-l border-slate-200">
            <label class="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer select-none">
              <input type="checkbox" onchange="toggleCompareCandidate('${cand.candidate_name}', this.checked)" ${isChecked ? 'checked' : ''} class="w-4 h-4 text-indigo-600 rounded border-slate-300">
              <span>Compare</span>
            </label>
            <button onclick="inspectCandidate('${cand.candidate_name}')" class="px-3 py-1.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1">
              <i data-lucide="info" class="w-3.5 h-3.5"></i> Inspect
            </button>
          </div>
        </div>
      </div>

      <!-- 4 Score Dimension Bars -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-lg text-xs">
        <div>
          <div class="flex justify-between text-[11px] text-slate-500 mb-1">
            <span>Skills (45%)</span>
            <strong>${cand.breakdown.skills.score}%</strong>
          </div>
          <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div class="bg-indigo-600 h-1.5 rounded-full" style="width: ${cand.breakdown.skills.score}%"></div>
          </div>
        </div>

        <div>
          <div class="flex justify-between text-[11px] text-slate-500 mb-1">
            <span>Text Similarity (25%)</span>
            <strong>${cand.breakdown.text_similarity.score}%</strong>
          </div>
          <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div class="bg-blue-600 h-1.5 rounded-full" style="width: ${cand.breakdown.text_similarity.score}%"></div>
          </div>
        </div>

        <div>
          <div class="flex justify-between text-[11px] text-slate-500 mb-1">
            <span>Experience (20%)</span>
            <strong>${cand.breakdown.relevant_experience.score}%</strong>
          </div>
          <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div class="bg-emerald-600 h-1.5 rounded-full" style="width: ${cand.breakdown.relevant_experience.score}%"></div>
          </div>
        </div>

        <div>
          <div class="flex justify-between text-[11px] text-slate-500 mb-1">
            <span>Education (10%)</span>
            <strong>${cand.breakdown.education.score}%</strong>
          </div>
          <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div class="bg-purple-600 h-1.5 rounded-full" style="width: ${cand.breakdown.education.score}%"></div>
          </div>
        </div>
      </div>

      <!-- Skills and Insights Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div>
          <div class="font-semibold text-slate-700 mb-1.5 flex items-center gap-1">
            <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i> Matched Skills (${cand.matched_skills.length}):
          </div>
          <div class="flex flex-wrap gap-1">
            ${matchedPills || '<span class=\"text-slate-400\">None detected</span>'}
            ${matchedMore}
          </div>
        </div>

        <div>
          <div class="font-semibold text-slate-700 mb-1.5 flex items-center gap-1">
            <i data-lucide="x" class="w-3.5 h-3.5 text-amber-500"></i> Missing Skills (${cand.missing_skills.length}):
          </div>
          <div class="flex flex-wrap gap-1">
            ${missingPills || '<span class=\"text-slate-400\">None! Complete coverage</span>'}
            ${missingMore}
          </div>
        </div>
      </div>
    `;

    container.appendChild(card);
  });

  lucide.createIcons();
}

function toggleCompareCandidate(name, isChecked) {
  if (isChecked) {
    state.selectedForComparison.add(name);
  } else {
    state.selectedForComparison.delete(name);
  }
  updateCompareBadge();
}

function updateCompareBadge() {
  const badge = document.getElementById('compare-count-badge');
  if (badge) {
    badge.innerText = state.selectedForComparison.size;
  }
}

// --- Candidate Deep Inspection Modal ---
function inspectCandidate(candName) {
  if (!state.currentScreening) return;
  const cand = state.currentScreening.candidates.find(c => c.candidate_name === candName);
  if (!cand) return;

  const modal = document.getElementById('modal-candidate-detail');
  document.getElementById('modal-rank-badge').innerText = `Rank #${cand.rank || 1}`;
  document.getElementById('modal-candidate-name').innerText = cand.candidate_name;
  document.getElementById('modal-recommendation-text').innerText = cand.recommendation;
  document.getElementById('modal-overall-score').innerText = `${cand.overall_score}%`;

  const b = cand.breakdown;
  document.getElementById('modal-score-skills').innerText = `${b.skills.score}%`;
  document.getElementById('modal-contrib-skills').innerText = `+${b.skills.weighted_contribution} pts`;

  document.getElementById('modal-score-sim').innerText = `${b.text_similarity.score}%`;
  document.getElementById('modal-contrib-sim').innerText = `+${b.text_similarity.weighted_contribution} pts`;

  document.getElementById('modal-score-exp').innerText = `${b.relevant_experience.score}%`;
  document.getElementById('modal-contrib-exp').innerText = `+${b.relevant_experience.weighted_contribution} pts`;

  document.getElementById('modal-score-edu').innerText = `${b.education.score}%`;
  document.getElementById('modal-contrib-edu').innerText = `+${b.education.weighted_contribution} pts`;

  // Matched Skills
  const matchedContainer = document.getElementById('modal-matched-skills');
  matchedContainer.innerHTML = cand.matched_skills.map(s => 
    `<span class="px-2 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium">${s}</span>`
  ).join('');

  // Missing Skills
  const missingContainer = document.getElementById('modal-missing-skills');
  missingContainer.innerHTML = cand.missing_skills.length ? cand.missing_skills.map(s => 
    `<span class="px-2 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200 text-xs font-medium">${s}</span>`
  ).join('') : '<span class="text-slate-400">Full requirement coverage</span>';

  // Summaries
  document.getElementById('modal-exp-summary').innerText = b.relevant_experience.summary;
  document.getElementById('modal-edu-summary').innerText = `Highest Level: ${b.education.highest_degree}${b.education.certifications.length ? ' • Certifications: ' + b.education.certifications.join(', ') : ''}`;

  // Strengths
  const strengthsList = document.getElementById('modal-strengths-list');
  strengthsList.innerHTML = cand.strengths.map(st => `<li>${st}</li>`).join('');

  // Areas for improvement
  const impList = document.getElementById('modal-improvement-list');
  impList.innerHTML = cand.areas_for_improvement.map(imp => `<li>${imp}</li>`).join('');

  modal.classList.remove('hidden');
  lucide.createIcons();
}

function closeCandidateModal() {
  document.getElementById('modal-candidate-detail').classList.add('hidden');
}

// --- Comparison View Rendering ---
function renderComparisonView() {
  if (!state.currentScreening) {
    switchView('dashboard');
    return;
  }

  const allCandidates = state.currentScreening.candidates;
  
  // Render selector pills
  const pillContainer = document.getElementById('comparison-selector-pills');
  pillContainer.innerHTML = '';

  allCandidates.forEach(c => {
    const isSelected = state.selectedForComparison.has(c.candidate_name);
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = `px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
      isSelected 
        ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs' 
        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
    }`;
    pill.innerText = `${c.candidate_name} (${c.overall_score}%)`;
    pill.onclick = () => {
      if (isSelected) {
        state.selectedForComparison.delete(c.candidate_name);
      } else {
        state.selectedForComparison.add(c.candidate_name);
      }
      renderComparisonView();
    };
    pillContainer.appendChild(pill);
  });

  const compared = allCandidates.filter(c => state.selectedForComparison.has(c.candidate_name));

  if (compared.length === 0) {
    // Select first two candidates
    allCandidates.slice(0, 2).forEach(c => state.selectedForComparison.add(c.candidate_name));
    renderComparisonView();
    return;
  }

  // 1. Render Radar Chart
  renderRadarChart(compared);

  // 2. Render Side-by-side Table
  const tableHead = document.getElementById('comp-table-head');
  tableHead.innerHTML = '<th class="py-2.5 pr-4 text-slate-500 font-semibold">Dimension</th>' +
    compared.map(c => `<th class="py-2.5 px-3 text-slate-900 font-bold text-center">${c.candidate_name}</th>`).join('');

  const dimensions = [
    { label: 'Overall Score', getVal: c => `<strong class="text-indigo-600">${c.overall_score}%</strong>` },
    { label: 'Skills Match (45%)', getVal: c => `${c.breakdown.skills.score}%` },
    { label: 'Text Similarity (25%)', getVal: c => `${c.breakdown.text_similarity.score}%` },
    { label: 'Experience (20%)', getVal: c => `${c.breakdown.relevant_experience.score}%` },
    { label: 'Education (10%)', getVal: c => `${c.breakdown.education.score}%` },
    { label: 'Est. Experience', getVal: c => `~${c.breakdown.relevant_experience.estimated_years} yrs` },
    { label: 'Highest Degree', getVal: c => c.breakdown.education.highest_degree },
    { label: 'Recommendation', getVal: c => `<span class="px-2 py-0.5 rounded text-[10px] font-bold ${c.badge_class === 'success' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-800'}">${c.recommendation.split('-')[0]}</span>` }
  ];

  const tableBody = document.getElementById('comp-table-body');
  tableBody.innerHTML = dimensions.map(d => `
    <tr>
      <td class="py-2.5 pr-4 text-slate-600 font-medium">${d.label}</td>
      ${compared.map(c => `<td class="py-2.5 px-3 text-center">${d.getVal(c)}</td>`).join('')}
    </tr>
  `).join('');

  // 3. Render Skills Coverage Matrix
  const requiredSkills = Array.from(new Set([
    ...allCandidates[0].matched_skills,
    ...allCandidates[0].missing_skills
  ])).sort();

  const matrixHead = document.getElementById('matrix-table-head');
  matrixHead.innerHTML = '<th class="py-2.5 px-3 font-semibold text-slate-700">Required Competency</th>' +
    compared.map(c => `<th class="py-2.5 px-3 text-slate-900 font-bold text-center">${c.candidate_name}</th>`).join('');

  const matrixBody = document.getElementById('matrix-table-body');
  matrixBody.innerHTML = requiredSkills.map(skill => {
    const cells = compared.map(c => {
      const hasSkill = c.matched_skills.includes(skill);
      return hasSkill
        ? `<td class="py-2 px-3 text-center text-emerald-600 font-bold"><i data-lucide="check" class="w-4 h-4 mx-auto inline"></i></td>`
        : `<td class="py-2 px-3 text-center text-slate-300 font-bold"><i data-lucide="minus" class="w-4 h-4 mx-auto inline"></i></td>`;
    }).join('');

    return `
      <tr>
        <td class="py-2 px-3 text-slate-700 font-medium">${skill}</td>
        ${cells}
      </tr>
    `;
  }).join('');

  lucide.createIcons();
}

function renderRadarChart(candidates) {
  const ctx = document.getElementById('comparisonRadarChart').getContext('2d');
  if (state.comparisonRadarInstance) {
    state.comparisonRadarInstance.destroy();
  }

  const colors = [
    { bg: 'rgba(99, 102, 241, 0.2)', border: 'rgb(99, 102, 241)' },
    { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgb(16, 185, 129)' },
    { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgb(245, 158, 11)' },
    { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgb(239, 68, 68)' },
    { bg: 'rgba(168, 85, 247, 0.2)', border: 'rgb(168, 85, 247)' }
  ];

  const datasets = candidates.slice(0, 5).map((c, idx) => {
    const col = colors[idx % colors.length];
    return {
      label: c.candidate_name,
      data: [
        c.overall_score,
        c.breakdown.skills.score,
        c.breakdown.text_similarity.score,
        c.breakdown.relevant_experience.score,
        c.breakdown.education.score
      ],
      backgroundColor: col.bg,
      borderColor: col.border,
      borderWidth: 2,
      pointRadius: 3
    };
  });

  state.comparisonRadarInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Overall', 'Skills (45%)', 'Similarity (25%)', 'Experience (20%)', 'Education (10%)'],
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { stepSize: 25, display: false },
          grid: { color: 'rgba(0,0,0,0.05)' }
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 12, font: { size: 11 } }
        }
      }
    }
  });
}

// --- Dashboard View Updates ---
function updateDashboardUI() {
  if (state.currentScreening) {
    const cands = state.currentScreening.candidates;
    document.getElementById('chart-job-label').innerText = state.currentScreening.job_title;

    // Render bar chart for current candidates
    const ctx = document.getElementById('dashboardScoreChart').getContext('2d');
    if (state.dashboardChartInstance) {
      state.dashboardChartInstance.destroy();
    }

    state.dashboardChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: cands.map(c => c.candidate_name),
        datasets: [
          {
            label: 'Overall Match (%)',
            data: cands.map(c => c.overall_score),
            backgroundColor: cands.map(c => {
              if (c.overall_score >= 80) return '#10b981';
              if (c.overall_score >= 65) return '#6366f1';
              if (c.overall_score >= 50) return '#f59e0b';
              return '#f43f5e';
            }),
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 0, max: 100, ticks: { stepSize: 20 } },
          x: { grid: { display: false } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
}

// --- History Persistence & Management ---
async function loadHistory() {
  try {
    const res = await fetch('/api/history');
    if (!res.ok) return;

    const data = await res.json();
    const screenings = data.screenings || [];

    // Update nav badge
    document.getElementById('nav-history-badge').innerText = screenings.length;

    // Update Dashboard KPIs
    document.getElementById('kpi-total-screenings').innerText = screenings.length;
    const totalCandidatesCount = screenings.reduce((acc, s) => acc + s.candidate_count, 0);
    document.getElementById('kpi-total-candidates').innerText = totalCandidatesCount;
    
    if (screenings.length > 0) {
      const avg = Math.round(screenings.reduce((acc, s) => acc + (s.average_score || 0), 0) / screenings.length);
      document.getElementById('kpi-avg-score').innerText = `${avg}%`;
    }

    // Render History Table
    const tbody = document.getElementById('history-table-body');
    const emptyState = document.getElementById('history-empty-state');
    tbody.innerHTML = '';

    if (screenings.length === 0) {
      emptyState.classList.remove('hidden');
      return;
    } else {
      emptyState.classList.add('hidden');
    }

    screenings.forEach(s => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-50 transition';
      tr.innerHTML = `
        <td class="py-3 px-4 font-mono text-[11px] text-slate-500">${s.timestamp}</td>
        <td class="py-3 px-4 font-semibold text-slate-800">${s.job_title}</td>
        <td class="py-3 px-4 text-center font-bold text-slate-700">${s.candidate_count}</td>
        <td class="py-3 px-4 text-slate-700">
          <span class="font-medium">${s.top_candidate}</span> 
          <span class="text-indigo-600 font-bold text-[11px]">(${s.top_score}%)</span>
        </td>
        <td class="py-3 px-4 text-center font-bold text-slate-700">${s.average_score}%</td>
        <td class="py-3 px-4 text-right space-x-2">
          <button onclick="reloadScreening('${s.id}')" class="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded font-semibold text-[11px] transition">
            View
          </button>
          <a href="/api/export/${s.id}/csv" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-semibold text-[11px] transition inline-block">
            CSV
          </a>
          <button onclick="deleteHistoryItem('${s.id}')" class="p-1 text-slate-400 hover:text-rose-600 rounded transition inline-block align-middle">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    lucide.createIcons();
  } catch (err) {
    console.error('Failed to load history:', err);
  }
}

async function reloadScreening(screeningId) {
  try {
    const res = await fetch(`/api/history/${screeningId}`);
    if (!res.ok) throw new Error('Screening record not found');
    const detail = await res.json();

    state.currentScreening = {
      id: detail.id,
      job_title: detail.job_title,
      candidates: detail.candidates,
      fairness_audit: null
    };

    state.selectedForComparison.clear();
    detail.candidates.slice(0, 3).forEach(c => state.selectedForComparison.add(c.candidate_name));

    renderResultsView();
    switchView('results');
  } catch (err) {
    alert(err.message);
  }
}

async function deleteHistoryItem(screeningId) {
  if (!confirm('Are you sure you want to delete this screening record?')) return;
  try {
    await fetch(`/api/history/${screeningId}`, { method: 'DELETE' });
    await loadHistory();
  } catch (err) {
    alert('Failed to delete screening.');
  }
}

async function clearHistoryRecords() {
  if (!confirm('Are you sure you want to clear all screening history records?')) return;
  try {
    await fetch('/api/history/clear', { method: 'POST' });
    await loadHistory();
  } catch (err) {
    alert('Failed to clear history.');
  }
}
