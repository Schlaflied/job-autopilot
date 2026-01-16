// Job Autopilot Helper - Background Service Worker
// Polls Flask API for tasks and coordinates with content script

const API_BASE = 'http://localhost:5000';
const POLL_INTERVAL_MS = 60000; // 1 minute (rate limiting)

let isRunning = false;
let currentTask = null;

// ============================================================
// Core Functions
// ============================================================

async function fetchNextTask() {
    try {
        const response = await fetch(`${API_BASE}/api/apollo/task/next`);
        const data = await response.json();

        if (data.status === 'task_found') {
            console.log('[Apollo Helper] Task received:', data.task);
            return data.task;
        } else {
            console.log('[Apollo Helper] No pending tasks');
            return null;
        }
    } catch (error) {
        console.error('[Apollo Helper] Failed to fetch task:', error);
        return null;
    }
}

async function submitTaskResult(jobId, contacts, status) {
    try {
        const response = await fetch(`${API_BASE}/api/apollo/task/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_id: jobId,
                contacts: contacts,
                status: status
            })
        });

        const data = await response.json();
        console.log('[Apollo Helper] Task submitted:', data);
        return data;
    } catch (error) {
        console.error('[Apollo Helper] Failed to submit task:', error);
        return null;
    }
}

// ============================================================
// Task Execution
// ============================================================

async function executeTask(task) {
    currentTask = task;

    // Build Apollo search URL with domain filter
    const searchParams = new URLSearchParams();
    searchParams.append('organizationDomains[]', task.company_domain);

    // Add recruiter title based on department
    const recruiterTitles = getRecruiterTitlesForDepartment(task.department);
    recruiterTitles.forEach(title => {
        searchParams.append('personTitles[]', title);
    });

    const apolloUrl = `https://app.apollo.io/#/people?${searchParams.toString()}`;
    console.log('[Apollo Helper] Opening Apollo search:', apolloUrl);

    // Open Apollo in new tab
    chrome.tabs.create({ url: apolloUrl, active: true }, (tab) => {
        console.log('[Apollo Helper] Apollo tab opened:', tab.id);
    });
}

function getRecruiterTitlesForDepartment(department) {
    const mapping = {
        'Engineering': ['Technical Recruiter', 'Engineering Recruiter'],
        'Marketing': ['Marketing Recruiter'],
        'Sales': ['Sales Recruiter'],
        'Design': ['Design Recruiter', 'Creative Recruiter'],
        'HR': ['HR Recruiter', 'Talent Acquisition'],
        'General': ['Recruiter', 'Talent Acquisition', 'HR Manager']
    };

    return mapping[department] || mapping['General'];
}

// ============================================================
// Polling Loop
// ============================================================

async function pollForTasks() {
    if (!isRunning) return;

    console.log('[Apollo Helper] Polling for tasks...');

    const task = await fetchNextTask();

    if (task) {
        await executeTask(task);
    }

    // Schedule next poll
    setTimeout(pollForTasks, POLL_INTERVAL_MS);
}

// ============================================================
// Message Handlers (from content script and popup)
// ============================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[Apollo Helper] Message received:', message);

    if (message.type === 'START_POLLING') {
        isRunning = true;
        pollForTasks();
        sendResponse({ status: 'started' });
    }

    if (message.type === 'STOP_POLLING') {
        isRunning = false;
        sendResponse({ status: 'stopped' });
    }

    if (message.type === 'GET_STATUS') {
        sendResponse({
            isRunning: isRunning,
            currentTask: currentTask
        });
    }

    if (message.type === 'CONTACTS_SCRAPED') {
        // Content script found contacts
        if (currentTask) {
            submitTaskResult(
                currentTask.job_id,
                message.contacts,
                message.contacts.length > 0 ? 'found' : 'not_found'
            ).then(() => {
                currentTask = null;
            });
        }
        sendResponse({ status: 'submitted' });
    }

    return true; // Keep channel open for async response
});

console.log('[Apollo Helper] Background service worker loaded');
