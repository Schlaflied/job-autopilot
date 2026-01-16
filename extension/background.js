// Job Autopilot Helper - Background Service Worker
// Polls Flask API for tasks and coordinates with content script

const API_BASE = 'http://localhost:5000';
const POLL_INTERVAL_MS = 60000; // 1 minute (rate limiting)

let isRunning = false;
let currentTask = null;

console.log('[Apollo Helper] Background service worker initializing...');

// ============================================================
// Core Functions
// ============================================================

async function fetchNextTask() {
    try {
        const response = await fetch(`${API_BASE}/api/apollo/task/next`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            console.error('[Apollo Helper] API returned error:', response.status);
            return null;
        }

        const data = await response.json();

        if (data.status === 'task_found') {
            console.log('[Apollo Helper] Task received:', data.task);
            return data.task;
        } else {
            console.log('[Apollo Helper] No pending tasks');
            return null;
        }
    } catch (error) {
        console.error('[Apollo Helper] Failed to fetch task (API may be offline):', error.message);
        return null;
    }
}

async function submitTaskResult(jobId, contacts, status) {
    try {
        const response = await fetch(`${API_BASE}/api/apollo/task/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                job_id: jobId,
                contacts: contacts,
                status: status
            })
        });

        if (!response.ok) {
            console.error('[Apollo Helper] Submit failed:', response.status);
            return null;
        }

        const data = await response.json();
        console.log('[Apollo Helper] Task submitted:', data);
        return data;
    } catch (error) {
        console.error('[Apollo Helper] Failed to submit task:', error.message);
        return null;
    }
}

// ============================================================
// Task Execution
// ============================================================

async function executeTask(task) {
    currentTask = task;

    // Build Apollo search URL based on search mode
    const searchParams = new URLSearchParams();

    if (task.search_mode === 'domain' && task.company_domain) {
        searchParams.append('organizationDomains[]', task.company_domain);
        console.log('[Apollo Helper] Using domain search:', task.company_domain);
    } else {
        searchParams.append('organizationName', task.company);
        console.log('[Apollo Helper] Using company name search:', task.company);
    }

    // Add recruiter title based on department
    const recruiterTitles = getRecruiterTitlesForDepartment(task.department);
    recruiterTitles.forEach(title => {
        searchParams.append('personTitles[]', title);
    });

    const apolloUrl = `https://app.apollo.io/#/people?${searchParams.toString()}`;
    console.log('[Apollo Helper] Opening Apollo search:', apolloUrl);

    // Open Apollo in new tab
    try {
        chrome.tabs.create({ url: apolloUrl, active: true }, (tab) => {
            if (chrome.runtime.lastError) {
                console.error('[Apollo Helper] Tab creation error:', chrome.runtime.lastError);
            } else {
                console.log('[Apollo Helper] Apollo tab opened:', tab.id);
            }
        });
    } catch (e) {
        console.error('[Apollo Helper] Failed to open tab:', e);
    }
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

    try {
        const task = await fetchNextTask();

        if (task) {
            await executeTask(task);
        }
    } catch (e) {
        console.error('[Apollo Helper] Polling error:', e);
    }

    // Schedule next poll
    if (isRunning) {
        setTimeout(pollForTasks, POLL_INTERVAL_MS);
    }
}

// ============================================================
// Message Handlers (from content script and popup)
// ============================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[Apollo Helper] Message received:', message.type);

    try {
        if (message.type === 'START_POLLING') {
            isRunning = true;
            pollForTasks();
            sendResponse({ status: 'started' });
            return true;
        }

        if (message.type === 'STOP_POLLING') {
            isRunning = false;
            sendResponse({ status: 'stopped' });
            return true;
        }

        if (message.type === 'GET_STATUS') {
            sendResponse({
                isRunning: isRunning,
                currentTask: currentTask
            });
            return true;
        }

        if (message.type === 'CONTACTS_SCRAPED') {
            console.log('[Apollo Helper] Contacts received:', message.contacts?.length || 0);

            if (currentTask) {
                submitTaskResult(
                    currentTask.job_id,
                    message.contacts || [],
                    message.contacts?.length > 0 ? 'found' : 'not_found'
                ).then(() => {
                    currentTask = null;
                    console.log('[Apollo Helper] Task completed and cleared');
                }).catch(e => {
                    console.error('[Apollo Helper] Submit error:', e);
                });
            } else {
                console.log('[Apollo Helper] No current task to submit to');
            }

            sendResponse({ status: 'submitted' });
            return true;
        }
    } catch (e) {
        console.error('[Apollo Helper] Message handler error:', e);
        sendResponse({ status: 'error', message: e.message });
    }

    return true;
});

console.log('[Apollo Helper] Background service worker loaded successfully!');
