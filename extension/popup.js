// Job Autopilot Helper - Popup Script

document.addEventListener('DOMContentLoaded', () => {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const taskInfo = document.getElementById('taskInfo');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    // Get current status
    function updateStatus() {
        chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (response) => {
            if (response) {
                if (response.isRunning) {
                    statusDot.classList.add('active');
                    statusText.textContent = 'Running';

                    if (response.currentTask) {
                        taskInfo.textContent = `Current: ${response.currentTask.company} (${response.currentTask.job_title})`;
                    } else {
                        taskInfo.textContent = 'Polling for tasks...';
                    }
                } else {
                    statusDot.classList.remove('active');
                    statusText.textContent = 'Stopped';
                    taskInfo.textContent = 'Click Start to begin';
                }
            }
        });
    }

    // Start polling
    startBtn.addEventListener('click', () => {
        chrome.runtime.sendMessage({ type: 'START_POLLING' }, (response) => {
            console.log('Polling started:', response);
            updateStatus();
        });
    });

    // Stop polling
    stopBtn.addEventListener('click', () => {
        chrome.runtime.sendMessage({ type: 'STOP_POLLING' }, (response) => {
            console.log('Polling stopped:', response);
            updateStatus();
        });
    });

    // Initial status check
    updateStatus();

    // Refresh status every 5 seconds
    setInterval(updateStatus, 5000);
});
