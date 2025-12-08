import os
import re
import fnmatch
import difflib
import shutil
from typing import List, Optional, Literal, Set, Union
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
    file_types: Optional[Union[str, List[str]]] = Field(None, description='File extensions to include (list or comma-separated string).')
    exclude_dirs: Optional[Union[str, List[str]]] = Field(None, description='Directories to skip (list or comma-separated string).')
    exclude_files: Optional[Union[str, List[str]]] = Field(None, description='File patterns to skip (list or comma-separated string).')
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
            pattern_type: str = 'substring', file_types: Optional[Union[str, List[str]]] = None,
            exclude_dirs: Optional[Union[str, List[str]]] = None, exclude_files: Optional[Union[str, List[str]]] = None,
            max_results: int = 100, context_lines: int = 0, group_by_file: bool = False) -> ToolResult:
        try:
            from pathlib import Path
            import re, fnmatch, os
            from collections import deque

            base_dir = Path(directory).resolve()
            if not base_dir.is_dir():
                return ToolResult(success=False, error="Directory not found.")

            # Normalizers
            def _norm(v):
                if v is None:
                    return []
                if isinstance(v, str):
                    return [x.strip() for x in v.split(',')]
                return list(v)

            excludes = set(_norm(exclude_dirs) + ['.git','__pycache__','node_modules','venv','.env','.idea','.vscode'])
            file_excludes = set(_norm(exclude_files))
            ftypes = set(v.lower().lstrip('.') for v in _norm(file_types)) if file_types else None

            if pattern_type == 'regex':
                try:
                    regex = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
                except re.error as e:
                    return ToolResult(success=False, error=f"Invalid regex: {e}")
            else:
                regex = None

            pat_cmp = pattern.lower() if not case_sensitive else pattern
            results, grouped = [], {} if group_by_file else None
            found = 0

            for root, dirs, files in os.walk(base_dir, topdown=True):
                dirs[:] = [d for d in dirs if d not in excludes]
                for f in files:
                    if found >= max_results:
                        break
                    if file_excludes and any(fnmatch.fnmatch(f, p) for p in file_excludes):
                        continue
                    if ftypes and f.rsplit('.',1)[-1].lower() not in ftypes:
                        continue
                    if file_pattern != '*' and not fnmatch.fnmatch(f, file_pattern):
                        continue

                    fp = os.path.join(root, f)
                    try:
                        stat = os.stat(fp)
                        if stat.st_size > 10*1024*1024:
                            continue
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                            if context_lines:
                                lines = fh.readlines()
                                iter_lines = enumerate(lines, start=1)
                                use_buf = True
                            else:
                                iter_lines = enumerate(fh, start=1)
                                use_buf = False
                            for ln_num, line in iter_lines:
                                txt = line.rstrip('\n')
                                matched = False
                                if pattern_type == 'substring':
                                    matched = (pattern in txt) if case_sensitive else (pat_cmp in txt.lower())
                                elif pattern_type == 'regex':
                                    matched = bool(regex.search(txt))
                                elif pattern_type == 'exact':
                                    matched = (txt.strip() == pattern) if case_sensitive else (txt.strip().lower() == pat_cmp)
                                if matched:
                                    ctx = []
                                    if context_lines and use_buf:
                                        start = max(0, ln_num-context_lines-1)
                                        end = min(len(lines), ln_num+context_lines)
                                        ctx = [l.strip() for l in lines[start:end]]
                                    else:
                                        ctx = [txt.strip()]
                                    rec = {'file': fp, 'line_number': ln_num, 'line': txt[:200], 'context': ctx}
                                    if group_by_file:
                                        grouped.setdefault(fp, []).append(rec)
                                    else:
                                        results.append(rec)
                                    found += 1
                                    if found >= max_results:
                                        break
                    except Exception:
                        continue
                if found >= max_results:
                    break
            return ToolResult(success=True, content=grouped if group_by_file else results)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to search files: {e}")

class FastGrepTool(BaseTool):
    name = "fast_grep"
    description = "Search for a keyword or regex pattern in a directory. This is an alias for the search_files tool."
    args_schema = FastGrepParams

    def run(self, keyword: str, directory: str = '.', file_pattern: Optional[str] = None) -> ToolResult:
        search_tool = SearchFilesTool()
        return search_tool.run(pattern=keyword, directory=directory, file_pattern=file_pattern or '*')
