const API_BASE = '';
let currentJobId = null;
let pollingInterval = null;

const urlsTextarea = document.getElementById('urls');
const urlCount = document.getElementById('url-count');
const btnProcess = document.getElementById('btn-process');
const resultsSection = document.getElementById('results-section');
const videoList = document.getElementById('video-list');

urlsTextarea.addEventListener('input', () => {
    const urls = parseUrls(urlsTextarea.value);
    urlCount.textContent = `${urls.length} / 15 links`;
    urlCount.style.color = urls.length > 15 ? '#d55b5b' : '#666';
});

function parseUrls(text) {
    return text
        .split(/[\n,]+/)
        .map(u => u.trim())
        .filter(u => u.length > 0);
}

async function startProcessing() {
    const urls = parseUrls(urlsTextarea.value);

    if (urls.length === 0) {
        alert('Please enter at least one YouTube URL.');
        return;
    }
    if (urls.length > 15) {
        alert('Maximum 15 URLs allowed.');
        return;
    }

    btnProcess.disabled = true;
    btnProcess.textContent = 'Processing...';

    try {
        const res = await fetch(`${API_BASE}/api/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to start processing');
        }

        const data = await res.json();
        currentJobId = data.job_id;

        resultsSection.style.display = 'block';
        renderVideos(urls.map(url => ({ url, title: '', status: 'pending', error: null, files: null })));

        startPolling();
    } catch (err) {
        alert('Error: ' + err.message);
        btnProcess.disabled = false;
        btnProcess.textContent = 'Process Videos';
    }
}

function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(pollStatus, 2000);
}

async function pollStatus() {
    if (!currentJobId) return;

    try {
        const res = await fetch(`${API_BASE}/api/status/${currentJobId}`);
        if (!res.ok) return;

        const data = await res.json();
        renderVideos(data.videos);

        const allDone = data.videos.every(v => v.status === 'done' || v.status === 'error');
        if (allDone) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            btnProcess.disabled = false;
            btnProcess.textContent = 'Process Videos';
        }
    } catch (err) {
        console.error('Polling error:', err);
    }
}

function renderVideos(videos) {
    videoList.innerHTML = videos.map((v, i) => {
        const title = v.title || `Video ${i + 1}`;
        const statusClass = `status-${v.status}`;
        const cardClass = v.status === 'done' ? 'done' : v.status === 'error' ? 'error' : '';
        const isLoading = !['done', 'error', 'pending'].includes(v.status);

        let statusLabel = v.status;
        const labels = {
            pending: 'Pending',
            downloading: 'Downloading Transcript',
            translating: 'Translating to English',
            processing: 'Processing with AI',
            done: 'Complete',
            error: 'Error',
        };
        statusLabel = labels[v.status] || v.status;

        let extra = '';
        if (v.status === 'error' && v.error) {
            extra = `<div class="error-message">${escapeHtml(v.error)}</div>`;
        }
        if (v.status === 'done' && v.files) {
            extra = `
                <div class="download-buttons">
                    <a class="btn-download" href="${API_BASE}/api/download/${currentJobId}/${encodeURIComponent(v.files.full)}" download>
                        &#11015; Full Transcript
                    </a>
                    <a class="btn-download" href="${API_BASE}/api/download/${currentJobId}/${encodeURIComponent(v.files.processed)}" download>
                        &#11015; AI Analysis
                    </a>
                </div>
            `;
        }

        return `
            <div class="video-card ${cardClass}">
                <div class="video-url">${escapeHtml(v.url)}</div>
                <div class="video-header">
                    <span class="video-title">${escapeHtml(title)}</span>
                    <span class="status-badge ${statusClass} ${isLoading ? 'loading' : ''}">${statusLabel}</span>
                </div>
                ${extra}
            </div>
        `;
    }).join('');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
