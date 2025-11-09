# 🧠 Sentimind — The emotional radar for your digital world.

A comprehensive **AI-powered system** that detects and analyzes **tone, trust and intent** in real-time conversations across multiple platforms including Reddit, chat applications, and social media.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-green.svg)
![AI](https://img.shields.io/badge/AI-Gemini%202.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

---

## 🚀 Overview

**Sentimind** integrates a Chrome extension for live chat analysis and a Reddit MCP server for large-scale social data analysis.  
Powered by **Google Gemini 2.0 AI**, the system identifies **sentiment patterns**, **toxic behaviors**, and offers **constructive feedback** to improve digital communication.

### ✨ Key Features

- **🔍 Real-time Analysis**: Monitors conversations as they happen  
- **🌐 Multi-Platform Support**: Works with WhatsApp, Messenger, Telegram, Discord, and Reddit  
- **🤖 AI-Powered Intelligence**: Uses Gemini 2.0 Flash for advanced contextual sentiment detection  
- **📊 Visual Feedback**: Intuitive UI displaying sentiment and toxicity levels with suggestions  
- **🛡️ Privacy-First**: No user data stored — all analysis happens locally  
- **⚡ MCP Integration**: Seamless AI orchestration using the Model Context Protocol  

---

## 🏗️ Architecture

```
Sentimind System
├── 🖥️ Chrome Extension (Frontend)
│   ├── Real-time chat monitoring
│   ├── Sentiment & toxicity indicator overlay
│   └── Gemini AI integration
├── 🔌 Reddit MCP Server (Backend)
│   ├── Live Reddit data crawling
│   ├── Sentiment and toxic pattern detection
│   └── Conversation formatting
└── 🤖 Dedalus Agent (Orchestration)
    ├── MCP client management
    ├── Gemini API coordination
    └── Analysis pipeline
```

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.10+
- Chrome Browser
- Reddit API credentials
- Gemini API key
- Dedalus API key

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sentiMind.git
cd sentiMind
```

---

### 2. Backend Setup (Reddit MCP Server)

```bash
cd reddit-mcp-server

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start the server
python reddit_sentimind_server.py
```

---

### 3. Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`  
2. Enable **Developer mode**  
3. Click **Load unpacked** and select the `chrome-extension/` folder  
4. Click the extension icon and enter your **Gemini API key**

---

### 4. Agent Setup

```bash
cd dedalus-agent

# Create virtual environment
python3.10 -m venv sentimind_env
source sentimind_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the agent
python agent.py
```

---

## 🔑 API Configuration

### Required API Keys

- **Reddit API** — [Get from Reddit App Preferences](https://www.reddit.com/prefs/apps)
- **Gemini API** — [Get from Google AI Studio](https://aistudio.google.com/)
- **Dedalus API** — [Get from Dedalus Labs](https://dedalus.ai/)

### Environment Variables

```env
# dedalus-agent/.env
DEDALUS_API_KEY=your_dedalus_key
GEMINI_API_KEY=your_gemini_key
REDDIT_SERVER_URL=http://localhost:8000

# reddit-mcp-server/.env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
```

---

## 🎯 Usage

### Real-time Chat Analysis

1. Install the Chrome extension  
2. Navigate to any supported chat platform (WhatsApp Web, Messenger, etc.)  
3. Start chatting — Sentimind automatically analyzes conversations  
4. View **sentiment and toxicity indicators** with improvement suggestions  

### Reddit Analysis

1. Start the Reddit MCP server  
2. Run the Dedalus Agent for live Reddit sentiment tracking  
3. Monitor results in real-time via WebSocket  

---

### ✅ Supported Platforms

- WhatsApp Web  
- Facebook Messenger  
- Telegram Web  
- Discord  
- Slack  
- Microsoft Teams  
- Reddit (via MCP Server)

---

## 📊 Features in Detail

### 🧩 Sentiment & Toxicity Detection

- **Pattern Recognition** — Detects insults, sarcasm, manipulation  
- **Communication Analysis** — Identifies tone, emotion, and passive-aggressive behavior  
- **Real-time Scoring** — Displays instant sentiment levels (Positive / Neutral / Negative)

### 💬 User Interface

- **Floating Indicator** — Non-intrusive overlay  
- **Color-coded Alerts** — Visual representation of sentiment intensity  
- **Actionable Suggestions** — Constructive communication improvement advice  

### ⚙️ MCP Integration

- **Standard Protocol** — Uses Model Context Protocol for orchestration  
- **Extensible Design** — Add new data sources easily  
- **Scalable Deployment** — Production-ready modular setup  

---

## 🚀 Quick Start

```bash
# 1. Start Reddit server (Terminal 1)
cd reddit-mcp-server && python reddit_sentimind_server.py

# 2. Start WebSocket server (Terminal 2)
cd dedalus-agent && source sentimind_env/bin/activate && python websocket_server.py

# 3. Run agent (Terminal 3)
cd dedalus-agent && source sentimind_env/bin/activate && python agent.py

# 4. Load Chrome extension in browser
```

---

## 🧪 Testing

```bash
# Test Reddit server
cd reddit-mcp-server && python test_reddit_server.py

# Test agent integration
cd dedalus-agent && python test_integration.py

# Run all tests
./run_tests.sh
```

---

## 📁 Project Structure

```
sentimind/
├── 📖 README.md
├── 📁 chrome-extension/          # Browser extension
│   ├── manifest.json
│   ├── content.js               # Core analysis logic
│   ├── popup.html               # Extension UI
│   ├── content.css              # Styling
│   └── icons/                   # Icons
├── 📁 reddit-mcp-server/        # Reddit data server
│   ├── reddit_sentimind_server.py
│   ├── requirements.txt
│   └── test_reddit_server.py
├── 📁 dedalus-agent/            # AI orchestration
│   ├── agent.py
│   ├── websocket_server.py
│   ├── requirements.txt
│   └── .env.example
└── 📁 docs/                     # Documentation
    ├── architecture.md
    └── api-reference.md
```

---

## 🔧 Development

### Adding New Platforms

1. Extend `content.js` with new platform selectors  
2. Update permissions in `manifest.json`  
3. Test extraction patterns  

### Customizing Analysis

- Modify detection patterns in Reddit crawler  
- Adjust Gemini prompt templates for emotion depth  
- Extend MCP tools for multimodal understanding  

### Building for Production

```bash
# Package Chrome extension
cd chrome-extension && zip -r sentimind.zip .

# Dockerize servers
docker build -t sentimind .
```

---

## 🤝 Contributing

We welcome contributions! See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

1. Fork the repository  
2. Create a feature branch  
3. Commit your changes  
4. Push and open a pull request  

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** for advanced AI capabilities  
- **Reddit PRAW** for API integration  
- **Dedalus Labs** for MCP orchestration  
- **Chrome Extension API** for seamless browser integration  

---

<div align="center">
Built with ❤️ for emotionally intelligent online communication.  

![Star History](https://api.star-history.com/svg?repos=yourusername/sentimind&type=Date)
</div>
