import os
import mimetypes
import base64
from typing import List, Dict, Union, Any
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

def pick_files() -> List[str]:
    """Opens a native file picker dialog."""
    if not TK_AVAILABLE:
        return []
    
    try:
        root = tk.Tk()
        root.withdraw() # Hide main window
        root.attributes('-topmost', True) # Bring to front
        
        file_paths = filedialog.askopenfilenames(
            title="Select files to upload",
            filetypes=[("All files", "*.*")]
        )
        
        root.destroy()
        return list(file_paths)
    except Exception as e:
        print(f"Error opening file picker: {e}")
        return []

def build_user_message(user_input: str, attachments: List[str] = None) -> Union[str, List[Dict[str, Any]]]:
    """
    Constructs a message payload from user input and optional file attachments.
    """
    attachments = attachments or []
    tokens = user_input.split()
    
    # Collect all potential file paths (explicit + implicit)
    potential_paths = list(attachments)
    for token in tokens:
        clean_token = token.strip('"').strip("'")
        if clean_token not in potential_paths:
            potential_paths.append(clean_token)
            
    processed_content: List[Dict[str, Any]] = []
    processed_paths = set()
    
    # Process files
    for path in potential_paths:
        if not os.path.exists(path) or not os.path.isfile(path):
            continue
            
        # Avoid processing the same file twice
        if path in processed_paths:
            continue
            
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        
        # 1. Document Handling (PDF, DOCX, PPTX, etc.)
        from agentry.document_handlers import get_handler, DocumentHandlerRegistry
        if ext in DocumentHandlerRegistry._handlers and ext not in ['.txt', '.md', '.py']:
            print(f"   ⏳ Processing document: {os.path.basename(path)}...", end='\r')
            try:
                handler = get_handler(path)
                md_content = handler.to_markdown()
                
                content_block = f"\n\n--- Document Attachment: {os.path.basename(path)} ---\n{md_content}\n-----------------------------------\n"
                processed_content.append({
                    "type": "text",
                    "text": content_block
                })
                print(f"   📄 Attached document: {path}")
                processed_paths.add(path)
                continue
            except Exception as e:
                print(f"   ⚠️  Failed to attach document {path}: {e}")

        # 2. Image Handling
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type and mime_type.startswith('image/'):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    b64_data = base64.b64encode(data).decode('utf-8')
                    data_uri = f"data:{mime_type};base64,{b64_data}"
                    
                    processed_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri
                        }
                    })
                    print(f"   🖼️  Attached image: {path}")
                    processed_paths.add(path)
            except Exception as e:
                print(f"   ⚠️  Failed to load image {path}: {e}")

    # If no attachments processed, just return text
    if not processed_content:
        return user_input
        
    final_message = []
    if user_input.strip():
        final_message.append({"type": "text", "text": user_input})
    
    final_message.extend(processed_content)
    
    return final_message
