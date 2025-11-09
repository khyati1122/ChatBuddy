#!/usr/bin/env python3
"""
REDDIT MCP SERVER FOR TOXICITY ANALYSIS
========================================

Features:
- Search multiple subreddits for toxic behavior patterns
- Extract conversations and comments for analysis
- Real-time monitoring of toxic discussions
- Integration with Gemini AI for toxicity scoring

Setup:
1. pip install praw flask flask-cors requests
2. Get Reddit credentials from https://www.reddit.com/prefs/apps
3. Replace credentials below
4. Run: python reddit_toxicity_server.py
"""

import praw
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any

# ===== REDDIT CONFIGURATION =====
REDDIT_CLIENT_ID = "LMUF4NdFuf3HF8OwMS3KJw"
REDDIT_CLIENT_SECRET = "g8vywXGmClkID4tmkCW53OlBWSrGRw"
# =================================

# Toxic behavior keywords for targeted search
TOXIC_KEYWORDS = [
    "toxic", "gaslighting", "narcissist", "manipulation", "emotional abuse",
    "controlling", "jealous", "cheating", "lying", "trust issues",
    "breakup", "divorce", "argument", "fight", "conflict",
    "disrespect", "insults", "name calling", "yelling", "silent treatment",
    "guilt trip", "passive aggressive", "stonewalling", "criticism"
]

# Subreddits focused on relationships and personal issues
RELATIONSHIP_SUBREDDITS = [
    "relationship_advice", "relationships", "AmItheAsshole", 
    "dating_advice", "marriage", "breakups", "infidelity",
    "socialskills", "communication", "mentalhealth"
]

# Initialize Reddit
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent="ToxicityAnalyzer/2.0"
)

# Initialize Flask
app = Flask(__name__)
CORS(app)

