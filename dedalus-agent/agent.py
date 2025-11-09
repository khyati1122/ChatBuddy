# import asyncio
# from dedalus_labs import AsyncDedalus, DedalusRunner
# from dotenv import load_dotenv
# import os
# import aiohttp
# import json

# load_dotenv()

# class RedditToxicityIntegration:
#     def __init__(self):
#         self.reddit_server_url = "http://localhost:8000"
    
#     async def get_toxic_posts_for_analysis(self, keyword: str = "toxic", limit: int = 5):
#         """Fetch toxic posts from Reddit MCP server"""
#         try:
#             async with aiohttp.ClientSession() as session:
#                 # Get posts from Reddit server
#                 async with session.post(
#                     f"{self.reddit_server_url}/search_toxic_posts",
#                     json={"keyword": keyword, "limit": limit}
#                 ) as response:
                    
#                     if response.status == 200:
#                         data = await response.json()
#                         return self._format_for_gemini(data)
#                     else:
#                         return {"error": f"Failed to fetch posts: {response.status}"}
                        
#         except Exception as e:
#             return {"error": f"Connection error: {str(e)}"}
    
#     def _format_for_gemini(self, reddit_data):
#         """Format Reddit posts for Gemini toxicity analysis"""
#         if "results" not in reddit_data or not reddit_data["results"]:
#             return {"message": "No toxic posts found"}
        
#         formatted_posts = []
#         for post in reddit_data["results"]:
#             formatted_post = {
#                 "title": post["post"]["title"],
#                 "content": post["post"]["content"],
#                 "subreddit": post["post"]["subreddit"],
#                 "url": post["post"]["url"],
#                 "toxic_patterns": post["toxic_patterns"],
#                 "conversation_snippet": post["conversation_snippet"],
#                 "analysis_ready": True
#             }
#             formatted_posts.append(formatted_post)
        
#         return {
#             "total_posts": len(formatted_posts),
#             "search_term": reddit_data.get("keyword", "toxic"),
#             "posts": formatted_posts
#         }

# async def analyze_toxic_reddit_posts():
#     """Main function to analyze toxic Reddit posts using Dedalus + Gemini"""
#     client = AsyncDedalus()
#     runner = DedalusRunner(client)
    
#     # Initialize Reddit integration
#     reddit_integration = RedditToxicityIntegration()
    
#     print("🔍 Fetching toxic posts from Reddit...")
    
#     # Step 1: Get toxic posts from Reddit MCP server
#     reddit_posts = await reddit_integration.get_toxic_posts_for_analysis(
#         keyword="gaslighting", 
#         limit=3
#     )
    
#     if "error" in reddit_posts:
#         print(f"❌ Error: {reddit_posts['error']}")
#         return
    
#     if "message" in reddit_posts:
#         print(f"ℹ️ {reddit_posts['message']}")
#         return
    
#     print(f"✅ Found {reddit_posts['total_posts']} toxic posts")
    
#     # Step 2: Send to Dedalus for Gemini analysis
#     for i, post in enumerate(reddit_posts["posts"]):
#         print(f"\n📊 Analyzing post {i+1}: {post['title'][:50]}...")
        
#         # Create analysis prompt for Gemini
#         analysis_prompt = f"""
#         Analyze this Reddit post for toxic behavior and communication patterns:

#         TITLE: {post['title']}
#         CONTENT: {post['content']}
#         CONVERSATION: {post['conversation_snippet']}
#         SUBREDDIT: r/{post['subreddit']}

#         Please provide a toxicity analysis with:
#         1. Toxicity Level (Low/Medium/High)
#         2. Main toxic behaviors detected
#         3. Which person is primarily responsible (if identifiable)
#         4. Specific examples of toxic communication
#         5. Suggestions for healthier communication

#         Focus on communication patterns and provide constructive feedback.
#         """
        
#         try:
#             # Send to Dedalus (which will use your Gemini agent)
#             response = await runner.run(
#                 input=analysis_prompt,
#                 model="google/gemini-2.0-flash-exp",  # or whatever model you're using
#                 mcp_servers=["your-reddit-mcp-server"]  # Your Reddit MCP server
#             )
            
#             print(f"🎯 Analysis Result:")
#             print(f"   {response.final_output}")
            
