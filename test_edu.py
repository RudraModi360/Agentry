
import re

EDUCATIONAL_KEYWORDS = [
    # Science topics
    'water cycle', 'rain cycle', 'carbon cycle', 'nitrogen cycle', 'rock cycle', 'life cycle',
    'photosynthesis', 'respiration', 'digestion', 'cell division', 'mitosis', 'meiosis',
    'evolution', 'ecosystem', 'food chain', 'food web',
    # Anatomy
    'heart', 'lungs', 'brain', 'skeleton', 'nervous system', 'digestive system',
    'circulatory system', 'respiratory system', 'muscular system',
    # Physics
    'circuit', 'electricity', 'magnetism', 'force', 'motion', 'wave', 'light', 'sound',
    'gravity', 'energy', 'momentum',
    # Chemistry
    'periodic table', 'atom', 'molecule', 'chemical reaction', 'bond',
    # Geography
    'tectonic', 'volcano', 'earthquake', 'weather', 'climate', 'erosion', 'landform',
    # General educational triggers
    'explain', 'describe', 'how does', 'what is', 'diagram', 'process', 'steps of',
]

def detect_educational_query(message: str) -> tuple:
    if not message:
        return False, None
    
    message_lower = message.lower()
    
    # Check for educational keywords
    for keyword in EDUCATIONAL_KEYWORDS:
        if keyword in message_lower:
            if 'cycle' in keyword:
                return True, f"{keyword} diagram labeled"
            elif keyword in ['explain', 'describe', 'how does', 'what is']:
                import re
                patterns = [
                    r'explain\s+(?:the\s+)?(.+?)(?:\?|$)',
                    r'describe\s+(?:the\s+)?(.+?)(?:\?|$)',
                    r'how does\s+(?:the\s+)?(.+?)\s+work',
                    r'what is\s+(?:a\s+|an\s+|the\s+)?(.+?)(?:\?|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, message_lower, re.IGNORECASE)
                    if match:
                        topic = match.group(1).strip()
                        if len(topic) > 3 and len(topic) < 50:
                            return True, f"{topic} diagram"
                return False, None
            else:
                return True, f"{keyword} diagram"
    
    return False, None

prompt = "Explain the Rain cycle "
print(f"Prompt: '{prompt}'")
print(f"Result: {detect_educational_query(prompt)}")

prompt2 = "Tell me about the water cycle"
print(f"Prompt: '{prompt2}'")
print(f"Result: {detect_educational_query(prompt2)}")
