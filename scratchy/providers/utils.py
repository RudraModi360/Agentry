import base64
import re
from typing import List, Dict, Any, Tuple, Optional

def extract_content(message_content: Any) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts text and images from a message content.
    Returns (text_content, list_of_image_info).
    
    image_info structure:
    {
        "url": str, # Original URL/Data URI
        "mime_type": str (optional),
        "data": bytes (optional)
    }
    """
    if isinstance(message_content, str):
        return message_content, []
    
    if isinstance(message_content, list):
        text_parts = []
        images = []
        for part in message_content:
            if isinstance(part, dict):
                part_type = part.get("type")
                if part_type == "text":
                    text_parts.append(part.get("text", ""))
                elif part_type == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if url:
                        mime_type, data = parse_image_url(url)
                        images.append({
                            "url": url,
                            "mime_type": mime_type,
                            "data": data
                        })
        return " ".join(text_parts), images
        
    return "", []

def parse_image_url(url: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Parses a data URL.
    Returns (mime_type, image_bytes).
    """
    # Check for data URI scheme
    match = re.match(r"data:(image/[a-zA-Z0-9+.-]+);base64,(.+)", url)
    if match:
        mime_type = match.group(1)
        b64_data = match.group(2)
        try:
            return mime_type, base64.b64decode(b64_data)
        except Exception:
            return mime_type, None
            
    # If standard URL, we can't easily get bytes without downloading, 
    # but the providers might handle URLs.
    # For this specific task, we assume the user provides data URIs or we return None for data.
    return None, None
