const BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
    ? 'http://localhost:8000'
    : `http://${window.location.hostname}:8000`;

// View Map
const views = {
    dashboard: renderDashboard,
    evaluate: renderEvaluate,
    history: renderHistory,
    resumes: renderResumes,
    jobs: renderJobs,
    about: renderAbout
};

// State
// State
let currentState = {
    view: 'dashboard',
    lastEvaluation: null,
    recentEvaluations: []
};

// Make navigation globally accessible for inline onclick handlers
window.switchView = switchView;
window.renderDashboard = renderDashboard;
window.renderEvaluate = renderEvaluate;
window.renderFullResult = renderFullResult;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // Setup navigation listeners
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const view = this.getAttribute('data-view');
            if (view) {
                switchView(view);
            }
        });
    });

    // Logo click -> Dashboard
    const logo = document.querySelector('.logo');
    if (logo) {
        logo.style.cursor = 'pointer';
        logo.addEventListener('click', () => switchView('dashboard'));
    }

    // Header Actions removed as requested

    // Search Bar Functionality
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && searchInput.value.trim()) {
                showNotification(`Searching for: ${searchInput.value}`, 'info');
                // Could eventually search in history
            }
        });
    }

    // Backend Status Polling
    checkBackendStatus();
    setInterval(checkBackendStatus, 10000);

    // Initial view
    switchView('dashboard');
});

async function checkBackendStatus() {
    const indicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-value');
    try {
        const res = await fetch(`${BASE_URL}/`, { method: 'GET' });
        if (res.ok) {
            indicator.className = 'status-indicator online';
            statusText.innerText = 'Connected';
            statusText.style.color = '#238636';
        } else {
            throw new Error(`Status ${res.status}`);
        }
    } catch (e) {
        console.warn('Backend connection lost:', e.message);
        indicator.className = 'status-indicator offline';
        statusText.innerText = 'Offline';
        statusText.style.color = '#da3633';
    }
}

function switchView(viewName) {
    console.log(`[SwitchView] Target: ${viewName}`);
    const container = document.getElementById('view-container');
    if (!container) {
        console.error('[SwitchView] Container #view-container not found');
        return;
    }

    container.classList.remove('fade-in');

    // Update nav active state
    document.querySelectorAll('.nav-link').forEach(link => {
        const linkView = link.getAttribute('data-view');
        link.classList.toggle('active', linkView === viewName);
    });

    // Trigger animation
    setTimeout(() => {
        container.innerHTML = '<div class="loader-inline"></div>';
        if (views[viewName]) {
            try {
                views[viewName](container);
            } catch (err) {
                console.error(`[SwitchView] Error rendering ${viewName}:`, err);
                container.innerHTML = `<div class="error-state">Failed to load ${viewName}. Please try refreshing.</div>`;
            }
        }
        container.classList.add('fade-in');
        if (window.lucide) lucide.createIcons();
    }, 50);
}

// ─────────────────────────────────────────────────────────────────────────────
// DASHBOARD VIEW
// ─────────────────────────────────────────────────────────────────────────────

