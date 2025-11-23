import os
import re
import fnmatch
import difflib
import shutil
from typing import List, Optional, Literal, Set
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult

# --- Shared State ---
global_read_files_tracker: Set[str] = set()

def validate_read_before_edit(file_path: str) -> bool:
    return os.path.abspath(file_path) in global_read_files_tracker

def get_read_before_edit_error(file_path: str) -> str:
    return f"File must be read before editing. Use read_file tool first: {file_path}"

# --- Schemas ---

class ReadFileParams(BaseModel):
    file_path: str = Field(..., description='Path to file.')
    start_line: Optional[int] = Field(None, description='Starting line number (1-indexed, optional)', ge=1)
    end_line: Optional[int] = Field(None, description='Ending line number (1-indexed, optional)', ge=1)

class CreateFileParams(BaseModel):
    file_path: str = Field(..., description='Path for new file/directory.')
    content: str = Field(..., description='File content (use empty string "" for directories)')
    file_type: Literal['file', 'directory'] = Field('file', description='Create file or directory')
    overwrite: bool = Field(False, description='Overwrite existing file')

class EditFileParams(BaseModel):
    file_path: str = Field(..., description='Path to file to edit.')
    old_text: str = Field(..., description='Exact text to replace.')
    new_text: str = Field(..., description='Replacement text.')
    replace_all: bool = Field(False, description='Replace all occurrences.')

class DeleteFileParams(BaseModel):
    file_path: str = Field(..., description='Path to file/directory to delete.')
    recursive: bool = Field(False, description='Delete directories and their contents.')

class ListFilesParams(BaseModel):
    directory: str = Field('.', description='Directory path to list.')
    pattern: str = Field('*', description='File pattern filter.')
    recursive: bool = Field(False, description='List subdirectories recursively.')
    show_hidden: bool = Field(False, description='Include hidden files.')

class SearchFilesParams(BaseModel):
    pattern: str = Field(..., description='Text to search for.')
    file_pattern: str = Field('*', description='File pattern filter (e.g., "*.py").')
    directory: str = Field('.', description='Directory to search in.')
    case_sensitive: bool = Field(False, description='Case-sensitive search.')
    pattern_type: Literal['substring', 'regex', 'exact', 'fuzzy'] = Field('substring', description='Match type.')
    file_types: Optional[List[str]] = Field(None, description='File extensions to include.')
    exclude_dirs: Optional[List[str]] = Field(None, description='Directories to skip.')
    exclude_files: Optional[List[str]] = Field(None, description='File patterns to skip.')
    max_results: int = Field(100, description='Maximum results to return (1-1000)', ge=1, le=1000)
    context_lines: int = Field(0, description='Lines of context around matches (0-10)', ge=0, le=10)
    group_by_file: bool = Field(False, description='Group results by filename.')

class FastGrepParams(BaseModel):
    keyword: str = Field(..., description='The keyword or regex pattern to search for.')
    directory: str = Field('.', description='The directory to search in.')
    file_pattern: Optional[str] = Field(None, description='Glob pattern to filter files to be searched (e.g., "*.py", "**/*.js").')

# --- Tools ---

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read file contents with optional line range. REQUIRED before edit_file."
    args_schema = ReadFileParams

    def run(self, file_path: str, start_line: int = None, end_line: int = None) -> ToolResult:
        try:
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                return ToolResult(success=False, error="File not found")
            if not os.path.isfile(abs_path):
                return ToolResult(success=False, error="Path is not a file")
            if os.path.getsize(abs_path) > 50 * 1024 * 1024: # 50MB limit
                return ToolResult(success=False, error="File too large (max 50MB)")

            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            global_read_files_tracker.add(abs_path)
            lines = content.splitlines()

            if start_line is not None:
                start_idx = max(0, start_line - 1)
                end_idx = len(lines) if end_line is None else min(len(lines), end_line)
                if start_idx >= len(lines):
                    return ToolResult(success=False, error="Start line exceeds file length")
                
                selected_content = "\n".join(lines[start_idx:end_idx])
                return ToolResult(success=True, content=selected_content)
            else:
                return ToolResult(success=True, content=content)

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to read file: {e}")

class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create NEW files or directories. Check if file exists first."
    args_schema = CreateFileParams

    def run(self, file_path: str, content: str, file_type: str = 'file', overwrite: bool = False) -> ToolResult:
        try:
            abs_path = os.path.abspath(file_path)
            if os.path.exists(abs_path) and not overwrite:
                return ToolResult(success=False, error="File already exists. Use overwrite=true to replace.")

            if file_type == 'directory':
                os.makedirs(abs_path, exist_ok=True)
                return ToolResult(success=True, content=f"Directory created: {file_path}")
            elif file_type == 'file':
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return ToolResult(success=True, content=f"File created: {file_path}")
            else:
                return ToolResult(success=False, error="Invalid file_type. Must be 'file' or 'directory'.")

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create file/directory: {e}")

