import subprocess
from typing import Optional
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult

class GitCommandParams(BaseModel):
    command: str = Field(..., description='Git command to execute (e.g., "status", "commit -m ...", "log"). Do not include "git" prefix.')
    working_directory: Optional[str] = Field(None, description='Directory to run git command in.')

class GitCommandTool(BaseTool):
    name = "git_command"
    description = "Execute git commands to manage version control. Use this for all git operations."
    args_schema = GitCommandParams

    def run(self, command: str, working_directory: str = None) -> ToolResult:
        try:
            full_command = f"git {command}"
            
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_directory,
                timeout=300
            )

            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            
            if result.returncode != 0:
                return ToolResult(success=False, content=output, error=f"Git command failed with exit code {result.returncode}")
            
            return ToolResult(success=True, content=output)

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Git command timed out.")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to execute git command: {e}")