async function renderDashboard(container) {
    console.log('[Dashboard] Rendering started');
    container.innerHTML = `
        <div class="page-header" style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
                <h1 class="page-title">Dashboard Overview</h1>
                <p class="page-subtitle">Real-time insights and system analytics</p>
            </div>
            <button class="icon-btn" id="refresh-dashboard" title="Refresh Data" style="margin-bottom: 5px;">
                <i data-lucide="refresh-cw"></i>
            </button>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card glass-card" onclick="switchView('resumes')">
                <div class="kpi-icon blue"><i data-lucide="file-text"></i></div>
                <div class="kpi-data">
                    <span class="label">Total Resumes</span>
                    <h3 class="value" id="total-resumes">--</h3>
                </div>
            </div>
            <div class="kpi-card glass-card" onclick="switchView('jobs')">
                <div class="kpi-icon violet"><i data-lucide="briefcase"></i></div>
                <div class="kpi-data">
                    <span class="label">Job Positions</span>
                    <h3 class="value" id="total-jobs">--</h3>
                </div>
            </div>
            <div class="kpi-card glass-card" onclick="switchView('history')">
                <div class="kpi-icon green"><i data-lucide="activity"></i></div>
                <div class="kpi-data">
                    <span class="label">Evaluations Run</span>
                    <h3 class="value" id="total-evals">--</h3>
                </div>
            </div>
            <div class="kpi-card glass-card" onclick="switchView('history')">
                <div class="kpi-icon orange"><i data-lucide="star"></i></div>
                <div class="kpi-data">
                    <span class="label">Avg Match Score</span>
                    <h3 class="value" id="avg-score">--</h3>
                </div>
            </div>
        </div>

        <div class="dashboard-charts" id="dashboard-charts-container">
            <div class="chart-container glass-card">
                <h4 class="chart-title">Match Score Distribution</h4>
                <div class="chart-wrapper">
                    <canvas id="distribution-chart"></canvas>
                </div>
            </div>
            <div class="chart-container glass-card">
                <h4 class="chart-title">In-Demand Skills</h4>
                <div class="chart-wrapper">
                    <canvas id="skills-chart"></canvas>
                </div>
            </div>
        </div>
    `;

    if (window.lucide) lucide.createIcons();

    // Event listener for refresh
    const refreshBtn = document.getElementById('refresh-dashboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('[Dashboard] Manual refresh triggered');
            refreshBtn.classList.add('spinning');
            renderDashboard(container).finally(() => {
                setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
            });
        });
    }

    // Fetch data
    try {
        console.log('[Dashboard] Fetching analytics data...');
        const data = await fetchApi('/api/analytics');
        console.log('[Dashboard] Data received:', data);

        if (data && data.summary) {
            updateKpis(data.summary);
            // Small delay to ensure canvas elements are rendered before Chart.js starts
            setTimeout(() => renderCharts(data), 100);
        } else {
            console.warn('[Dashboard] Incomplete data payload:', data);
            throw new Error('Incomplete data received');
        }
    } catch (e) {
        console.error('[Dashboard] Error:', e);
        showNotification('Error loading dashboard data', 'error');
        updateKpis({ total_resumes: 0, total_jobs: 0, total_evaluations: 0, avg_match_score: 0 });

        // Show error message in the charts area if we can't load them
        const chartsArea = document.getElementById('dashboard-charts-container');
        if (chartsArea) {
            chartsArea.innerHTML = `
                <div class="glass-card" style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                    <i data-lucide="alert-triangle" style="width: 48px; height: 48px; color: var(--accent-orange); margin-bottom: 1rem;"></i>
                    <p style="color: var(--text-muted)">Unable to load analytics charts. Check backend connection.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
        }
    }
}

function updateKpis(summary) {
    if (!summary) return;
    console.log('[Dashboard] Updating KPIs:', summary);
    document.getElementById('total-resumes').innerText = summary.total_resumes || 0;
    document.getElementById('total-jobs').innerText = summary.total_jobs || 0;
    document.getElementById('total-evals').innerText = summary.total_evaluations || 0;
    document.getElementById('avg-score').innerText = (summary.avg_match_score || 0).toFixed(0) + '%';
}

// Global chart instances to prevent 'Canvas is already in use' errors
let charts = {
    dist: null,
    skills: null
};

function renderCharts(data) {
    console.log('[Dashboard] Rendering charts with data:', data);
    if (typeof Chart === 'undefined') {
        console.error('[Dashboard] Chart.js NOT found! Ensure CDN is reachable.');
        return;
    }

    // Destroy existing charts if they exist
    if (charts.dist) charts.dist.destroy();
    if (charts.skills) charts.skills.destroy();

    // Score Distribution Chart
    const distCtx = document.getElementById('distribution-chart');
    if (distCtx) {
        const dist = data.score_distribution || {};
        const values = Object.values(dist);
        const hasData = values.some(v => v > 0);

        if (!hasData) {
            distCtx.style.display = 'none';
            const emptyMsg = distCtx.parentElement.querySelector('.empty-msg') || document.createElement('p');
            emptyMsg.className = 'empty-msg';
            emptyMsg.style.textAlign = 'center';
            emptyMsg.style.color = 'var(--text-muted)';
            emptyMsg.style.marginTop = '40px';
            emptyMsg.innerText = 'No evaluation data yet';
            if (!distCtx.parentElement.querySelector('.empty-msg')) distCtx.parentElement.appendChild(emptyMsg);
        } else {
            distCtx.style.display = 'block';
            charts.dist = new Chart(distCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(dist),
                    datasets: [{
                        data: values,
                        backgroundColor: ['#da3633', '#d29922', '#6366f1', '#238636'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#848d97', padding: 20, font: { family: 'Plus Jakarta Sans' } }
                        }
                    },
                    cutout: '70%'
                }
            });
        }
    }

    // Skills Chart
    const skillsCtx = document.getElementById('skills-chart');
    if (skillsCtx) {
        const skills = data.top_skills_in_demand || {};
        const labels = Object.keys(skills);
        const values = Object.values(skills);

        if (labels.length === 0) {
            skillsCtx.style.display = 'none';
            const emptyMsg = skillsCtx.parentElement.querySelector('.empty-msg') || document.createElement('p');
            emptyMsg.className = 'empty-msg';
            emptyMsg.style.textAlign = 'center';
            emptyMsg.style.color = 'var(--text-muted)';
            emptyMsg.style.marginTop = '40px';
            emptyMsg.innerText = 'No skills data found in JDs';
            if (!skillsCtx.parentElement.querySelector('.empty-msg')) skillsCtx.parentElement.appendChild(emptyMsg);
        } else {
            skillsCtx.style.display = 'block';
            const ctx = skillsCtx.getContext('2d');

            // Create gradient
            const gradient = ctx.createLinearGradient(0, 0, 400, 0);
            gradient.addColorStop(0, 'rgba(99, 102, 241, 0.8)');
            gradient.addColorStop(1, 'rgba(139, 92, 246, 0.8)');

            charts.skills = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels.slice(0, 5),
                    datasets: [{
                        label: 'Mentions',
                        data: values.slice(0, 5),
                        backgroundColor: gradient,
                        borderColor: '#6366f1',
                        borderWidth: 1,
                        borderRadius: 6,
                        barThickness: 16,
                        hoverBackgroundColor: 'rgba(139, 92, 246, 1)'
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 2000,
                        easing: 'easeOutQuart'
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(13, 17, 23, 0.95)',
                            titleFont: { family: 'Plus Jakarta Sans', size: 13, weight: '700' },
                            bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
                            padding: 12,
                            borderColor: 'rgba(99, 102, 241, 0.3)',
                            borderWidth: 1,
                            displayColors: false
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#848d97', font: { family: 'Plus Jakarta Sans' } },
                            grid: { color: 'rgba(48, 54, 61, 0.3)', drawBorder: false },
                            beginAtZero: true
                        },
                        y: {
                            ticks: {
                                color: '#e6edf3',
                                font: { family: 'Plus Jakarta Sans', weight: '600', size: 12 }
                            },
                            grid: { display: false, drawBorder: false }
                        }
                    }
                }
            });
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// EVALUATE VIEW
// ─────────────────────────────────────────────────────────────────────────────

function renderEvaluate(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Evaluate Resume</h1>
            <p class="page-subtitle">Run a high-precision AI evaluation against job requirements</p>
        </div>

        <div class="evaluation-form-grid">
            <div class="form-card glass-card">
                <h4 class="form-title"><i data-lucide="file-up"></i> Candidate Details</h4>
                <div class="upload-zone" id="resume-upload-zone">
                    <input type="file" id="resume-file" hidden accept=".pdf,.docx,.txt,.png,.jpg,.jpeg">
                    <div id="resume-preview-container">
                        <i data-lucide="upload-cloud"></i>
                        <p>Click to upload or drag & drop Resume</p>
                        <span>PDF, DOCX, TXT, IMG (Max 5MB)</span>
                    </div>
                </div>
                <div class="separator"><span>OR</span></div>
                <textarea id="resume-text" placeholder="Paste resume text here..."></textarea>
            </div>

            <div class="form-card glass-card">
                <h4 class="form-title"><i data-lucide="briefcase"></i> Job Requirements</h4>
                <div class="upload-zone" id="jd-upload-zone" style="padding: 1rem; margin-bottom: 1.5rem;">
                    <input type="file" id="jd-file" hidden accept=".pdf,.docx,.txt,.png,.jpg,.jpeg">
                    <div id="jd-preview-container">
                        <i data-lucide="file-text"></i>
                        <p style="font-size: 0.85rem;">Upload JD File (Optional OCR)</p>
                    </div>
                </div>
                <div class="input-group">
                    <label>Job Title</label>
                    <input type="text" id="jd-title" placeholder="e.g. Senior Machine Learning Engineer">
                </div>
                <div class="input-group">
                    <label>Company (Optional)</label>
                    <input type="text" id="jd-company" placeholder="e.g. Meta Labs">
                </div>
                <div class="input-group">
                    <label>Job Description</label>
                    <textarea id="jd-text" placeholder="Kindly enter your Job description here..." style="height: 120px;"></textarea>
                </div>
            </div>
        </div>

        <div class="action-footer">
            <button id="run-eval-btn" class="primary-btn pulse">
                <i data-lucide="zap"></i> Run Evaluation
            </button>
        </div>

        <div id="eval-loading" class="hidden">
            <div class="loader-overlay">
                <div class="loader-content">
                    <div class="spinner"></div>
                    <p>AI Agents are analyzing documents...</p>
                    <span style="font-size: 0.8rem; color: var(--text-muted); margin-top: 10px;">This may take up to 60 seconds</span>
                    <div class="stepper" id="eval-stepper">
                        <!-- Step items -->
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('run-eval-btn').addEventListener('click', handleRunEvaluation);

    // Resume Upload zone trigger
    const resumeZone = document.getElementById('resume-upload-zone');
    const resumeInput = document.getElementById('resume-file');
    const resumePreview = document.getElementById('resume-preview-container');

    resumeZone.addEventListener('click', () => resumeInput.click());
    resumeInput.addEventListener('change', (e) => handleFilePreview(e, resumePreview));

    // JD Upload zone trigger
    const jdZone = document.getElementById('jd-upload-zone');
    const jdInput = document.getElementById('jd-file');
    const jdPreview = document.getElementById('jd-preview-container');

    jdZone.addEventListener('click', () => jdInput.click());
    jdInput.addEventListener('change', (e) => handleFilePreview(e, jdPreview));
}

function handleFilePreview(event, previewContainer) {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewContainer.innerHTML = `
                <div class="file-info">
                    <img src="${e.target.result}" class="image-preview">
                    <span>${file.name}</span>
                </div>
            `;
        };
        reader.readAsDataURL(file);
    } else {
        previewContainer.innerHTML = `
            <div class="file-info">
                <i data-lucide="file-check"></i>
                <span>${file.name}</span>
            </div>
        `;
        lucide.createIcons();
    }
}

async function handleRunEvaluation() {
    const resumeFile = document.getElementById('resume-file').files[0];
    const resumeText = document.getElementById('resume-text').value;
    const jdFile = document.getElementById('jd-file').files[0];
    const jdTitle = document.getElementById('jd-title').value;
    const jdText = document.getElementById('jd-text').value;
    const jdCompany = document.getElementById('jd-company').value;

    console.log('Starting Evaluation:', { resumeFile, resumeText: !!resumeText, jdFile, jdTitle, jdText: !!jdText });

    if (!resumeFile && (!resumeText || !resumeText.trim())) {
        showNotification('Please upload a resume or paste resume text', 'warning');
        return;
    }

    if (!jdFile && (!jdTitle || !jdTitle.trim() || !jdText || !jdText.trim())) {
        showNotification('Kindly provide both Job Title and Description to proceed', 'warning');
        return;
    }

    const loader = document.getElementById('eval-loading');
    loader.classList.remove('hidden');

    try {
        // 1. Upload Resume
        let resumeId;
        if (resumeFile) {
            console.log('Uploading Resume File...');
            const formData = new FormData();
            formData.append('file', resumeFile);
            const res = await fetchApi('/api/resumes/upload', { method: 'POST', body: formData }, true);
            resumeId = res.id;
        } else {
            console.log('Uploading Pasted Resume Text...');
            const formData = new FormData();
            formData.append('resume_text', resumeText);
            const res = await fetchApi('/api/resumes/upload', { method: 'POST', body: formData }, true);
            resumeId = res.id;
        }

        // 2. Create/Upload Job
        let jobId;
        if (jdFile) {
            console.log('Uploading Job File...');
            const formData = new FormData();
            formData.append('file', jdFile);
            if (jdTitle) formData.append('title', jdTitle);
            if (jdCompany) formData.append('company', jdCompany);

            const res = await fetchApi('/api/jobs/upload', { method: 'POST', body: formData }, true);
            jobId = res.id;
        } else {
            console.log('Creating Job Entry...');
            const jobRes = await fetchApi('/api/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: jdTitle,
                    company: jdCompany || 'N/A',
                    description_text: jdText
                })
            });
            jobId = jobRes.id;
        }

        console.log('Starting Analysis...', { resumeId, jobId });
        // 3. Run Sync Evaluation (wait for heavy AI analysis)
        const evalRes = await fetchApi('/api/evaluate/sync', {
            method: 'POST',
            body: JSON.stringify({ resume_id: resumeId, job_id: jobId })
        });

        console.log('Analysis Complete:', evalRes);

        loader.classList.add('hidden');
        renderFullResult(evalRes);

    } catch (e) {
        loader.classList.add('hidden');
        console.error('Evaluation Error:', e);

        let errorMsg = 'Evaluation failed';
        try {
            const errorObj = JSON.parse(e.message);
            errorMsg = errorObj.detail || errorMsg;
        } catch (err) {
            errorMsg = e.message || errorMsg;
        }

        showNotification(errorMsg, 'error');
    }
}

function renderFullResult(result) {
    const container = document.getElementById('view-container');
    const score = result.overall_score || 0;
    const colorClass = score >= 75 ? 'success' : (score >= 50 ? 'warning' : 'danger');

    container.innerHTML = `
        <div class="result-header">
            <button class="back-link" onclick="switchView('evaluate')"><i data-lucide="arrow-left"></i> New Evaluation</button>
            <div class="result-title">
                <h2>Analysis Complete</h2>
                <div class="badge ${colorClass}">${score >= 75 ? 'Strong Match' : (score >= 50 ? 'Good Match' : 'Gap Identified')}</div>
            </div>
        </div>

        <div class="result-top-grid">
            <div class="score-card glass-card">
                <div class="score-circle-container">
                    <svg viewBox="0 0 36 36" class="circular-chart ${colorClass}">
                        <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        <path class="circle" stroke-dasharray="${score}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        <text x="18" y="20.35" class="percentage">${score.toFixed(0)}%</text>
                    </svg>
                </div>
                <h3>Overall Match</h3>
                <p>Calculated across 4 key dimensions</p>
            </div>

            <div class="details-card glass-card">
                <h4 class="card-subtitle">Score Breakdown</h4>
                <div class="breakdown-list">
                    <div class="breakdown-item">
                        <div class="bi-header"><span>Skill Coverage</span><span>${(result.skill_match_score || 0).toFixed(0)}%</span></div>
                        <div class="progress-track"><div class="progress-bar" style="width: ${result.skill_match_score}%"></div></div>
                    </div>
                    <div class="breakdown-item">
                        <div class="bi-header"><span>Semantic Similarity</span><span>${(result.semantic_score || 0).toFixed(0)}%</span></div>
                        <div class="progress-track"><div class="progress-bar violet" style="width: ${result.semantic_score}%"></div></div>
                    </div>
                    <div class="breakdown-item">
                        <div class="bi-header"><span>Experience Match</span><span>${(result.experience_score || 0).toFixed(0)}%</span></div>
                        <div class="progress-track"><div class="progress-bar green" style="width: ${result.experience_score}%"></div></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="skill-analysis-grid">
            <div class="glass-card">
                <h4 class="card-subtitle"><i data-lucide="check-circle" class="success-text"></i> Matched Skills</h4>
                <div class="skills-wrap">
                    ${(result.matched_skills || []).map(s => `<span class="skill-tag match">${s}</span>`).join('')}
                </div>
            </div>
            <div class="glass-card">
                <h4 class="card-subtitle"><i data-lucide="alert-circle" class="error-text"></i> Missing Skills</h4>
                <div class="skills-wrap">
                    ${(result.missing_skills || []).map(s => `<span class="skill-tag missing">${s}</span>`).join('')}
                </div>
            </div>
        </div>

        <div class="recommendations-section glass-card">
            <h4 class="card-subtitle"><i data-lucide="lightbulb" class="warning-text"></i> AI Recommendations</h4>
            <div class="rec-content">
                ${result.recommendation_text ? formatMarkdown(result.recommendation_text) : 'No specific recommendations provided.'}
            </div>
        </div>
    `;
    lucide.createIcons();
}

// ─────────────────────────────────────────────────────────────────────────────
// RANKINGS VIEW
// ─────────────────────────────────────────────────────────────────────────────

async function renderRankings(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Candidate Rankings</h1>
            <p class="page-subtitle">Ranked leaderboard for job positions</p>
        </div>

        <div class="filters-bar glass-card">
            <label>Select Job Position:</label>
            <select id="job-selector">
                <option value="">Loading positions...</option>
            </select>
        </div>

        <div id="rankings-list" class="rankings-container">
            <div class="empty-state">Select a job position to see rankings</div>
        </div>
    `;

    try {
        const jobs = await fetchApi('/api/jobs');
        const selector = document.getElementById('job-selector');
        selector.innerHTML = '<option value="">-- Select a Job --</option>';
        jobs.forEach(j => {
            selector.innerHTML += `<option value="${j.id}">${j.title} (${j.evaluation_count})</option>`;
        });

        selector.addEventListener('change', async (e) => {
            if (!e.target.value) return;
            renderRankingsForJob(e.target.value);
        });
    } catch (e) {
        showNotification('Failed to load jobs', 'error');
    }
}

async function renderRankingsForJob(jobId) {
    const list = document.getElementById('rankings-list');
    list.innerHTML = '<div class="loader-inline"></div>';

    const rankings = await fetchApi(`/api/rankings/${jobId}`);
    if (rankings.length === 0) {
        list.innerHTML = '<div class="empty-state">No evaluations yet for this position</div>';
        return;
    }

    list.innerHTML = rankings.map((r, i) => `
        <div class="ranking-item glass-card slide-up" style="animation-delay: ${i * 0.1}s">
            <div class="rank-pos">#${r.rank}</div>
            <div class="cand-info">
                <h3>${r.candidate_name}</h3>
                <div class="cand-meta">
                    <span>${(r.candidate_experience || 0).toFixed(0)} yrs exp</span>
                    <span>•</span>
                    <span>${r.matched_skills_count} skills matched</span>
                </div>
            </div>
            <div class="cand-score">
                <span class="score">${(r.overall_score || 0).toFixed(0)}</span>
                <span class="label">Match</span>
            </div>
        </div>
    `).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────────────────────────────────────

async function fetchApi(path, options = {}, isMultipart = false) {
    const config = { ...options };
    if (!isMultipart && config.body && !config.headers) {
        config.headers = { 'Content-Type': 'application/json' };
    }

    const response = await fetch(`${BASE_URL}${path}`, config);
    if (!response.ok) {
        throw new Error(await response.text());
    }
    return response.json();
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const note = document.createElement('div');
    note.className = `notification ${type}`;
    note.innerHTML = `
        <div class="note-icon"></div>
        <div class="note-msg">${message}</div>
    `;
    container.appendChild(note);
    setTimeout(() => note.classList.add('show'), 10);
    setTimeout(() => {
        note.classList.remove('show');
        setTimeout(() => note.remove(), 300);
    }, 4000);
}

function formatMarkdown(text) {
    if (!text) return '';
    return text
        .replace(/^## (.*$)/gm, '<h2 style="margin-top:1.5rem; color:var(--accent-blue)">$1</h2>')
        .replace(/^### (.*$)/gm, '<h3 style="margin-top:1.2rem">$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^• (.*$)/gm, '<div class="rec-list-item"><span>•</span> $1</div>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

// ─────────────────────────────────────────────────────────────────────────────
// LIBRARY VIEWS
// ─────────────────────────────────────────────────────────────────────────────

async function renderResumes(container) {
    container.innerHTML = `
        <div class="page-header">
            <div class="header-main">
                <h1 class="page-title">Resume Library</h1>
                <p class="page-subtitle">Internal repository of processed talent profiles</p>
            </div>
            <div class="header-actions-row">
                <div class="search-mini">
                    <i data-lucide="search"></i>
                    <input type="text" placeholder="Filter by name or skill..." id="resume-filter">
                </div>
                <button class="primary-btn sm" onclick="switchView('evaluate')">
                    <i data-lucide="plus"></i> New Upload
                </button>
            </div>
        </div>
        <div class="library-grid candidate-library" id="resume-list">
            <div class="loader-inline"></div>
        </div>
    `;

    if (window.lucide) lucide.createIcons();

    try {
        const resumes = await fetchApi('/api/resumes');
        const list = document.getElementById('resume-list');

        if (resumes.length === 0) {
            list.innerHTML = `
                <div class="empty-state-container glass-card">
                    <div class="empty-icon"><i data-lucide="folder-open"></i></div>
                    <h3>No Resumes Found</h3>
                    <p>Start by uploading your first candidate resume for AI analysis.</p>
                    <button class="primary-btn sm" onclick="switchView('evaluate')">Upload Now</button>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        const renderItems = (items) => {
            list.innerHTML = items.map(r => `
                <div class="prof-card candidate-item slide-up">
                    <div class="card-edge"></div>
                    <div class="card-content">
                        <div class="card-top">
                            <div class="user-meta">
                                <div class="prof-avatar">${(r.candidate_name || 'U').charAt(0)}</div>
                                <div class="prof-info">
                                    <h3>${r.candidate_name || 'Anonymous Candidate'}</h3>
                                    <span>${r.email || 'Contact not extracted'}</span>
                                </div>
                            </div>
                            <div class="eval-count-badge" title="Total Evaluations">
                                <i data-lucide="activity"></i> ${r.evaluation_count || 0}
                            </div>
                        </div>
                        
                        <div class="card-mid">
                            <div class="mini-stat">
                                <span class="label">Total Experience</span>
                                <span class="value">${(r.experience_years || 0).toFixed(1)} Years</span>
                            </div>
                            <div class="mini-stat">
                                <span class="label">Skills Detected</span>
                                <span class="value">${(r.skills || []).length} Keys</span>
                            </div>
                        </div>

                        <div class="card-tags">
                            ${(r.skills || []).slice(0, 4).map(s => `<span class="modern-tag">${s}</span>`).join('')}
                            ${(r.skills || []).length > 4 ? `<span class="modern-tag more">+${r.skills.length - 4}</span>` : ''}
                        </div>

                        <div class="card-footer">
                            <span class="date">Added ${new Date().toLocaleDateString()}</span>
                            <button class="ghost-btn" onclick="showNotification('Profile deep-view is in development', 'info')">
                                View Full Profile <i data-lucide="chevron-right"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
            if (window.lucide) lucide.createIcons();
        };

        renderItems(resumes);

        const filterInput = document.getElementById('resume-filter');
        filterInput.addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            const filtered = resumes.filter(r =>
                (r.candidate_name || '').toLowerCase().includes(val) ||
                (r.skills || []).some(s => s.toLowerCase().includes(val))
            );
            renderItems(filtered);
        });

    } catch (err) {
        console.error('Error loading resumes:', err);
        showNotification('Failed to sync Resume Library', 'error');
    }
}

async function renderJobs(container) {
    container.innerHTML = `
        <div class="page-header">
            <div class="header-main">
                <h1 class="page-title">Job Positions</h1>
                <p class="page-subtitle">Repository of strategic role requirements</p>
            </div>
            <div class="header-actions-row">
                <div class="search-mini">
                    <i data-lucide="search"></i>
                    <input type="text" placeholder="Search roles..." id="job-filter">
                </div>
                <button class="primary-btn sm" onclick="switchView('evaluate')">
                    <i data-lucide="plus"></i> Define Role
                </button>
            </div>
        </div>
        <div class="library-grid" id="job-list">
            <div class="loader-inline"></div>
        </div>
    `;

    if (window.lucide) lucide.createIcons();

    try {
        const jobs = await fetchApi('/api/jobs');
        const list = document.getElementById('job-list');

        if (jobs.length === 0) {
            list.innerHTML = `
                <div class="empty-state-container glass-card">
                    <div class="empty-icon"><i data-lucide="briefcase"></i></div>
                    <h3>No Job Profiles</h3>
                    <p>Create a job description to start matching candidates.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        const renderItems = (items) => {
            list.innerHTML = items.map(j => `
                <div class="prof-card job-item slide-up">
                    <div class="card-edge job"></div>
                    <div class="card-content">
                        <div class="card-top">
                            <div class="user-meta">
                                <div class="prof-avatar job"><i data-lucide="briefcase"></i></div>
                                <div class="prof-info">
                                    <h3>${j.title}</h3>
                                    <span>${j.company || 'Internal Entity'}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card-mid">
                            <div class="mini-stat">
                                <span class="label">Exp required</span>
                                <span class="value">${(j.experience_required || 0).toFixed(0)}+ Years</span>
                            </div>
                            <div class="mini-stat">
                                <span class="label">Matches Run</span>
                                <span class="value">${j.evaluation_count || 0} Candidates</span>
                            </div>
                        </div>

                        <div class="card-tags">
                            ${(j.required_skills || []).slice(0, 4).map(s => `<span class="modern-tag violet">${s}</span>`).join('')}
                            ${(j.required_skills || []).length > 4 ? `<span class="modern-tag more">+${j.required_skills.length - 4}</span>` : ''}
                        </div>

                        <div class="card-footer">
                            <button class="primary-btn sm outline" onclick="switchView('evaluate')">
                                <i data-lucide="play-circle"></i> Run New Batch
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
            if (window.lucide) lucide.createIcons();
        };

        renderItems(jobs);

        const filterInput = document.getElementById('job-filter');
        filterInput.addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            const filtered = jobs.filter(j =>
                j.title.toLowerCase().includes(val) ||
                (j.company || '').toLowerCase().includes(val)
            );
            renderItems(filtered);
        });

    } catch (err) {
        console.error('Error loading jobs:', err);
    }
}

// History and About remain the same...
function renderHistory(container) {
    container.innerHTML = `
        <div class="page-header">
            <div class="header-main">
                <h1 class="page-title">Evaluation History</h1>
                <p class="page-subtitle">Timeline of all AI talent assessments</p>
            </div>
            <div class="header-actions-row">
                <div class="search-mini">
                    <i data-lucide="search"></i>
                    <input type="text" placeholder="Search history..." id="history-filter">
                </div>
            </div>
        </div>
        <div class="library-grid history-library" id="history-list">
            <div class="loader-inline"></div>
        </div>
    `;

    if (window.lucide) lucide.createIcons();

    fetchApi('/api/analytics').then(data => {
        const list = document.getElementById('history-list');
        let evals = data.recent_evaluations || [];

        if (evals.length === 0) {
            list.innerHTML = `
                <div class="empty-state-container glass-card">
                    <div class="empty-icon"><i data-lucide="history"></i></div>
                    <h3>No evaluations found</h3>
                    <p>Analysis results will appear here once you run your first batch.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        // Sort by date descending (latest analysis first)
        evals.sort((a, b) => new Date(b.date) - new Date(a.date));

        const renderItems = (items) => {
            list.innerHTML = items.map(e => {
                const score = e.score || 0;
                const color = score >= 75 ? 'success' : (score >= 50 ? 'warning' : 'danger');
                const dateObj = new Date(e.date);
                const formattedDate = dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                return `
                    <div class="prof-card history-item slide-up">
                        <div class="card-edge ${color}"></div>
                        <div class="card-content">
                            <div class="card-top">
                                <div class="user-meta">
                                    <div class="prof-avatar ${color}"><i data-lucide="file-check"></i></div>
                                    <div class="prof-info">
                                        <h3>${e.candidate || 'Unknown Candidate'}</h3>
                                        <span>Target: ${e.job || 'No Position Defined'}</span>
                                    </div>
                                </div>
                                <div class="item-badge ${color}">${score.toFixed(0)}%</div>
                            </div>
                            
                            <div class="card-footer">
                                <span class="date">Analyzed on ${formattedDate}</span>
                                <button class="ghost-btn" onclick="showNotification('Detailed report access is coming soon', 'info')">
                                    Full Report <i data-lucide="chevron-right"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            if (window.lucide) lucide.createIcons();
        };

        renderItems(evals);

        const filterInput = document.getElementById('history-filter');
        filterInput.addEventListener('input', (event) => {
            const val = event.target.value.toLowerCase();
            const filtered = evals.filter(e =>
                (e.candidate || '').toLowerCase().includes(val) ||
                (e.job || '').toLowerCase().includes(val)
            );
            renderItems(filtered);
        });

    }).catch(err => {
        console.error('Error fetching history:', err);
        const list = document.getElementById('history-list');
        if (list) list.innerHTML = `<div class="error-state">Failed to load history findings. ${err.message}</div>`;
    });
}

function renderAbout(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">About ResumeLens</h1>
            <p class="page-subtitle">Next-gen candidate evaluation platform</p>
        </div>
        <div class="glass-card">
            <h3>The Technology Stack</h3>
            <p>ResumeLens uses a multi-agent orchestration pattern to provide deep insights.</p>
            <ul>
                <li><strong>LangGraph:</strong> Agentic orchestrator</li>
                <li><strong>FAISS:</strong> Vector database</li>
                <li><strong>Sentence-Transformers:</strong> Semantic embeddings</li>
                <li><strong>FastAPI:</strong> High-performance backend</li>
                <li><strong>EasyOCR & Pillow:</strong> Image-to-text extraction</li>
            </ul>
        </div>
    `;
}
