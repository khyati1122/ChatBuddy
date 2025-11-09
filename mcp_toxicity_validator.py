#!/usr/bin/env python3
"""
MCP Server for Toxicity Validation Pipeline
Dynamically analyzes chat toxicity and validates with Reddit human opinions
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp
import re
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("toxicity_validator")

class ToxicityLevel(Enum):
    """Toxicity level classification"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ChatAnalysis:
    """Container for chat analysis results"""
    conversation: str
    toxicity_level: ToxicityLevel
    toxic_person: str
    flagged_phrases: List[str]
    behaviors: List[str]
    confidence: float

@dataclass
class RedditValidation:
    """Container for Reddit validation results"""
    subreddit: str
    relevance_score: float
    similar_posts: List[Dict[str, Any]]
    human_consensus: Optional[str]
    validation_score: float

class ToxicityValidatorMCPServer:
    """
    MCP Server that:
    1. Analyzes chat data for toxicity and extracts keywords
    2. Crawls Reddit for relevant subreddits based on those keywords
    3. Validates AI toxicity analysis with human opinions from Reddit
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.llm_client = None  # Will be configured based on your LLM provider
        
    async def initialize(self):
        """Initialize the MCP server and HTTP session"""
        self.session = aiohttp.ClientSession()
        logger.info("Toxicity Validator MCP Server initialized")
    
    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        logger.info("Toxicity Validator MCP Server shutdown")
    
    async def call_llm(self, prompt: str, system_message: str = None) -> str:
        """
        Dynamic LLM caller - adapts to your LLM provider
        This should be configured based on your specific LLM API (OpenAI, Anthropic, etc.)
        """
        try:
            # TODO: Configure based on your LLM provider
            # Example for OpenAI-style API:
            # async with self.session.post(
            #     "https://api.openai.com/v1/chat/completions",
            #     headers={"Authorization": f"Bearer {API_KEY}"},
            #     json={
            #         "model": "gpt-4",
            #         "messages": [
            #             {"role": "system", "content": system_message or "You are a toxicity analysis expert."},
            #             {"role": "user", "content": prompt}
            #         ],
            #         "temperature": 0.1
            #     }
            # ) as response:
            #     result = await response.json()
            #     return result["choices"][0]["message"]["content"]
            
            # Placeholder - replace with actual LLM call
            logger.info(f"LLM called with prompt: {prompt[:100]}...")
            return "Mock LLM response - configure with your LLM provider"
            
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise
    
    async def analyze_chat_toxicity(self, chat_data: str) -> ChatAnalysis:
        """
        Step 1: Analyze chat conversation for toxicity and extract keywords
        Uses LLM to identify toxic patterns and extract relevant phrases
        """
        try:
            prompt = f"""
            Analyze the following chat conversation for toxic behavior and extract key phrases.
            
            CHAT CONVERSATION:
            {chat_data}
            
            Provide analysis in this exact JSON format:
            {{
                "toxicity_level": "none|low|medium|high",
                "toxic_person": "Person A|Person B|Both|None",
                "flagged_phrases": ["list", "of", "toxic", "phrases"],
                "behaviors": ["list", "of", "toxic", "behaviors"],
                "confidence": 0.95
            }}
            
            Focus on:
            - Personal attacks, insults, harassment
            - Aggressive language, threats
            - Passive-aggressive behavior
            - Manipulative language
            - Exclusionary language
            """
            
            response = await self.call_llm(prompt, "You are an expert in communication analysis and toxicity detection.")
            
            # Parse LLM response
            analysis_data = self._parse_llm_json_response(response)
            
            return ChatAnalysis(
                conversation=chat_data,
                toxicity_level=ToxicityLevel(analysis_data.get("toxicity_level", "none")),
                toxic_person=analysis_data.get("toxic_person", "None"),
                flagged_phrases=analysis_data.get("flagged_phrases", []),
                behaviors=analysis_data.get("behaviors", []),
                confidence=analysis_data.get("confidence", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Chat toxicity analysis failed: {str(e)}")
            raise
    
    async def find_relevant_subreddits(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Step 2: Dynamically find Reddit subreddits relevant to the toxicity keywords
        Uses Reddit API to search for communities discussing similar issues
        """
        try:
            subreddits = []
            
            for keyword in keywords[:5]:  # Limit to top 5 keywords to avoid rate limiting
                try:
                    # Search Reddit for subreddits related to the toxicity keyword
                    search_url = f"https://www.reddit.com/subreddits/search.json?q={quote(keyword)}&limit=5"
                    
                    async with self.session.get(search_url, headers={"User-Agent": "ToxicityValidator/1.0"}) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for subreddit in data.get("data", {}).get("children", []):
                                sub_data = subreddit["data"]
                                subreddit_info = {
                                    "name": sub_data["display_name"],
                                    "title": sub_data.get("title", ""),
                                    "description": sub_data.get("public_description", ""),
                                    "subscribers": sub_data.get("subscribers", 0),
                                    "url": f"https://reddit.com{sub_data['url']}",
                                    "relevance_keyword": keyword,
                                    "relevance_score": self._calculate_relevance_score(sub_data, keyword)
                                }
                                
                                # Only include subreddits with sufficient relevance
                                if subreddit_info["relevance_score"] > 0.3:
                                    subreddits.append(subreddit_info)
                            
                            await asyncio.sleep(1)  # Rate limiting
                            
                except Exception as e:
                    logger.warning(f"Failed to search for keyword '{keyword}': {str(e)}")
                    continue
            
            # Deduplicate and sort by relevance
            unique_subs = {sub["name"]: sub for sub in subreddits}.values()
            sorted_subs = sorted(unique_subs, key=lambda x: x["relevance_score"], reverse=True)
            
            return sorted_subs[:limit]
            
        except Exception as e:
            logger.error(f"Subreddit search failed: {str(e)}")
            return []
    
    def _calculate_relevance_score(self, subreddit_data: Dict[str, Any], keyword: str) -> float:
        """Calculate how relevant a subreddit is to the toxicity keyword"""
        score = 0.0
        
        # Check title
        title = subreddit_data.get("title", "").lower()
        if keyword.lower() in title:
            score += 0.4
        
        # Check description
        description = subreddit_data.get("public_description", "").lower()
        if keyword.lower() in description:
            score += 0.3
        
        # Check display name
        display_name = subreddit_data.get("display_name", "").lower()
        if keyword.lower() in display_name:
            score += 0.3
        
        # Boost score for relationship/communication focused subreddits
        relationship_terms = ["relationship", "advice", "communication", "social", "interpersonal"]
        if any(term in description for term in relationship_terms):
            score += 0.2
        
        return min(score, 1.0)
    
    async def validate_with_reddit_posts(self, chat_analysis: ChatAnalysis, subreddits: List[Dict[str, Any]]) -> List[RedditValidation]:
        """
        Step 3: Validate toxicity analysis by examining similar discussions on Reddit
        Checks if human communities agree with the AI's toxicity assessment
        """
        validation_results = []
        
        for subreddit in subreddits[:3]:  # Limit to top 3 most relevant subreddits
            try:
                # Search for posts in this subreddit related to our toxicity themes
                search_terms = chat_analysis.flagged_phrases + chat_analysis.behaviors
                posts = await self._search_subreddit_posts(subreddit["name"], search_terms)
                
                if posts:
                    # Analyze posts to get human consensus
                    human_consensus = await self._analyze_reddit_sentiment(posts, chat_analysis)
                    validation_score = self._calculate_validation_score(human_consensus, chat_analysis)
                    
                    validation_results.append(RedditValidation(
                        subreddit=subreddit["name"],
                        relevance_score=subreddit["relevance_score"],
                        similar_posts=posts,
                        human_consensus=human_consensus,
                        validation_score=validation_score
                    ))
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Validation failed for subreddit {subreddit['name']}: {str(e)}")
                continue
        
        return validation_results
    
    async def _search_subreddit_posts(self, subreddit: str, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search for relevant posts in a subreddit"""
        posts = []
        
        for term in search_terms[:3]:  # Use top 3 most significant terms
            try:
                search_url = f"https://www.reddit.com/r/{subreddit}/search.json?q={quote(term)}&restrict_sr=1&limit=5"
                
                async with self.session.get(search_url, headers={"User-Agent": "ToxicityValidator/1.0"}) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for post in data.get("data", {}).get("children", []):
                            post_data = post["data"]
                            posts.append({
                                "title": post_data.get("title", ""),
                                "content": post_data.get("selftext", ""),
                                "upvotes": post_data.get("ups", 0),
                                "comments": post_data.get("num_comments", 0),
                                "url": f"https://reddit.com{post_data['permalink']}",
                                "created_utc": post_data.get("created_utc", 0),
                                "search_term": term
                            })
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Post search failed for term '{term}': {str(e)}")
                continue
        
        return posts[:10]  # Return top 10 posts
    
    async def _analyze_reddit_sentiment(self, posts: List[Dict[str, Any]], chat_analysis: ChatAnalysis) -> str:
        """Use LLM to analyze Reddit posts and determine human consensus on similar toxicity"""
        try:
            posts_summary = "\n".join([
                f"Post: {post['title']}\nContent: {post['content'][:200]}...\nUpvotes: {post['upvotes']}\nComments: {post['comments']}"
                for post in posts[:5]  # Analyze top 5 posts
            ])
            
            prompt = f"""
            Based on these Reddit posts about similar communication issues, what is the general human consensus?
            
            ORIGINAL TOXICITY ANALYSIS:
            - Level: {chat_analysis.toxicity_level.value}
            - Behaviors: {', '.join(chat_analysis.behaviors)}
            - Flagged Phrases: {', '.join(chat_analysis.flagged_phrases)}
            
            REDDIT POSTS:
            {posts_summary}
            
            Determine if the human consensus from these Reddit discussions:
            1. Supports the toxicity analysis
            2. Partially supports it
            3. Contradicts it
            4. Is inconclusive
            
            Provide a brief summary of the human perspective.
            """
            
            consensus = await self.call_llm(prompt, "You analyze community consensus on social behavior issues.")
            return consensus
            
        except Exception as e:
            logger.error(f"Reddit sentiment analysis failed: {str(e)}")
            return "Analysis unavailable"
    
    def _calculate_validation_score(self, human_consensus: str, chat_analysis: ChatAnalysis) -> float:
        """Calculate how well Reddit human consensus validates our AI analysis"""
        consensus_lower = human_consensus.lower()
        
        # Simple heuristic scoring - can be enhanced with more sophisticated NLP
        if "support" in consensus_lower and "contradict" not in consensus_lower:
            return 0.8  # Strong support
        elif "partially" in consensus_lower:
            return 0.5  # Partial support
        elif "contradict" in consensus_lower:
            return 0.2  # Contradiction
        elif "inconclusive" in consensus_lower:
            return 0.3  # Inconclusive
        else:
            return 0.4  # Neutral/unknown
    
    def _parse_llm_json_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, handling various formats"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to simple parsing
                logger.warning("Could not parse JSON from LLM response, using fallback")
                return {
                    "toxicity_level": "none",
                    "toxic_person": "None",
                    "flagged_phrases": [],
                    "behaviors": [],
                    "confidence": 0.0
                }
        except Exception as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            return {
                "toxicity_level": "none",
                "toxic_person": "None", 
                "flagged_phrases": [],
                "behaviors": [],
                "confidence": 0.0
            }
    
    async def process_toxicity_validation(self, chat_data: str) -> Dict[str, Any]:
        """
        Main MCP endpoint: Complete toxicity validation pipeline
        This is the primary method that Dedalus Lab will call
        """
        logger.info("Starting toxicity validation pipeline")
        
        try:
            # Step 1: Analyze chat toxicity
            logger.info("Step 1: Analyzing chat toxicity")
            chat_analysis = await self.analyze_chat_toxicity(chat_data)
            
            # Step 2: Find relevant subreddits based on toxicity keywords
            logger.info("Step 2: Finding relevant subreddits")
            keywords = chat_analysis.flagged_phrases + chat_analysis.behaviors
            relevant_subreddits = await self.find_relevant_subreddits(keywords)
            
            # Step 3: Validate with Reddit human opinions
            logger.info("Step 3: Validating with Reddit consensus")
            validation_results = await self.validate_with_reddit_posts(chat_analysis, relevant_subreddits)
            
            # Calculate overall validation confidence
            overall_validation = self._calculate_overall_validation(validation_results, chat_analysis)
            
            # Return comprehensive results
            return {
                "success": True,
                "chat_analysis": {
                    "toxicity_level": chat_analysis.toxicity_level.value,
                    "toxic_person": chat_analysis.toxic_person,
                    "flagged_phrases": chat_analysis.flagged_phrases,
                    "behaviors": chat_analysis.behaviors,
                    "confidence": chat_analysis.confidence
                },
                "reddit_validation": {
                    "relevant_subreddits_found": len(relevant_subreddits),
                    "validation_results": [
                        {
                            "subreddit": result.subreddit,
                            "relevance_score": result.relevance_score,
                            "human_consensus": result.human_consensus,
                            "validation_score": result.validation_score,
                            "sample_posts": len(result.similar_posts)
                        }
                        for result in validation_results
                    ],
                    "overall_validation_score": overall_validation,
                    "is_validated": overall_validation > 0.5
                },
                "metadata": {
                    "total_processing_time": "N/A",  # Would track actual time in production
                    "subreddits_analyzed": len(validation_results),
                    "posts_considered": sum(len(result.similar_posts) for result in validation_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Toxicity validation pipeline failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "chat_analysis": None,
                "reddit_validation": None
            }
    
    def _calculate_overall_validation(self, validation_results: List[RedditValidation], chat_analysis: ChatAnalysis) -> float:
        """Calculate overall validation score across all subreddits"""
        if not validation_results:
            return 0.0
        
        # Weight by relevance score and number of posts
        total_weight = 0
        weighted_score = 0
        
        for result in validation_results:
            weight = result.relevance_score * (1 + len(result.similar_posts) * 0.1)
            weighted_score += result.validation_score * weight
            total_weight += weight
        
        if total_weight > 0:
            base_score = weighted_score / total_weight
        else:
            base_score = 0.5  # Neutral default
        
        # Adjust based on original confidence
        adjusted_score = (base_score * 0.7) + (chat_analysis.confidence * 0.3)
        
        return min(adjusted_score, 1.0)


# MCP Server Standard Interface
class ToxicityValidatorServer:
    """
    Standard MCP server interface for integration with Dedalus Lab
    Follows MCP (Model Context Protocol) standards
    """
    
    def __init__(self):
        self.validator = ToxicityValidatorMCPServer()
    
    async def start(self):
        """Start the MCP server"""
        await self.validator.initialize()
        logger.info("MCP Toxicity Validator Server started")
    
    async def stop(self):
        """Stop the MCP server"""
        await self.validator.close()
        logger.info("MCP Toxicity Validator Server stopped")
    
    async def validate_toxicity(self, chat_data: str) -> Dict[str, Any]:
        """
        Main MCP endpoint for toxicity validation
        This is what Dedalus Lab will call via MCP protocol
        """
        return await self.validator.process_toxicity_validation(chat_data)
    
    async def health_check(self) -> Dict[str, Any]:
        """MCP health check endpoint"""
        return {
            "status": "healthy",
            "service": "toxicity_validator",
            "version": "1.0.0"
        }


# Usage example for Dedalus Lab integration
async def main():
    """Example usage of the MCP server"""
    server = ToxicityValidatorServer()
    
    try:
        await server.start()
        
        # Example chat data from your extension
        example_chat = """
        Person A: You're always so lazy and never help with anything
        Person B: Maybe if you weren't so critical all the time, I'd want to help
        Person A: That's just an excuse for being useless
        Person B: I'm done with this conversation
        """
        
        # Process toxicity validation
        result = await server.validate_toxicity(example_chat)
        print("Validation Result:", json.dumps(result, indent=2))
        
        # Health check
        health = await server.health_check()
        print("Health:", health)
        
    finally:
        await server.stop()

if __name__ == "__main__":
    # Run example
    asyncio.run(main())