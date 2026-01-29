"""
Media Orchestrator Service
Uses LLM to analyze user intent and orchestrate media searches (images/videos).
"""

import json
import asyncio
from typing import List, Dict, Any, Optional

from agentry.tools.media_search import media_search_tool

class MediaOrchestrator:
    """
    Intelligent layer that decides WHEN to show media and WHAT to show.
    Uses a lightweight LLM call to extract specific search queries.
    """
    
    SYSTEM_PROMPT = """You are a Media Search Coordinator.
Your job is to analyze the user's latest message and decide if it would benefit from visual aids (images or videos).

Output a JSON object with:
{
  "needs_media": boolean,      // True if the user asks for diagrams, videos, how-to, visual explanations, or specific entities.
  "query": string,             // A precise, short search query for the media (e.g., "RBF Kernel formula", "Rain cycle diagram").
  "media_types": ["image"] or ["video"] or ["image", "video"] // What types are relevant?
}

Rules:
1. "needs_media": true ONLY if visual content significantly aids understanding OR if explicitly requested (e.g., "show me", "video of").
2. "query": Strip filler words. Be specific.
3. "media_types": Include "video" if the user asks for a video, process explanation, or dynamic mechanism. Default to ["image"] for static concepts.
4. Response MUST be valid JSON only. No markdown formatting.
"""

    async def analyze_intent(self, message: str, provider: Any) -> Dict[str, Any]:
        """
        Analyze the message to see if media is needed.
        """
        if not message or len(message) < 3:
            return {"needs_media": False}
            
        try:
            print(f"[MediaOrchestrator] Analyzing intent for: {message[:100]}...")
            # Construct messages for the LLM
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"User Message: \"{message}\"\nAnalyze intent:"}
            ]
            
            # Call the provider (assuming standard chat interface)
            response = await provider.chat(messages)
            
            content = ""
            if isinstance(response, dict):
                content = response.get("content", "")
            elif hasattr(response, "content"):
                content = response.content
            else:
                content = str(response)
                
            # Clean up potential markdown blocks
            content = content.replace("```json", "").replace("```", "").strip()
            print(f"[MediaOrchestrator] Raw intent response: {content}")
            
            intent = json.loads(content)
            return intent
            
        except Exception as e:
            print(f"[MediaOrchestrator] Intent analysis failed: {e}")
            return {"needs_media": False}

    async def search_media(self, query: str, media_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Execute the search based on the intent.
        Returns a structured list of media items.
        """
        print(f"[MediaOrchestrator] Searching for '{query}' types: {media_types}")
        if not media_types:
            media_types = ["image"]
            
        media_mode = "both"
        if "image" in media_types and "video" not in media_types:
            media_mode = "image"
        elif "video" in media_types and "image" not in media_types:
            media_mode = "video"
            
        try:
            loop = asyncio.get_event_loop()
            
            # Helper wrapper for sync search
            def _do_search():
                results = []
                if media_mode in ["image", "both"]:
                    # Fetch images
                    imgs = media_search_tool._search_images(query, num_results=4)
                    print(f"[MediaOrchestrator] Found {len(imgs)} images")
                    results.extend(imgs)
                    
                if media_mode in ["video", "both"]:
                    # Fetch videos
                    vids = media_search_tool._search_youtube(query, num_results=2)
                    print(f"[MediaOrchestrator] Found {len(vids)} videos")
                    results.extend(vids)
                return results

            results = await loop.run_in_executor(None, _do_search)
            return results
            
        except Exception as e:
            print(f"[MediaOrchestrator] Search execution failed: {e}")
            return []

# Singleton instance
media_orchestrator = MediaOrchestrator()
