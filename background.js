// Background script for extension management
chrome.runtime.onInstalled.addListener(() => {
    console.log('Emotion Analysis Assistant installed');

    // Set default settings
    chrome.storage.local.set({
        analysisType: 'comprehensive',
        analysisDelay: 10,
        messageCount: 10,
        detailLevel: 'moderate',
        isActive: false
    });
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
    // Open popup by default (handled by manifest)
});

// Keep service worker alive
chrome.runtime.onStartup.addListener(() => {
    console.log('Emotion Analysis Assistant starting up');
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'log') {
        console.log('Content Script:', request.message);
    }
    sendResponse({ received: true });
});

// Add this to your existing backend (e.g., background.js or a new API file)
class MCPIntegration {
    constructor(mcpServerUrl = 'http://localhost:8000') {
        this.mcpServerUrl = mcpServerUrl;
    }

    async validateToxicityWithReddit(conversationData, apiKey) {
        try {
            // Step 1: Get toxicity analysis
            const analysisResponse = await fetch(`${this.mcpServerUrl}/analyze/toxicity`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_data: conversationData,
                    api_key: apiKey,
                    sensitivity: 'medium'
                })
            });

            const analysis = await analysisResponse.json();

            // Step 2: Search Reddit for validation
            const redditResponse = await fetch(`${this.mcpServerUrl}/search/reddit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    keywords: analysis.analysis.keywords.slice(0, 5),
                    limit: 5
                })
            });

            const redditData = await redditResponse.json();

            // Step 3: Validate with human perspectives
            const validationResponse = await fetch(`${this.mcpServerUrl}/validate/toxicity`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chat_data: conversationData,
                    subreddit_data: redditData.subreddits_found.slice(0, 3),
                    api_key: apiKey
                })
            });

            const validation = await validationResponse.json();

            return {
                initialAnalysis: analysis,
                communityValidation: validation,
                relevantCommunities: redditData.subreddits_found
            };

        } catch (error) {
            console.error('MCP Integration error:', error);
            throw error;
        }
    }
}

// Usage in your extension
// const mcp = new MCPIntegration();
// const results = await mcp.validateToxicityWithReddit(chatMessages, apiKey);