#             # You can also send this back to your Chrome extension
#             await send_to_chrome_extension({
#                 "post_title": post["title"],
#                 "analysis": response.final_output,
#                 "url": post["url"]
#             })
            
#         except Exception as e:
#             print(f"❌ Analysis failed for post {i+1}: {str(e)}")

# async def send_to_chrome_extension(analysis_data):
#     """Send analysis results back to your Chrome extension"""
#     # This would connect to your Chrome extension
#     # You might use websockets or the extension's background script
#     print(f"📨 Sending to Chrome extension: {analysis_data['post_title'][:30]}...")
#     # Implementation depends on your extension setup

# async def continuous_monitoring():
#     """Continuous monitoring for new toxic posts"""
#     client = AsyncDedalus()
#     runner = DedalusRunner(client)
#     reddit_integration = RedditToxicityIntegration()
    
#     print("🔄 Starting continuous toxicity monitoring...")
    
#     while True:
#         try:
#             # Monitor for new toxic discussions
#             hot_posts = await reddit_integration.get_toxic_posts_for_analysis(
#                 keyword="",  # Empty to get various toxic posts
#                 limit=5
#             )
            
#             if "posts" in hot_posts and hot_posts["posts"]:
#                 for post in hot_posts["posts"]:
#                     analysis_prompt = f"""
#                     Quick toxicity check for new post:
                    
#                     TITLE: {post['title']}
#                     CONTENT: {post['content'][:200]}...
                    
#                     Provide brief toxicity assessment (1-2 sentences).
#                     """
                    
#                     response = await runner.run(
#                         input=analysis_prompt,
#                         model="google/gemini-2.0-flash-exp",
#                         mcp_servers=["your-reddit-mcp-server"]
#                     )
                    
#                     print(f"🆕 New Post Analysis: {post['title'][:40]}...")
#                     print(f"   📝 {response.final_output}")
            
#             # Wait before next check
#             await asyncio.sleep(60)  # Check every minute
            
#         except Exception as e:
#             print(f"Monitoring error: {e}")
#             await asyncio.sleep(30)

# if __name__ == "__main__":
#     # Run single analysis
#     asyncio.run(analyze_toxic_reddit_posts())
    
#     # Or run continuous monitoring
#     # asyncio.run(continuous_monitoring())

import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from dotenv import load_dotenv
import os
import aiohttp
import json



load_dotenv()

import websockets
import json

class AnalysisSender:
    def __init__(self):
        self.websocket_url = "ws://localhost:8765"
    
    async def send_to_extension(self, analysis_data):
        """Send analysis results to Chrome extension via WebSocket"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                message = {
                    "type": "reddit_analysis",
                    "data": analysis_data
                }
                await websocket.send(json.dumps(message))
                print(f"📨 Sent to extension: {analysis_data['post_title'][:30]}...")
        except Exception as e:
            print(f"❌ Failed to send to extension: {e}")

class RedditToxicityIntegration:
    def __init__(self):
        self.reddit_server_url = "http://localhost:8000"
    
    async def get_toxic_posts_for_analysis(self, keyword: str = "toxic", limit: int = 5):
        """Fetch toxic posts from Reddit MCP server with proper error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get posts from Reddit server
                async with session.post(
                    f"{self.reddit_server_url}/search_toxic_posts",
                    json={"keyword": keyword, "limit": limit},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"📊 Raw Reddit response: {json.dumps(data, indent=2)[:500]}...")
                        return self._format_for_gemini(data)
                    else:
                        error_text = await response.text()
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def _format_for_gemini(self, reddit_data):
        """Format Reddit posts for Gemini toxicity analysis with safe access"""
        print(f"🔧 Formatting data - keys: {list(reddit_data.keys())}")
        
        # Safe data access
        results = reddit_data.get("results", [])
        if not results:
            return {"message": "No toxic posts found", "raw_data": reddit_data}
        
        formatted_posts = []
        for i, post in enumerate(results):
            try:
                # Safe access to nested data
                post_data = post.get("post", {})
                formatted_post = {
                    "title": post_data.get("title", "No title"),
                    "content": post_data.get("content", "No content"),
                    "subreddit": post_data.get("subreddit", "unknown"),
                    "url": post_data.get("url", ""),
                    "toxic_patterns": post.get("toxic_patterns", []),  # This might be the issue
                    "conversation_snippet": post.get("conversation_snippet", ""),
                    "analysis_ready": True
                }
                formatted_posts.append(formatted_post)
                print(f"   ✅ Processed post {i+1}: {formatted_post['title'][:50]}...")
            except Exception as e:
                print(f"   ❌ Error processing post {i+1}: {e}")
                continue
        
        return {
            "total_posts": len(formatted_posts),
            "search_term": reddit_data.get("keyword", "toxic"),
            "posts": formatted_posts
        }