class RedditToxicityCrawler:
    def __init__(self):
        self.reddit = reddit
        self.toxic_patterns = [
            r'\b(loser|idiot|stupid|ugly|worthless|fat|useless)\b',
            r'\b(hate|despise|can\'t stand)\b.*\b(you|your)\b',
            r'\b(always|never)\b.*\b(you)\b',
            r'\b(you\'re|you are)\b.*\b(crazy|insane|delusional)\b',
            r'\b(shut up|shut your mouth|be quiet)\b',
            r'\b(nobody|no one)\b.*\b(love|like|care about)\b.*\b(you)\b'
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        if not text:
            return ""
        # Remove URLs, markdown, and extra whitespace
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'\*\*.*?\*\*', '', text)
        text = re.sub(r'\*.*?\*', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def detect_toxic_patterns(self, text: str) -> List[str]:
        """Detect toxic language patterns in text"""
        found_patterns = []
        text_lower = text.lower()
        
        for pattern in self.toxic_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_patterns.append(pattern)
        
        # Check for toxic keywords
        for keyword in TOXIC_KEYWORDS:
            if keyword in text_lower:
                found_patterns.append(f"keyword: {keyword}")
        
        return found_patterns
    
    def extract_conversation_thread(self, submission) -> Dict[str, Any]:
        """Extract a conversation thread from a post and its comments"""
        try:
            # Get post content
            post_data = {
                "title": submission.title,
                "content": self.clean_text(submission.selftext),
                "author": str(submission.author),
                "score": submission.score,
                "created_utc": submission.created_utc,
                "url": f"https://reddit.com{submission.permalink}",
                "subreddit": submission.subreddit.display_name,
                "toxic_patterns": self.detect_toxic_patterns(
                    f"{submission.title} {submission.selftext}"
                )
            }
            
            # Get top-level comments as conversation
            comments = []
            submission.comments.replace_more(limit=0)  # Remove "load more" comments
            
            for comment in submission.comments.list()[:20]:  # Top 20 comments
                if not comment.body or comment.body == '[deleted]':
                    continue
                    
                comment_data = {
                    "author": str(comment.author),
                    "content": self.clean_text(comment.body),
                    "score": comment.score,
                    "created_utc": comment.created_utc,
                    "toxic_patterns": self.detect_toxic_patterns(comment.body),
                    "is_op_reply": comment.parent_id == submission.name
                }
                comments.append(comment_data)
            
            return {
                "post": post_data,
                "comments": comments,
                "total_toxic_patterns": len(post_data["toxic_patterns"]) + 
                                      sum(len(c["toxic_patterns"]) for c in comments),
                "conversation_snippet": self.create_conversation_snippet(post_data, comments)
            }
            
        except Exception as e:
            return {"error": f"Failed to extract thread: {str(e)}"}
    
    def create_conversation_snippet(self, post: Dict, comments: List[Dict]) -> str:
        """Create a formatted conversation snippet for Gemini analysis"""
        snippet = f"OP: {post['content'][:300]}\n\n"
        
        for i, comment in enumerate(comments[:8]):  # First 8 comments
            author = "OP" if comment["is_op_reply"] else f"User{i+1}"
            snippet += f"{author}: {comment['content'][:200]}\n\n"
        
        return snippet

crawler = RedditToxicityCrawler()

@app.route('/search_toxic_posts', methods=['POST'])
def search_toxic_posts():
    """Search for posts containing toxic behavior patterns"""
    data = request.json
    keyword = data.get('keyword', 'toxic')
    subreddit_name = data.get('subreddit', 'relationship_advice')
    limit = data.get('limit', 10)
    time_filter = data.get('time_filter', 'month')
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.search(keyword, limit=limit, time_filter=time_filter)
        
        results = []
        for post in posts:
            thread_data = crawler.extract_conversation_thread(post)
            if "error" not in thread_data:
                results.append(thread_data)
        
        return jsonify({
            "keyword": keyword,
            "subreddit": subreddit_name,
            "time_filter": time_filter,
            "total_results": len(results),
            "results": results[:5]  # Return top 5 most relevant
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_hot_toxic_discussions', methods=['POST'])
def get_hot_toxic_discussions():
    """Get currently hot discussions that might contain toxic behavior"""
    data = request.json
    subreddit_name = data.get('subreddit', 'relationship_advice')
    limit = data.get('limit', 15)
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        hot_posts = subreddit.hot(limit=limit)
        
        toxic_discussions = []
        for post in hot_posts:
            # Check if post title contains toxic keywords
            title_lower = post.title.lower()
            if any(keyword in title_lower for keyword in TOXIC_KEYWORDS):
                thread_data = crawler.extract_conversation_thread(post)
                if "error" not in thread_data:
                    toxic_discussions.append(thread_data)
        
        return jsonify({
            "subreddit": subreddit_name,
            "total_discussions": len(toxic_discussions),
            "discussions": toxic_discussions
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_user_history', methods=['POST'])
def analyze_user_history():
    """Analyze a user's post history for toxic behavior patterns"""
    data = request.json
    username = data.get('username')
    limit = data.get('limit', 25)
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    try:
        user = reddit.redditor(username)
        posts = []
        
        # Get user's recent posts
        for submission in user.submissions.new(limit=limit):
            post_data = {
                "title": submission.title,
                "content": crawler.clean_text(submission.selftext),
                "subreddit": submission.subreddit.display_name,
                "score": submission.score,
                "created_utc": submission.created_utc,
                "url": f"https://reddit.com{submission.permalink}",
                "toxic_patterns": crawler.detect_toxic_patterns(
                    f"{submission.title} {submission.selftext}"
                )
            }
            posts.append(post_data)
        
        # Calculate toxicity metrics
        total_toxic_patterns = sum(len(post["toxic_patterns"]) for post in posts)
        toxic_posts_count = sum(1 for post in posts if post["toxic_patterns"])
        
        return jsonify({
            "username": username,
            "total_posts_analyzed": len(posts),
            "toxic_posts_count": toxic_posts_count,
            "total_toxic_patterns": total_toxic_patterns,
            "toxicity_score": round((toxic_posts_count / len(posts)) * 100, 2) if posts else 0,
            "posts": posts
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_conversation_for_analysis', methods=['POST'])
def get_conversation_for_analysis():
    """Get a complete conversation thread formatted for Gemini toxicity analysis"""
    data = request.json
    post_url = data.get('post_url')
    
    if not post_url:
        return jsonify({"error": "Post URL is required"}), 400
    
    try:
        # Extract post ID from URL
        if '/comments/' in post_url:
            post_id = post_url.split('/comments/')[1].split('/')[0]
            submission = reddit.submission(id=post_id)
        else:
            return jsonify({"error": "Invalid Reddit post URL"}), 400
        
        thread_data = crawler.extract_conversation_thread(submission)
        
        if "error" in thread_data:
            return jsonify(thread_data), 400
        
        # Format for Gemini analysis
        gemini_format = {
            "conversation_context": {
                "title": thread_data["post"]["title"],
                "subreddit": thread_data["post"]["subreddit"],
                "url": thread_data["post"]["url"]
            },
            "conversation_text": thread_data["conversation_snippet"],
            "toxic_patterns_found": thread_data["total_toxic_patterns"],
            "analysis_ready": True,
            "participants": len(set(
                [thread_data["post"]["author"]] + 
                [c["author"] for c in thread_data["comments"]]
            ))
        }
        
        return jsonify(gemini_format)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/monitor_subreddit', methods=['POST'])
def monitor_subreddit():
    """Real-time monitoring of new posts in a subreddit for toxic content"""
    data = request.json
    subreddit_name = data.get('subreddit', 'relationship_advice')
    duration_minutes = data.get('duration', 5)
    check_interval = data.get('interval', 30)  # seconds
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        monitored_posts = []
        seen_posts = set()
        
        print(f"🔍 Monitoring r/{subreddit_name} for {duration_minutes} minutes...")
        
        while datetime.now() < end_time:
            try:
                for post in subreddit.new(limit=10):
                    if post.id not in seen_posts:
                        seen_posts.add(post.id)
                        
                        # Check for toxic keywords
                        title_lower = post.title.lower()
                        content_lower = post.selftext.lower() if post.selftext else ""
                        
                        if any(keyword in title_lower or keyword in content_lower 
                              for keyword in TOXIC_KEYWORDS):
                            
                            thread_data = crawler.extract_conversation_thread(post)
                            if "error" not in thread_data:
                                monitored_posts.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "post": thread_data["post"],
                                    "toxic_patterns": thread_data["total_toxic_patterns"],
                                    "urgency": "high" if thread_data["total_toxic_patterns"] > 3 else "medium"
                                })
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(check_interval)
        
        return jsonify({
            "subreddit": subreddit_name,
            "monitoring_duration": f"{duration_minutes} minutes",
            "total_new_posts_found": len(seen_posts),
            "toxic_posts_detected": len(monitored_posts),
            "results": monitored_posts
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Check server and Reddit connection status"""
    try:
        # Test Reddit connection
        reddit.user.me()
        reddit_status = "connected"
        
        # Test subreddit access
        test_sub = reddit.subreddit("relationship_advice")
        test_post = next(test_sub.hot(limit=1))
        subreddit_access = "working"
        
    except Exception as e:
        reddit_status = f"error: {str(e)}"
        subreddit_access = "failed"
    
    return jsonify({
        "status": "running",
        "reddit_connection": reddit_status,
        "subreddit_access": subreddit_access,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "search_toxic_posts": "POST - Search for toxic posts",
            "get_hot_toxic_discussions": "POST - Get hot toxic discussions", 
            "analyze_user_history": "POST - Analyze user toxicity",
            "get_conversation_for_analysis": "POST - Get formatted conversation",
            "monitor_subreddit": "POST - Real-time monitoring"
        }
    })

def self_test():
    """Auto-test the server after startup"""
    import requests
    import threading
    import time
    
    def run_tests():
        time.sleep(3)
        
        print("\n" + "="*60)
        print("🧪 REDDIT TOXICITY MCP SERVER - SELF TEST")
        print("="*60)
        
        base_url = "http://localhost:8000"
        
        try:
            # Test 1: Health check
            print("\n1. Testing health endpoint...")
            response = requests.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ Server running - Reddit: {health_data['reddit_connection']}")
            else:
                print("   ❌ Health check failed")
                return
            
            # Test 2: Search toxic posts
            print("\n2. Testing toxic post search...")
            response = requests.post(f"{base_url}/search_toxic_posts", 
                                   json={"keyword": "gaslighting", "limit": 3})
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['total_results']} toxic posts in r/{data['subreddit']}")
                if data['results']:
                    print(f"   📝 Sample: '{data['results'][0]['post']['title'][:50]}...'")
            else:
                print(f"   ⚠️ Search test failed: {response.json().get('error', 'Unknown error')}")
            
            # Test 3: Get conversation for analysis
            print("\n3. Testing conversation extraction...")
            response = requests.post(f"{base_url}/get_hot_toxic_discussions", 
                                   json={"limit": 2})
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['total_discussions']} hot toxic discussions")
                if data['discussions']:
                    conv = data['discussions'][0]
                    print(f"   💬 Conversation snippet ready for Gemini analysis")
                    print(f"   🎯 Toxic patterns detected: {conv['total_toxic_patterns']}")
            
            print("\n" + "="*60)
            print("✨ REDDIT TOXICITY MCP SERVER IS READY!")
            print("="*60)
            print("\n📡 Server URL: http://localhost:8000")
            print("\n🔧 Available Endpoints:")
            print("   POST /search_toxic_posts - Search for toxic content")
            print("   POST /get_hot_toxic_discussions - Get trending toxic discussions") 
            print("   POST /analyze_user_history - Analyze user toxicity patterns")
            print("   POST /get_conversation_for_analysis - Format conversation for AI")
            print("   POST /monitor_subreddit - Real-time toxic content monitoring")
            print("   GET  /health - Server status check")
            
            print("\n💡 Integration with Gemini:")
            print("   Use /get_conversation_for_analysis to get formatted conversations")
            print("   Send the conversation_text to Gemini for toxicity analysis")
            print("   Combine with your Chrome extension for comprehensive analysis")
            
        except Exception as e:
            print(f"❌ Self-test failed: {e}")
    
    test_thread = threading.Thread(target=run_tests)
    test_thread.daemon = True
    test_thread.start()

if __name__ == "__main__":
    print("\n🚀 Starting Reddit Toxicity MCP Server...")
    print("=" * 60)
    print("🔍 Designed for Gemini AI Toxicity Analysis")
    print("📊 Monitoring relationship subreddits for toxic patterns")
    print("🤖 Perfect for Dedalus AI orchestration")
    print("=" * 60)
    
    # Run self-test
    self_test()
    
    # Start server
    app.run(host='0.0.0.0', port=8000, debug=False)