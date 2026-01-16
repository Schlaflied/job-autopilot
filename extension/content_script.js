// Job Autopilot Helper - Content Script
// Semi-automatic mode: User clicks to reveal emails, script extracts them

console.log('[Apollo Helper] Content script loaded on Apollo.io');

// ============================================================
// Helper Functions
// ============================================================

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================
// Email Extraction (reads already-visible emails)
// ============================================================

function extractVisibleEmails() {
    const contacts = [];
    const rows = document.querySelectorAll('[role="row"]');

    console.log(`[Apollo Helper] Scanning ${rows.length} rows for visible emails...`);

    for (let i = 1; i < rows.length && contacts.length < 10; i++) {
        const row = rows[i];

        try {
            // Look for mailto links (emails that are already revealed)
            const emailEl = row.querySelector('a[href^="mailto:"]');

            if (emailEl) {
                const nameEl = row.querySelector('a[href*="#/people/"]');
                const companyEl = row.querySelector('a[href*="#/organizations/"]');

                // Extract title from row text
                let title = '';
                const rowText = row.textContent;
                const titleMatch = rowText.match(/((?:senior\s+)?(?:technical\s+)?recruiter|talent\s+acquisition(?:\s+\w+)?|hr\s+manager)/i);
                if (titleMatch) {
                    title = titleMatch[1];
                }

                const contact = {
                    name: nameEl ? nameEl.textContent.trim() : 'Unknown',
                    email: emailEl.href.replace('mailto:', ''),
                    title: title,
                    company: companyEl ? companyEl.textContent.trim() : ''
                };

                // Validate email
                if (contact.email && contact.email.includes('@') && contact.email.includes('.')) {
                    contacts.push(contact);
                    console.log(`[Apollo Helper] ✅ Found: ${contact.name} <${contact.email}>`);
                }
            }
        } catch (e) {
            console.error('[Apollo Helper] Error extracting from row:', e);
        }
    }

    return contacts;
}

// ============================================================
// Send results to background
// ============================================================

function sendResultsToBackground(contacts) {
    try {
        chrome.runtime.sendMessage({
            type: 'CONTACTS_SCRAPED',
            contacts: contacts
        }, (response) => {
            if (chrome.runtime.lastError) {
                console.log('[Apollo Helper] Note: Background SW may be idle. Results will be saved on next poll.');
                // Store locally for later
                localStorage.setItem('apolloHelper_pendingContacts', JSON.stringify(contacts));
            } else {
                console.log('[Apollo Helper] Results sent to background:', response);
                localStorage.removeItem('apolloHelper_pendingContacts');
            }
        });
    } catch (e) {
        console.log('[Apollo Helper] Could not send to background:', e.message);
        localStorage.setItem('apolloHelper_pendingContacts', JSON.stringify(contacts));
    }
}

// ============================================================
// Main Scan Function
// ============================================================

async function scanForEmails() {
    console.log('[Apollo Helper] Scanning for visible emails...');

    const contacts = extractVisibleEmails();

    if (contacts.length > 0) {
        console.log(`[Apollo Helper] Found ${contacts.length} contacts with emails!`);
        sendResultsToBackground(contacts);

        // Show user notification
        showNotification(`✅ Found ${contacts.length} HR contacts! Data sent to Job Autopilot.`);
    } else {
        console.log('[Apollo Helper] No visible emails found. Click "Access email" buttons to reveal emails, then click the extension button to scan.');
    }

    return contacts;
}

// ============================================================
// UI Notification
// ============================================================

function showNotification(message) {
    const existing = document.getElementById('apollo-helper-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.id = 'apollo-helper-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: 500;
        z-index: 999999;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;

    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => notification.remove(), 5000);
}

// ============================================================
// Auto-scan on page load
// ============================================================

async function autoScan() {
    await sleep(5000);

    const isSearchPage = window.location.hash.includes('#/people');
    if (!isSearchPage) {
        console.log('[Apollo Helper] Not on search page.');
        return;
    }

    console.log('[Apollo Helper] On Apollo search page. Tip: Click "Access email" to reveal emails, then I will scan them automatically.');

    // Initial scan
    await scanForEmails();

    // Set up observer to detect when emails are revealed
    setupMutationObserver();
}

// ============================================================
// Watch for DOM changes (when user clicks "Access email")
// ============================================================

let scanTimeout = null;

function setupMutationObserver() {
    const observer = new MutationObserver((mutations) => {
        // Check if any mailto links were added
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                const hasNewEmail = Array.from(mutation.addedNodes).some(node => {
                    if (node.nodeType === 1) {
                        return node.querySelector?.('a[href^="mailto:"]') ||
                            (node.tagName === 'A' && node.href?.startsWith('mailto:'));
                    }
                    return false;
                });

                if (hasNewEmail) {
                    // Debounce the scan
                    if (scanTimeout) clearTimeout(scanTimeout);
                    scanTimeout = setTimeout(() => {
                        console.log('[Apollo Helper] New email detected! Auto-scanning...');
                        scanForEmails();
                    }, 1000);
                }
            }
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log('[Apollo Helper] Watching for new emails...');
}

// ============================================================
// Start
// ============================================================

console.log('[Apollo Helper] Ready. Auto-scanning in 5 seconds...');
setTimeout(autoScan, 5000);

// Listen for manual trigger from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TRIGGER_SCRAPE') {
        console.log('[Apollo Helper] Manual scan triggered');
        scanForEmails().then(contacts => {
            sendResponse({ status: 'complete', count: contacts.length });
        });
        return true;
    }
});
