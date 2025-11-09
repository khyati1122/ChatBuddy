document.addEventListener('DOMContentLoaded', function () {
    const apiKeyInput = document.getElementById('apiKey');
    const toggleBtn = document.getElementById('toggleAnalysis');
    const statusDiv = document.getElementById('status');
    const analysisDelaySelect = document.getElementById('analysisDelay');
    const messageCountSelect = document.getElementById('messageCount');
    const sensitivitySelect = document.getElementById('sensitivity');
    const apiStatusDiv = document.getElementById('apiStatus');

    let isActive = false;

    // Load saved settings
    chrome.storage.local.get([
        'geminiApiKey',
        'isActive',
        'analysisDelay',
        'messageCount',
        'sensitivity'
    ], function (result) {
        if (result.geminiApiKey) {
            apiKeyInput.value = result.geminiApiKey;
            validateApiKey(result.geminiApiKey);
        }
        if (result.isActive !== undefined) {
            isActive = result.isActive;
            updateUI();
        }
        if (result.analysisDelay) {
            analysisDelaySelect.value = result.analysisDelay;
        }
        if (result.messageCount) {
            messageCountSelect.value = result.messageCount;
        }
        if (result.sensitivity) {
            sensitivitySelect.value = result.sensitivity;
        }
    });

    // Real-time API key validation
    apiKeyInput.addEventListener('input', function () {
        const apiKey = apiKeyInput.value.trim();
        validateApiKey(apiKey);
        if (apiKey.startsWith('AIza')) {
            chrome.storage.local.set({ geminiApiKey: apiKey });
        }
    });

    // Save settings when changed
    analysisDelaySelect.addEventListener('change', saveSettings);
    messageCountSelect.addEventListener('change', saveSettings);
    sensitivitySelect.addEventListener('change', saveSettings);

    toggleBtn.addEventListener('click', toggleAnalysis);

    function validateApiKey(apiKey) {
        if (!apiKey) {
            apiStatusDiv.style.display = 'none';
            return;
        }

        if (apiKey.startsWith('AIza') && apiKey.length > 30) {
            apiStatusDiv.innerHTML = '<span style="color: #10b981;">●</span> <span>Valid API Key</span>';
            apiStatusDiv.style.display = 'flex';
        } else {
            apiStatusDiv.innerHTML = '<span style="color: #ef4444;">●</span> <span>Invalid API Key</span>';
            apiStatusDiv.style.display = 'flex';
        }
    }

    function saveSettings() {
        chrome.storage.local.set({
            analysisDelay: analysisDelaySelect.value,
            messageCount: messageCountSelect.value,
            sensitivity: sensitivitySelect.value
        });
    }

    async function toggleAnalysis() {
        const apiKey = apiKeyInput.value.trim();

        if (!apiKey) {
            showNotification('Please enter your Gemini API key', 'error');
            apiKeyInput.focus();
            return;
        }

        if (!apiKey.startsWith('AIza') || apiKey.length < 30) {
            showNotification('Please enter a valid Gemini API key', 'error');
            apiKeyInput.focus();
            return;
        }

        // Save API key
        chrome.storage.local.set({ geminiApiKey: apiKey });

        isActive = !isActive;

        chrome.storage.local.set({
            isActive: isActive
        });

        // Send message to content script
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab) {
                await chrome.tabs.sendMessage(tab.id, {
                    action: isActive ? 'startAnalysis' : 'stopAnalysis',
                    settings: {
                        apiKey: apiKey,
                        analysisDelay: parseInt(analysisDelaySelect.value),
                        messageCount: parseInt(messageCountSelect.value),
                        sensitivity: sensitivitySelect.value
                    }
                });

                showNotification(
                    isActive ? 'Analysis started - switch to your chat!' : 'Analysis stopped',
                    isActive ? 'success' : 'info'
                );
            }
        } catch (error) {
            console.log('Error:', error);
            if (isActive) {
                showNotification('Open a chat platform first (WhatsApp Web, etc.)', 'error');
                isActive = false;
                chrome.storage.local.set({ isActive: false });
            }
        }

        updateUI();
    }

    function updateUI() {
        if (isActive) {
            statusDiv.innerHTML = `
        <div class="status-icon">🔍</div>
        <div class="status-text">Analyzing Messages</div>
      `;
            statusDiv.className = 'status-card status-active';
            toggleBtn.innerHTML = `
        <span>🛑</span>
        Stop Analysis
      `;
            toggleBtn.className = 'btn-primary btn-stop';
        } else {
            statusDiv.innerHTML = `
        <div class="status-icon">⏸️</div>
        <div class="status-text">Ready to Start</div>
      `;
            statusDiv.className = 'status-card status-inactive';
            toggleBtn.innerHTML = `
        <span>🚀</span>
        Start Analysis
      `;
            toggleBtn.className = 'btn-primary';
        }
    }

    function showNotification(message, type) {
        // Remove existing notifications
        document.querySelectorAll('.popup-notification').forEach(n => n.remove());

        const notification = document.createElement('div');
        notification.className = 'popup-notification';
        notification.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#6366f1'};
      color: white;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      animation: slideInRight 0.3s ease;
      max-width: 300px;
    `;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Add CSS for notifications
    const style = document.createElement('style');
    style.textContent = `
    @keyframes slideInRight {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
  `;
    document.head.appendChild(style);
});