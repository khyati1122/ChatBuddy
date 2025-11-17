"""
Reddit Context Crawler MCP Server
Crawls Reddit for relevant discussions based on anonymized chat history context
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# MCP imports
from mcp.server.fastmcp import FastMCP

# Reddit API wrapper
import praw
from praw.models import Submission, Comment
import prawcore

# NLP for keyword extraction
from collections import Counter
import string

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# NEW - Log to file instead of console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reddit_mcp.log')  # Log to file, not console!
    ]
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("Reddit Context Crawler")

# Reddit API configuration (you'll need to set these as environment variables)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MCP Reddit Crawler v1.0")

# Initialize Reddit instance
reddit = None
try:
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            check_for_async=False
        )
        reddit.read_only = True
        logger.info("Reddit API initialized successfully")
    else:
        logger.warning("Reddit API credentials not found. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
except Exception as e:
    logger.error(f"Failed to initialize Reddit API: {e}")

# Helper functions
def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from anonymized chat history
    Removes common words and focuses on meaningful terms
    """
    # Common words to filter out
    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'was',
        'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'to', 'of', 'in',
        'for', 'with', 'by', 'from', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then',
        'once', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
        'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
        'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
        'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'will', 'dont',
        'just', 'not', 'only', 'very', 'too', 'also', 'than', 'so', 'if', 'but'
    }
    
    # Convert to lowercase and remove punctuation
    text_lower = text.lower()
    translator = str.maketrans('', '', string.punctuation)
    text_clean = text_lower.translate(translator)
    
    # Split into words
    words = text_clean.split()
    
    # Filter out stop words and short words
    meaningful_words = [
        word for word in words 
        if word not in stop_words and len(word) > 2
    ]
    
    # Count word frequency
    word_freq = Counter(meaningful_words)
    
    # Get most common keywords
    keywords = [word for word, _ in word_freq.most_common(max_keywords)]
    
    return keywords

def anonymize_text(text: str) -> str:
    """
    Remove any potential personal information from text
    """
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)
    
    # Remove phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\d{10}\b', '[PHONE]', text)
    
    # Remove potential social media handles
    text = re.sub(r'@\w+', '[USER]', text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '[URL]', text)
    
    # Remove potential names (capitalized words that aren't sentence starters)
    # This is a simple heuristic and may not catch all names
    sentences = text.split('.')
    for i, sentence in enumerate(sentences):
        words = sentence.split()
        for j, word in enumerate(words):
            if j > 0 and word[0].isupper() and word.lower() not in ['i']:
                words[j] = '[NAME]'
        sentences[i] = ' '.join(words)
    text = '. '.join(sentences)
    
    return text

def search_reddit_by_keywords(keywords: List[str], limit: int = 20) -> List[Dict]:
    """
    Search Reddit for relevant discussions based on keywords
    """
    if not reddit:
        raise Exception("Reddit API not initialized")
    
    results = []
    search_query = ' '.join(keywords[:5])  # Use top 5 keywords for search
    
    try:
        # Search across all of Reddit
        for submission in reddit.subreddit("all").search(search_query, limit=limit, sort="relevance"):
            result = {
                'subreddit': submission.subreddit.display_name,
                'title': submission.title,
                'url': f"https://reddit.com{submission.permalink}",
                'score': submission.score,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'selftext': submission.selftext[:500] if submission.selftext else "",
                'comments': []
            }
            
            # Get top comments (limited to avoid rate limiting)
            submission.comments.replace_more(limit=0)
            for comment in submission.comments[:5]:
                if isinstance(comment, Comment):
                    comment_text = anonymize_text(comment.body)
                    if len(comment_text) > 20:  # Filter out very short comments
                        result['comments'].append({
                            'text': comment_text,
                            'score': comment.score
                        })
            
            results.append(result)
            
    except prawcore.exceptions.ResponseException as e:
        logger.error(f"Reddit API error: {e}")
        raise Exception(f"Reddit API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error searching Reddit: {e}")
        raise Exception(f"Error searching Reddit: {str(e)}")
    
    return results

def find_relevant_subreddits(keywords: List[str], limit: int = 10) -> List[str]:
    """
    Find relevant subreddits based on keywords
    """
    if not reddit:
        raise Exception("Reddit API not initialized")
    
    subreddits = set()
    
    try:
        # Search for subreddits
        for subreddit in reddit.subreddits.search(' '.join(keywords[:3]), limit=limit):
            subreddits.add(subreddit.display_name)
    except Exception as e:
        logger.error(f"Error finding subreddits: {e}")
    
    return list(subreddits)

def format_reddit_results(results: List[Dict], max_results: int = 10) -> Dict:
    """
    Format Reddit results into structured JSON
    """
    # Sort by relevance (score + number of comments)
    sorted_results = sorted(
        results, 
        key=lambda x: x['score'] + x['num_comments'], 
        reverse=True
    )[:max_results]
    
    formatted_results = []
    for result in sorted_results:
        formatted_result = {
            'subreddit': result['subreddit'],
            'title': result['title'],
            'url': result['url'],
            'relevance_score': result['score'] + result['num_comments'],
            'discussions': []
        }
        
        # Add main post content if available
        if result['selftext']:
            formatted_result['discussions'].append({
                'type': 'post',
                'content': result['selftext'],
                'score': result['score']
            })
        
        # Add comments
        for comment in result['comments']:
            formatted_result['discussions'].append({
                'type': 'comment',
                'content': comment['text'],
                'score': comment['score']
            })
        
        formatted_results.append(formatted_result)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'results_count': len(formatted_results),
        'reddit_discussions': formatted_results
    }

# MCP Tools