class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Modify EXISTING files by exact text replacement. Always read_file first."
    args_schema = EditFileParams

    def run(self, file_path: str, old_text: str, new_text: str, replace_all: bool = False) -> ToolResult:
        if not validate_read_before_edit(file_path):
            return ToolResult(success=False, error=get_read_before_edit_error(file_path))
        try:
            abs_path = os.path.abspath(file_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            if old_text not in original_content:
                return ToolResult(success=False, error="old_text not found in file.")

            if replace_all:
                updated_content = original_content.replace(old_text, new_text)
            else:
                updated_content = original_content.replace(old_text, new_text, 1)
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return ToolResult(success=True, content=f"Successfully edited file: {file_path}")

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to edit file: {e}")

class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Remove files or directories. Use with caution."
    args_schema = DeleteFileParams

    def run(self, file_path: str, recursive: bool = False) -> ToolResult:
        try:
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                return ToolResult(success=False, error="Path not found.")

            if os.path.isdir(abs_path):
                if recursive:
                    shutil.rmtree(abs_path)
                    return ToolResult(success=True, content=f"Recursively deleted directory: {file_path}")
                else:
                    if os.listdir(abs_path):
                        return ToolResult(success=False, error="Directory is not empty. Use recursive=true to delete.")
                    os.rmdir(abs_path)
                    return ToolResult(success=True, content=f"Deleted empty directory: {file_path}")
            else:
                os.remove(abs_path)
                return ToolResult(success=True, content=f"Deleted file: {file_path}")

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to delete: {e}")

class ListFilesTool(BaseTool):
    name = "list_files"
    description = "Browse directory contents and file structure."
    args_schema = ListFilesParams

    def run(self, directory: str = '.', pattern: str = '*.*', recursive: bool = False, show_hidden: bool = False) -> ToolResult:
        try:
            abs_path = os.path.abspath(directory)
            if not os.path.isdir(abs_path):
                return ToolResult(success=False, error="Directory not found.")

            file_list = []
            if recursive:
                for root, dirs, files in os.walk(abs_path):
                    if not show_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]
                    
                    for file in files:
                        if re.match(pattern.replace('*.*', '.*').replace('*', '.*'), file):
                            file_list.append(os.path.join(root, file))
            else:
                for item in os.listdir(abs_path):
                    if not show_hidden and item.startswith('.'):
                        continue
                    if re.match(pattern.replace('*.*', '.*').replace('*', '.*'), item):
                        file_list.append(os.path.join(abs_path, item))

            return ToolResult(success=True, content=file_list)

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to list files: {e}")

class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Find text patterns in files across the codebase."
    args_schema = SearchFilesParams

    def run(self, pattern: str, file_pattern: str = '*', directory: str = '.', case_sensitive: bool = False,
            pattern_type: str = 'substring', file_types: Optional[List[str]] = None,
            exclude_dirs: Optional[List[str]] = None, exclude_files: Optional[List[str]] = None,
            max_results: int = 100, context_lines: int = 0, group_by_file: bool = False) -> ToolResult:
        try:
            results = []
            abs_dir = os.path.abspath(directory)
            if not os.path.isdir(abs_dir):
                return ToolResult(success=False, error="Directory not found.")
            
            if pattern_type == 'regex':
                regex = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
            
            for root, dirs, files in os.walk(abs_dir):
                if exclude_dirs:
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                for file in files:
                    if exclude_files and any(fnmatch.fnmatch(file, pat) for pat in exclude_files):
                        continue
                    if not fnmatch.fnmatch(file, file_pattern):
                        continue
                    if file_types:
                        ext = os.path.splitext(file)[1].lstrip('.')
                        if ext not in file_types:
                            continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                    except Exception:
                        continue
                    
                    for idx, line in enumerate(lines, start=1):
                        matched = False
                        match_text = None
                        if pattern_type == 'substring':
                            if (line.find(pattern) != -1) if case_sensitive else (pattern.lower() in line.lower()):
                                matched = True
                                match_text = pattern
                        elif pattern_type == 'exact':
                            if (line.strip() == pattern) if case_sensitive else (line.strip().lower() == pattern.lower()):
                                matched = True
                                match_text = pattern
                        elif pattern_type == 'regex':
                            if regex.search(line):
                                matched = True
                                match_text = regex.search(line).group(0)
                        elif pattern_type == 'fuzzy':
                            ratio = difflib.SequenceMatcher(None, pattern, line.strip()).ratio()
                            if ratio > 0.8:
                                matched = True
                                match_text = line.strip()
                        
                        if matched:
                            start = max(0, idx - context_lines - 1)
                            end = min(len(lines), idx + context_lines)
                            context = ''.join(lines[start:end]).strip()
                            res = {
                                'file': file_path,
                                'line': idx,
                                'match': match_text,
                                'context': context
                            }
                            results.append(res)
                            if len(results) >= max_results:
                                break
                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break
            
            if group_by_file:
                grouped = {}
                for r in results:
                    grouped.setdefault(r['file'], []).append(r)
                content = grouped
            else:
                content = results
            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to search files: {e}")

class FastGrepTool(BaseTool):
    name = "fast_grep"
    description = "Search for a keyword or regex pattern in a directory. This is an alias for the search_files tool."
    args_schema = FastGrepParams

    def run(self, keyword: str, directory: str = '.', file_pattern: Optional[str] = None) -> ToolResult:
        search_tool = SearchFilesTool()
        return search_tool.run(pattern=keyword, directory=directory, file_pattern=file_pattern or '*')