async def analyze_toxic_reddit_posts():
    """Main function to analyze toxic Reddit posts using Dedalus + Gemini"""
    client = AsyncDedalus()
    runner = DedalusRunner(client)
    
    # Initialize Reddit integration
    reddit_integration = RedditToxicityIntegration()
    
    print("🔍 Fetching toxic posts from Reddit...")
    
    # Step 1: Get toxic posts from Reddit MCP server
    reddit_posts = await reddit_integration.get_toxic_posts_for_analysis(
        keyword="gaslighting", 
        limit=2
    )
    
    if "error" in reddit_posts:
        print(f"❌ Error fetching posts: {reddit_posts['error']}")
        
        # Try a simpler test
        print("\n🔄 Trying simpler test with different keyword...")
        reddit_posts = await reddit_integration.get_toxic_posts_for_analysis(
            keyword="relationship", 
            limit=1
        )
        
        if "error" in reddit_posts:
            print(f"❌ Still failing: {reddit_posts['error']}")
            return
    
    if "message" in reddit_posts:
        print(f"ℹ️ {reddit_posts['message']}")
        if "raw_data" in reddit_posts:
            print(f"📋 Raw data: {reddit_posts['raw_data']}")
        return
    
    print(f"✅ Found {reddit_posts['total_posts']} toxic posts")
    
    # Step 2: Send to Dedalus for Gemini analysis
    for i, post in enumerate(reddit_posts["posts"]):
        print(f"\n📊 Analyzing post {i+1}: {post['title'][:50]}...")
        
        # Create analysis prompt for Gemini
        analysis_prompt = f"""
        Analyze this Reddit post for toxic behavior and communication patterns:

        TITLE: {post['title']}
        CONTENT: {post['content'][:500]}
        SUBREDDIT: r/{post['subreddit']}
        URL: {post['url']}

        Please provide a toxicity analysis with:
        1. Toxicity Level (Low/Medium/High/None)
        2. Main communication issues detected
        3. Specific examples of problematic communication
        4. Suggestions for healthier communication

        Focus on communication patterns and provide constructive feedback.
        """
        
        try:
            # Send to Dedalus (which will use your Gemini agent)
            print("🤖 Sending to Gemini for analysis...")
            response = await runner.run(
                input=analysis_prompt,
                model="google/gemini-2.0-flash-exp",
                # Remove mcp_servers for now to test basic functionality
            )
            
            # print(f"🎯 Analysis Result:")
            # print(f"   {response.final_output}")
            
            analysis_sender = AnalysisSender()

            # After getting analysis from Gemini, send to extension:
            extension_data = {
                "post_title": post["title"],
                "toxicity_level": "Medium",  # Extract this from Gemini response
                "analysis_summary": response.final_output,
                "url": post["url"],
                "subreddit": post["subreddit"]
            }
            await analysis_sender.send_to_extension(extension_data)
                        
        except Exception as e:
            print(f"❌ Analysis failed for post {i+1}: {str(e)}")

async def simple_test():
    """Simple test to verify Reddit server is working"""
    print("🧪 Running simple Reddit server test...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Reddit server health: {health_data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
            
            # Test search endpoint
            async with session.post(
                "http://localhost:8000/search_toxic_posts",
                json={"keyword": "test", "limit": 1}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Search test - keys: {list(data.keys())}")
                    print(f"   Total results: {data.get('total_results', 0)}")
                else:
                    print(f"❌ Search test failed: {response.status}")
                    
    except Exception as e:
        print(f"❌ Server test failed: {e}")

if __name__ == "__main__":
    # First test if server is working
    asyncio.run(simple_test())
    
    print("\n" + "="*50)
    
    # Then run main analysis
    asyncio.run(analyze_toxic_reddit_posts())