@mcp.tool()
def crawl_reddit_from_chat(
    chat_history: str,
    max_results: int = 10,
    search_subreddits: bool = True
) -> Dict[str, Any]:
    """
    Crawl Reddit based on anonymized chat history context.
    
    Args:
        chat_history: Anonymized chat history to extract context from
        max_results: Maximum number of results to return (default: 10)
        search_subreddits: Whether to also search for relevant subreddits (default: True)
    
    Returns:
        JSON containing relevant Reddit discussions and subreddits
    """
    try:
        # Ensure Reddit is initialized
        if not reddit:
            return {
                'error': 'Reddit API not initialized. Please configure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.',
                'status': 'error'
            }
        
        # Anonymize the chat history
        anonymized_chat = anonymize_text(chat_history)
        
        # Extract keywords from chat history
        keywords = extract_keywords(anonymized_chat)
        
        if not keywords:
            return {
                'error': 'Could not extract meaningful keywords from the chat history',
                'status': 'error'
            }
        
        # Search Reddit
        reddit_results = search_reddit_by_keywords(keywords, limit=max_results * 2)
        
        # Format results
        formatted_results = format_reddit_results(reddit_results, max_results)
        formatted_results['extracted_keywords'] = keywords
        
        # Find relevant subreddits if requested
        if search_subreddits:
            relevant_subreddits = find_relevant_subreddits(keywords)
            formatted_results['suggested_subreddits'] = relevant_subreddits
        
        formatted_results['status'] = 'success'
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error in crawl_reddit_from_chat: {e}")
        return {
            'error': str(e),
            'status': 'error'
        }

@mcp.tool()
def search_reddit_keywords(
    keywords: List[str],
    subreddit: Optional[str] = None,
    max_results: int = 10,
    time_filter: str = "all"
) -> Dict[str, Any]:
    """
    Search Reddit directly with specific keywords.
    
    Args:
        keywords: List of keywords to search for
        subreddit: Specific subreddit to search in (optional, searches all if not provided)
        max_results: Maximum number of results to return
        time_filter: Time filter for search ("all", "day", "week", "month", "year")
    
    Returns:
        JSON containing relevant Reddit discussions
    """
    try:
        if not reddit:
            return {
                'error': 'Reddit API not initialized. Please configure credentials.',
                'status': 'error'
            }
        
        # Determine which subreddit to search
        search_sub = reddit.subreddit(subreddit) if subreddit else reddit.subreddit("all")
        
        # Build search query
        search_query = ' '.join(keywords)
        
        results = []
        for submission in search_sub.search(search_query, limit=max_results, time_filter=time_filter, sort="relevance"):
            result = {
                'subreddit': submission.subreddit.display_name,
                'title': submission.title,
                'url': f"https://reddit.com{submission.permalink}",
                'score': submission.score,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'selftext': anonymize_text(submission.selftext[:500]) if submission.selftext else "",
                'comments': []
            }
            
            # Get top comments
            submission.comments.replace_more(limit=0)
            for comment in submission.comments[:5]:
                if isinstance(comment, Comment):
                    comment_text = anonymize_text(comment.body)
                    if len(comment_text) > 20:
                        result['comments'].append({
                            'text': comment_text,
                            'score': comment.score
                        })
            
            results.append(result)
        
        # Format and return results
        formatted_results = format_reddit_results(results, max_results)
        formatted_results['search_keywords'] = keywords
        formatted_results['subreddit_searched'] = subreddit if subreddit else "all"
        formatted_results['time_filter'] = time_filter
        formatted_results['status'] = 'success'
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error in search_reddit_keywords: {e}")
        return {
            'error': str(e),
            'status': 'error'
        }

@mcp.tool()
def get_subreddit_info(subreddit_name: str) -> Dict[str, Any]:
    """Get information about a specific subreddit."""
    try:
        if not reddit:
            return {
                'error': 'Reddit API not initialized',
                'status': 'error'
            }
        
        # Get the subreddit
        subreddit = reddit.subreddit(subreddit_name)
        
        # Build info dict - access properties directly
        info = {
            'name': subreddit.display_name,
            'title': subreddit.title,
            'description': subreddit.public_description[:500] if hasattr(subreddit, 'public_description') and subreddit.public_description else "",
            'subscribers': subreddit.subscribers if hasattr(subreddit, 'subscribers') else 0,
            'created_utc': subreddit.created_utc if hasattr(subreddit, 'created_utc') else 0,
            'over18': subreddit.over18 if hasattr(subreddit, 'over18') else False,
            'status': 'success'
        }
        
        # Get recent top posts - this part was causing issues
        recent_posts = []
        for submission in subreddit.hot(limit=5):
            recent_posts.append({
                'title': submission.title,
                'score': submission.score,
                'num_comments': submission.num_comments,
                'url': f"https://reddit.com{submission.permalink}"
            })
        
        info['recent_top_posts'] = recent_posts
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting subreddit info: {e}")
        return {
            'error': str(e),
            'status': 'error'
        }

@mcp.tool()
def test_reddit_connection() -> Dict[str, Any]:
    """Test if Reddit connection is working"""
    try:
        if not reddit:
            return {"status": "error", "message": "Reddit object is None"}
        
        # Try to access Reddit front page
        for submission in reddit.subreddit("all").hot(limit=1):
            return {
                "status": "success",
                "message": "Reddit connection working!",
                "sample_post": submission.title
            }
        
        return {"status": "error", "message": "No posts found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    """Run the MCP server"""
    # Remove all print statements - they interfere with MCP protocol!
    # Warnings are logged to file instead
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.warning("Reddit API credentials not configured.")
        logger.warning("Using read-only mode without authentication")
    
    # Run the server
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()