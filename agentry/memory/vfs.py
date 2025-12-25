from typing import Dict, Any, List, Optional
from .storage import PersistentMemoryStore

class VirtualFileSystem:
    """
    Manages the Virtual File System (VFS) for the agent.
    Acts as a persistent memory layer where the agent can read/write files.
    """
    def __init__(self, memory_store: PersistentMemoryStore):
        self.memory_store = memory_store

    def load_session_files(self, session_id: str) -> Dict[str, str]:
        """Load VFS state for a session from persistent storage."""
        files = self.memory_store.load_state(session_id, "vfs_files")
        return files if files else {}

    def save_session_files(self, session_id: str, files: Dict[str, str]):
        """Save VFS state for a session to persistent storage."""
        self.memory_store.save_state(session_id, "vfs_files", files)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns the schemas for VFS tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_virtual_file",
                    "description": "Write content to a file in the agent's persistent virtual file system. Use this to save notes, plans, or code.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path/filename (e.g., 'notes/plan.md')"},
                            "content": {"type": "string", "description": "The text content to write"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_virtual_file",
                    "description": "Read content from a file in the virtual file system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path/filename to read"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_virtual_files",
                    "description": "List all files in the virtual file system.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def execute_tool(self, session_files: Dict[str, str], session_id: str, name: str, args: Dict[str, Any]) -> str:
        """Executes a VFS tool."""
        if name == "write_virtual_file":
            return self._write_file(session_files, session_id, args.get("path"), args.get("content"))
        elif name == "read_virtual_file":
            return self._read_file(session_files, args.get("path"))
        elif name == "list_virtual_files":
            return self._list_files(session_files)
        else:
            raise ValueError(f"Unknown VFS tool: {name}")

    def _write_file(self, files: Dict[str, str], session_id: str, path: str, content: str) -> str:
        if not path or content is None:
            return "Error: 'path' and 'content' are required."
        
        files[path] = content
        self.save_session_files(session_id, files)
        return f"File '{path}' written successfully."

    def _read_file(self, files: Dict[str, str], path: str) -> str:
        # Exact match
        if path in files:
            return files[path]
            
        # Try normalizing path (remove leading ./ or /)
        norm_path = path.lstrip("./").lstrip("/")
        if norm_path in files:
            return files[norm_path]
            
        # Try case-insensitive match
        for f in files:
            if f.lower() == path.lower() or f.lower() == norm_path.lower():
                return files[f]
                
        return f"Error: File '{path}' not found in virtual file system. Available files: {', '.join(files.keys())}"

    def _list_files(self, files: Dict[str, str]) -> str:
        if not files:
            return "Virtual file system is empty."
        return "Files:\n" + "\n".join(f"- {f}" for f in files.keys())
