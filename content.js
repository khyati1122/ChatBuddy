class ToxicityAnalyzer {
    constructor() {
        this.isActive = false;
        this.settings = {};
        this.lastAnalysisTime = 0;
        this.messageBuffer = [];
        this.analysisInProgress = false;
        this.indicator = null;
        this.observer = null;
        this.consecutiveEmptyAnalyses = 0;

        this.init();
    }

    init() {
        this.createIndicator();
        this.setupMessageListener();
        console.log('💬 Toxicity Analyzer initialized');
    }

    createIndicator() {
        const existingIndicator = document.querySelector('.toxicity-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        this.indicator = document.createElement('div');
        this.indicator.className = 'toxicity-indicator toxicity-hidden';
        this.indicator.innerHTML = `
      <div class="toxicity-header">
        <div class="toxicity-header-content">
          <div class="toxicity-title">
            <span>🔍</span>
            Chat Analysis
          </div>
          <button class="toxicity-close" title="Close">×</button>
        </div>
      </div>
      <div class="toxicity-content">
        <div class="toxicity-loading">
          <div class="loading-spinner"></div>
          <div>Listening for messages...</div>
        </div>
      </div>
    `;

        this.indicator.querySelector('.toxicity-close').addEventListener('click', () => {
            this.hideIndicator();
        });

        document.body.appendChild(this.indicator);
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'startAnalysis') {
                this.startAnalysis(request.settings);
                sendResponse({ status: 'started' });
            } else if (request.action === 'stopAnalysis') {
                this.stopAnalysis();
                sendResponse({ status: 'stopped' });
            }
            return true;
        });
    }

    startAnalysis(settings) {
        this.isActive = true;
        this.settings = settings;
        this.showIndicator();
        this.startObserving();

        console.log('🚀 Analysis started');
        this.showMessage('Active - analyzing messages as they appear...', 'loading');
    }

    stopAnalysis() {
        this.isActive = false;
        this.stopObserving();
        this.hideIndicator();
        this.messageBuffer = [];
        this.consecutiveEmptyAnalyses = 0;

        console.log('🛑 Analysis stopped');
    }

    startObserving() {
        if (this.observer) {
            this.observer.disconnect();
        }

        this.observer = new MutationObserver((mutations) => {
            if (!this.isActive || this.analysisInProgress) return;

            const newMessages = this.extractNewMessages(mutations);
            if (newMessages.length > 0) {
                newMessages.forEach(msg => {
                    // Avoid duplicates and system messages
                    if (!this.messageBuffer.includes(msg) && this.isUserMessage(msg)) {
                        this.messageBuffer.push(msg);
                    }
                });

                // Keep only recent messages
                const maxMessages = this.settings.messageCount || 10;
                if (this.messageBuffer.length > maxMessages) {
                    this.messageBuffer = this.messageBuffer.slice(-maxMessages);
                }

                // Throttle analysis
                const now = Date.now();
                const delay = (this.settings.analysisDelay || 10) * 1000;

                if (now - this.lastAnalysisTime > delay && this.messageBuffer.length >= 2) {
                    this.analyzeConversation();
                }
            }
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    stopObserving() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
    }

    isUserMessage(text) {
        // Filter out system messages, timestamps, etc.
        return text &&
            text.length > 2 &&
            text.length < 300 &&
            !text.match(/^\d{1,2}[:.]\d{2}/) && // Time stamps
            !text.match(/^[\d\s:apm]+$/i) && // Only time
            !text.includes('http') &&
            !text.includes('@') &&
            text.split(' ').length > 1; // More than one word
    }

    extractNewMessages(mutations) {
        const messages = new Set();

        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const text = this.extractMessageText(node);
                        if (text && this.isUserMessage(text)) {
                            messages.add(text);
                        }
                    }
                });
            }
        });

        return Array.from(messages);
    }

    extractMessageText(node) {
        const platform = this.detectPlatform();
        let text = '';

        try {
            switch (platform) {
                case 'whatsapp':
                    text = this.extractWhatsAppMessage(node);
                    break;
                case 'messenger':
                    text = this.extractMessengerMessage(node);
                    break;
                case 'telegram':
                    text = this.extractTelegramMessage(node);
                    break;
                case 'discord':
                    text = this.extractDiscordMessage(node);
                    break;
                default:
                    text = node.textContent || '';
            }
        } catch (error) {
            console.log('Error extracting message:', error);
        }

        return text ? text.trim() : '';
    }

    detectPlatform() {
        const url = window.location.href;
        if (url.includes('web.whatsapp.com')) return 'whatsapp';
        if (url.includes('messenger.com')) return 'messenger';
        if (url.includes('web.telegram.org')) return 'telegram';
        if (url.includes('discord.com')) return 'discord';
        return 'unknown';
    }

    extractWhatsAppMessage(node) {
        const selectors = [
            '[data-testid="conversation-panel-messages"] [data-testid="msg-container"]',
            '.message-in',
            '.message-out',
            '.selectable-text'
        ];

        for (const selector of selectors) {
            const elements = node.querySelectorAll ? node.querySelectorAll(selector) : [];
            for (const element of elements) {
                const text = element.textContent;
                if (text && this.isUserMessage(text)) {
                    return text;
                }
            }
        }
        return node.textContent;
    }

    extractMessengerMessage(node) {
        const selectors = [
            '[role="log"] [role="row"]',
            '[aria-label*="Message"]',
            '.msg'
        ];

        for (const selector of selectors) {
            const elements = node.querySelectorAll ? node.querySelectorAll(selector) : [];
            for (const element of elements) {
                const text = element.textContent;
                if (text && this.isUserMessage(text)) {
                    return text;
                }
            }
        }
        return node.textContent;
    }

    extractTelegramMessage(node) {
        const selectors = [
            '.message',
            '.bubble'
        ];

        for (const selector of selectors) {
            const elements = node.querySelectorAll ? node.querySelectorAll(selector) : [];
            for (const element of elements) {
                const text = element.textContent;
                if (text && this.isUserMessage(text)) {
                    return text;
                }
            }
        }
        return node.textContent;
    }

    extractDiscordMessage(node) {
        const selectors = [
            '[data-list-id="chat-messages"] [class*="message"]',
            '[class*="messageContent"]'
        ];

        for (const selector of selectors) {
            const elements = node.querySelectorAll ? node.querySelectorAll(selector) : [];
            for (const element of elements) {
                const text = element.textContent;
                if (text && this.isUserMessage(text)) {
                    return text;
                }
            }
        }
        return node.textContent;
    }

    async analyzeConversation() {
        if (this.messageBuffer.length < 2 || this.analysisInProgress) return;

        this.analysisInProgress = true;
        this.lastAnalysisTime = Date.now();

        try {
            this.showLoading();

            const conversation = this.formatConversation();
            const analysis = await this.sendToGemini(conversation);

            this.displayAnalysis(analysis);
        } catch (error) {
            console.error('Analysis failed:', error);
            this.showError(`Analysis error: ${error.message}`);
        } finally {
            this.analysisInProgress = false;
        }
    }

    formatConversation() {
        return this.messageBuffer.map((msg, index) => {
            const person = index % 2 === 0 ? 'A' : 'B';
            return `Person ${person}: ${msg}`;
        }).join('\n');
    }

    async sendToGemini(conversation) {
        const API_KEY = this.settings.apiKey;
        const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${API_KEY}`;

        const prompt = this.generatePrompt(conversation);

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: prompt
                    }]
                }],
                generationConfig: {
                    temperature: 0.1,
                    maxOutputTokens: 800,
                    topP: 0.8,
                    topK: 40
                }
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(`API Error: ${data.error.message}`);
        }

        if (!data.candidates?.[0]?.content?.parts?.[0]?.text) {
            throw new Error('Invalid response from API');
        }

        return data.candidates[0].content.parts[0].text;
    }

    generatePrompt(conversation) {
        return `Analyze this chat conversation for toxic communication patterns.

RULES:
- Use "Person A" and "Person B" only
- Focus on communication patterns
- Be constructive and objective

Conversation:
${conversation}

Respond in EXACT format:
Level: [None/Low/Medium/High]
ToxicPerson: [Person A/Person B/Both/None]
Behaviors: [comma separated list or "No toxic behaviors detected"]
Problem: [specific example or "No significant issues"]
Suggestion: [practical tip or "Keep up the good communication"]

If no toxicity found, use "None" and positive feedback.`;
    }

    showLoading() {
        if (this.indicator) {
            this.indicator.querySelector('.toxicity-content').innerHTML = `
        <div class="toxicity-loading">
          <div class="loading-spinner"></div>
          <div>Analyzing ${this.messageBuffer.length} messages...</div>
        </div>
      `;
            this.showIndicator();
        }
    }

    showError(message) {
        if (this.indicator) {
            this.indicator.querySelector('.toxicity-content').innerHTML = `
        <div class="toxicity-error">
          <div style="font-size: 20px; margin-bottom: 6px;">⚠️</div>
          <div style="font-weight: 600; margin-bottom: 4px; font-size: 13px;">Temporary Issue</div>
          <div style="font-size: 12px;">${message}</div>
        </div>
      `;
            this.showIndicator();
        }
    }

    showMessage(message, type = 'info') {
        if (this.indicator) {
            this.indicator.querySelector('.toxicity-content').innerHTML = `
        <div class="toxicity-${type}">
          ${message}
        </div>
      `;
            this.showIndicator();
        }
    }

    displayAnalysis(analysis) {
        try {
            const parsed = this.parseAnalysis(analysis);

            // Track consecutive empty analyses
            if (parsed.level === 'None' && parsed.toxicPerson === 'None') {
                this.consecutiveEmptyAnalyses++;
            } else {
                this.consecutiveEmptyAnalyses = 0;
            }

            if (this.indicator) {
                this.indicator.querySelector('.toxicity-content').innerHTML = this.renderAnalysis(parsed);
                this.showIndicator();
            }
        } catch (error) {
            this.showError('Failed to analyze messages');
        }
    }

    parseAnalysis(analysis) {
        const lines = analysis.split('\n');
        const result = {
            level: 'None',
            toxicPerson: 'None',
            behaviors: ['No toxic behaviors detected'],
            problem: 'No significant issues',
            suggestion: 'Keep up the good communication'
        };

        lines.forEach(line => {
            const cleanLine = line.trim();
            if (cleanLine.startsWith('Level:')) {
                const level = cleanLine.replace('Level:', '').trim();
                result.level = ['Low', 'Medium', 'High', 'None'].includes(level) ? level : 'None';
            } else if (cleanLine.startsWith('ToxicPerson:')) {
                const person = cleanLine.replace('ToxicPerson:', '').trim();
                result.toxicPerson = ['Person A', 'Person B', 'Both', 'None'].includes(person) ? person : 'None';
            } else if (cleanLine.startsWith('Behaviors:')) {
                const behaviors = cleanLine.replace('Behaviors:', '').trim();
                if (behaviors && !behaviors.includes('No toxic behaviors')) {
                    result.behaviors = behaviors.split(',').map(b => b.trim()).filter(b => b);
                }
            } else if (cleanLine.startsWith('Problem:')) {
                const problem = cleanLine.replace('Problem:', '').trim();
                if (problem && !problem.includes('No significant issues')) {
                    result.problem = problem;
                }
            } else if (cleanLine.startsWith('Suggestion:')) {
                const suggestion = cleanLine.replace('Suggestion:', '').trim();
                if (suggestion && !suggestion.includes('Keep up the good communication')) {
                    result.suggestion = suggestion;
                }
            }
        });

        return result;
    }

    renderAnalysis(analysis) {
        const levelClass = `toxicity-${analysis.level.toLowerCase()}`;
        const levelEmoji = analysis.level === 'High' ? '🔴' :
            analysis.level === 'Medium' ? '🟡' :
                analysis.level === 'Low' ? '🟢' : '⚪';

        const personAStatus = this.getPersonStatus('A', analysis.toxicPerson);
        const personBStatus = this.getPersonStatus('B', analysis.toxicPerson);

        // Show positive feedback for multiple clean analyses
        if (this.consecutiveEmptyAnalyses >= 2 && analysis.level === 'None') {
            return `
        <div class="positive-feedback">
          <div class="icon">💚</div>
          <div style="font-weight: 600; margin-bottom: 4px;">Healthy Conversation</div>
          <div style="font-size: 11px;">No toxicity detected in recent messages</div>
        </div>
      `;
        }

        return `
      <div class="toxicity-level-card ${levelClass}">
        ${levelEmoji} ${analysis.level === 'None' ? 'No Toxicity Detected' : `Toxicity: ${analysis.level}`}
      </div>

      <div class="toxicity-person-analysis">
        <div class="person-card ${personAStatus}">
          <div class="person-avatar ${personAStatus}">A</div>
          <div class="person-name">Person A</div>
          <div class="person-status ${personAStatus}">${this.getStatusText(personAStatus)}</div>
        </div>
        <div class="person-card ${personBStatus}">
          <div class="person-avatar ${personBStatus}">B</div>
          <div class="person-name">Person B</div>
          <div class="person-status ${personBStatus}">${this.getStatusText(personBStatus)}</div>
        </div>
      </div>

      <div class="toxicity-details">
        <div class="detail-section">
          <div class="detail-label">
            <span>🎯</span>
            Communication Patterns
          </div>
          <div class="behavior-tags">
            ${analysis.behaviors.map(behavior =>
            `<span class="behavior-tag ${analysis.level.toLowerCase()}">${behavior}</span>`
        ).join('')}
          </div>
        </div>
        
        ${analysis.problem !== 'No significant issues' ? `
          <div class="detail-section">
            <div class="detail-label">
              <span>💬</span>
              Example
            </div>
            <div class="problematic-message">
              "${analysis.problem}"
            </div>
          </div>
        ` : ''}
      </div>

      <div class="toxicity-suggestion">
        <div class="suggestion-header">
          <span>💡</span>
          Suggestion
        </div>
        <div class="suggestion-content">
          ${analysis.suggestion}
        </div>
      </div>
    `;
    }

    getPersonStatus(person, toxicPerson) {
        if (toxicPerson === `Person ${person}`) return 'toxic';
        if (toxicPerson === 'Both') return 'moderate';
        if (toxicPerson === 'None') return 'good';
        return 'neutral';
    }

    getStatusText(status) {
        switch (status) {
            case 'toxic': return 'Needs Attention';
            case 'moderate': return 'Some Concerns';
            case 'good': return 'Good';
            default: return 'Neutral';
        }
    }

    showIndicator() {
        if (this.indicator) {
            this.indicator.classList.remove('toxicity-hidden');
        }
    }

    hideIndicator() {
        if (this.indicator) {
            this.indicator.classList.add('toxicity-hidden');
        }
    }
}

// Initialize when page loads
let analyzer;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        analyzer = new ToxicityAnalyzer();
    });
} else {
    analyzer = new ToxicityAnalyzer();
}

// In content.js - add this function
function receiveToxicityAnalysis(analysisData) {
    console.log('Received toxicity analysis:', analysisData);

    // Display analysis in your extension UI
    if (window.toxicityIndicator) {
        window.toxicityIndicator.displayRedditAnalysis(analysisData);
    }
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'redditAnalysis') {
        receiveToxicityAnalysis(request.data);
    }
});

// Add to content.js
class RedditAnalysisReceiver {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.connect();
    }

    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:8765');

            this.ws.onopen = () => {
                console.log('🔗 Connected to analysis server');
                this.isConnected = true;
                this.showConnectionStatus('connected');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'reddit_analysis') {
                    this.displayAnalysis(data.data);
                }
            };

            this.ws.onclose = () => {
                console.log('🔌 Disconnected from analysis server');
                this.isConnected = false;
                this.showConnectionStatus('disconnected');
                // Reconnect after 5 seconds
                setTimeout(() => this.connect(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnected = false;
                this.showConnectionStatus('error');
            };

        } catch (error) {
            console.error('Failed to connect to analysis server:', error);
        }
    }

    displayAnalysis(analysisData) {
        console.log('📊 Received analysis:', analysisData);

        // Create or update the analysis indicator in the UI
        this.createAnalysisIndicator(analysisData);
    }

    createAnalysisIndicator(analysisData) {
        // Remove existing indicator
        const existingIndicator = document.getElementById('reddit-analysis-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // Create new indicator
        const indicator = document.createElement('div');
        indicator.id = 'reddit-analysis-indicator';
        indicator.innerHTML = `
            <div style="position: fixed; top: 10px; left: 10px; z-index: 10000; 
                       background: white; border: 2px solid #4f46e5; border-radius: 12px; 
                       padding: 15px; max-width: 400px; box-shadow: 0 8px 25px rgba(0,0,0,0.15); 
                       font-family: Arial, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3 style="margin: 0; color: #4f46e5;">🔍 Reddit Analysis</h3>
                    <button onclick="this.parentElement.parentElement.remove()" 
                            style="background: none; border: none; font-size: 18px; cursor: pointer;">×</button>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>${analysisData.post_title}</strong>
                </div>
                <div style="background: #f3f4f6; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                    <strong>Toxicity Level:</strong> 
                    <span style="color: ${analysisData.toxicity_level === 'High' ? '#ef4444' :
                analysisData.toxicity_level === 'Medium' ? '#f59e0b' : '#10b981'
            };">${analysisData.toxicity_level}</span>
                </div>
                <div style="font-size: 14px; color: #666; max-height: 200px; overflow-y: auto;">
                    ${analysisData.analysis_summary}
                </div>
            </div>
        `;

        document.body.appendChild(indicator);

        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (indicator.parentElement) {
                indicator.remove();
            }
        }, 30000);
    }

    showConnectionStatus(status) {
        // You can add connection status indicator to your extension UI
        console.log(`Connection status: ${status}`);
    }
}

// Initialize when content script loads
const analysisReceiver = new RedditAnalysisReceiver();