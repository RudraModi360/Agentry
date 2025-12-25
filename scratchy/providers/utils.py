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
                elif part_type == "image":
                    b64_data = part.get("data")
                    if b64_data:
                        # Assume png if not specified, or we could detect from b64
                        try:
                            # if it has the data prefix, parse it
                            if isinstance(b64_data, str) and b64_data.startswith('data:'):
                                mime_type, raw_data = parse_image_url(b64_data)
                            else:
                                mime_type = "image/png"
                                raw_data = base64.b64decode(b64_data)
                            
                            images.append({
                                "url": None,
                                "mime_type": mime_type,
                                "data": raw_data
                            })
                        except Exception:
                            pass
        return " ".join(text_parts), images
        
    return "", []

def parse_image_url(url: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Parses a data URL.
    Returns (mime_type, image_bytes).
    """
    if not isinstance(url, str):
        return None, None
        
    # Check for data URI scheme
    # More lenient regex to handle common variations
    match = re.search(r"data:(image/[a-zA-Z0-9+.-]+);base64,(.+)", url, re.DOTALL)
    if match:
        mime_type = match.group(1)
        b64_data = match.group(2).strip()
        try:
            return mime_type, base64.b64decode(b64_data)
        except Exception:
            return mime_type, None
            
    # Fallback for raw base64 that might have been passed without prefix
    # but still looks like a data URL or just base64
    if url.startswith('data:'):
        # Try to extract at least the mime type if regex failed
        parts = url.split(',', 1)
        if len(parts) == 2:
            mime_part = parts[0]
            data_part = parts[1].strip()
            mime_match = re.search(r"image/[a-zA-Z0-9+.-]+", mime_part)
            mime_type = mime_match.group(0) if mime_match else "image/png"
            try:
                return mime_type, base64.b64decode(data_part)
            except Exception:
                return mime_type, None

    return None, None

def simplify_tool_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplifies a complex JSON schema (e.g. from Pydantic v2) for models that 
    have limited support for JSON Schema features like anyOf, oneOf, or $ref.
    Specifically targets Ollama's tool calling requirements.
    """
    if "function" not in schema:
        return schema
    
    new_schema = schema.copy()
    new_func = new_schema["function"].copy()
    
    if "parameters" in new_func:
        params = new_func["parameters"].copy()
        if "properties" in params:
            new_properties = {}
            for param_name, param_info in params["properties"].items():
                new_info = _simplify_property(param_info)
                new_properties[param_name] = new_info
            params["properties"] = new_properties
        
        # Remove top-level things Ollama might not like
        params.pop("title", None)
        params.pop("description", None) # Task already has description in function level
        
        new_func["parameters"] = params
    
    new_schema["function"] = new_func
    return new_schema

def _simplify_property(info: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to simplify a single property's schema."""
    if not isinstance(info, dict):
        return info
    
    result = info.copy()
    
    # Handle anyOf/oneOf (usually from Optional or Union)
    if "anyOf" in result or "oneOf" in result:
        options = result.get("anyOf") or result.get("oneOf")
        # Find the first non-null type
        non_null_options = [opt for opt in options if isinstance(opt, dict) and opt.get("type") != "null"]
        if non_null_options:
            base_option = non_null_options[0].copy()
            # Merge common fields (description, title) from the top level into the branch if they were there
            for key in ["description", "title", "default"]:
                if key in result and key not in base_option:
                    base_option[key] = result[key]
            result = base_option
        else:
            # Fallback to the first option if all are null? Should not happen.
            result = options[0].copy()
    
    # Remove complex validators that might confuse simple parsers
    # but keep basic types
    result.pop("title", None)
    
    # Ensure type is present and is a string (not a list)
    if "type" in result and isinstance(result["type"], list):
        # If it's a list, take the first non-null type
        types = [t for t in result["type"] if t != "null"]
        if types:
            result["type"] = types[0]
        else:
            result["type"] = result["type"][0]

    # Recursive simplification for nested objects
    if result.get("type") == "object" and "properties" in result:
        new_props = {}
        for k, v in result["properties"].items():
            new_props[k] = _simplify_property(v)
        result["properties"] = new_props
    
    # Recursive for arrays
    if result.get("type") == "array" and "items" in result:
        result["items"] = _simplify_property(result["items"])

    return result
