// Job Autopilot Helper - Content Script
// DOM manipulation logic for Apollo.io

console.log('[Apollo Helper] Content script loaded on Apollo.io');

// ============================================================
// DOM Selectors (Update if Apollo UI changes)
// ============================================================

const SELECTORS = {
    // Contact list item
    contactRow: '[data-cy="people-row"]',
    contactName: '[data-cy="name-cell"]',
    contactTitle: '[data-cy="title-cell"]',
    contactCompany: '[data-cy="account-name"]',

    // Email access button
    accessEmailBtn: '[data-cy="access-button"]',
    emailDisplayed: '[data-cy="email-value"]',

    // Results info
    resultsCount: '[data-cy="total-count"]',
    noResults: '.zp-people-none',

    // Loading states
    loadingSpinner: '.zp-spinner'
};

// ============================================================
// Helper Functions
// ============================================================

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForElement(selector, timeout = 10000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
        const element = document.querySelector(selector);
        if (element) return element;
        await sleep(500);
    }

    return null;
}

async function waitForLoading() {
    // Wait for any loading spinners to disappear
    let spinner = document.querySelector(SELECTORS.loadingSpinner);
    while (spinner) {
        await sleep(500);
        spinner = document.querySelector(SELECTORS.loadingSpinner);
    }
    await sleep(1000); // Extra buffer
}

// ============================================================
// Email Scraping Logic
// ============================================================

async function scrapeContacts() {
    console.log('[Apollo Helper] Starting contact scrape...');

    await waitForLoading();

    // Check for no results
    const noResults = document.querySelector(SELECTORS.noResults);
    if (noResults) {
        console.log('[Apollo Helper] No results found');
        return [];
    }

    const rows = document.querySelectorAll(SELECTORS.contactRow);
    console.log(`[Apollo Helper] Found ${rows.length} contact rows`);

    const contacts = [];

    // Only process first 3 contacts to save credits
    const maxContacts = Math.min(rows.length, 3);

    for (let i = 0; i < maxContacts; i++) {
        const row = rows[i];

        try {
            // Extract basic info
            const nameEl = row.querySelector(SELECTORS.contactName);
            const titleEl = row.querySelector(SELECTORS.contactTitle);
            const companyEl = row.querySelector(SELECTORS.contactCompany);

            const contact = {
                name: nameEl ? nameEl.textContent.trim() : '',
                title: titleEl ? titleEl.textContent.trim() : '',
                company: companyEl ? companyEl.textContent.trim() : '',
                email: null
            };

            // Click "Access Email" button
            const accessBtn = row.querySelector(SELECTORS.accessEmailBtn);
            if (accessBtn) {
                accessBtn.click();
                console.log(`[Apollo Helper] Clicked access email for: ${contact.name}`);

                // Wait for email to load
                await sleep(2000);

                // Try to find the email display
                const emailEl = row.querySelector(SELECTORS.emailDisplayed);
                if (emailEl) {
                    contact.email = emailEl.textContent.trim();
                    console.log(`[Apollo Helper] Email found: ${contact.email}`);
                }
            }

            if (contact.email) {
                contacts.push(contact);
            }

            // Rate limiting between contacts
            await sleep(1500);

        } catch (error) {
            console.error('[Apollo Helper] Error scraping contact:', error);
        }
    }

    console.log(`[Apollo Helper] Scraped ${contacts.length} contacts with emails`);
    return contacts;
}

// ============================================================
// Auto-run on page load (when search results are ready)
// ============================================================

async function autoScrape() {
    // Wait for page to fully load
    await sleep(3000);

    // Check if we're on a search results page
    const isSearchPage = window.location.hash.includes('#/people');
    if (!isSearchPage) {
        console.log('[Apollo Helper] Not on search page, waiting...');
        return;
    }

    console.log('[Apollo Helper] On search page, starting auto-scrape...');

    const contacts = await scrapeContacts();

    // Send results to background script
    chrome.runtime.sendMessage({
        type: 'CONTACTS_SCRAPED',
        contacts: contacts
    }, (response) => {
        console.log('[Apollo Helper] Scrape results sent to background:', response);
    });
}

// Start auto-scrape after page loads
setTimeout(autoScrape, 3000);

// Listen for manual trigger from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TRIGGER_SCRAPE') {
        autoScrape().then(() => {
            sendResponse({ status: 'complete' });
        });
        return true;
    }
});
