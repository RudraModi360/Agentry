import subprocess
from typing import Literal, Optional
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult

# --- Schemas ---

class ExecuteCommandParams(BaseModel):
    command: str = Field(..., description='Shell command to execute.')
    command_type: Literal['bash', 'setup', 'run'] = Field(..., description='Command type.')
    working_directory: Optional[str] = Field(None, description='Directory to run command in.')
    timeout: int = Field(300, description='Max execution time in seconds (1-300)', ge=1, le=300)

class ExecuteCodeParams(BaseModel):
    code: str = Field(..., description='The Python code to execute.')
    timeout: int = Field(60, description='Max execution time in seconds (1-300)', ge=1, le=300)

# --- Tools ---

class ExecuteCommandTool(BaseTool):
    name = "execute_command"
    description = "Run shell commands, scripts. Only for commands that complete quickly."
    args_schema = ExecuteCommandParams

    def run(self, command: str, command_type: str, working_directory: str = None, timeout: int = 300) -> ToolResult:
        try:
            if command_type == 'python':
                escaped = command.replace('"', '\\"')
                command = f"python -c '{escaped}' "

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_directory,
                timeout=timeout
            )

            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            if result.returncode != 0:
                return ToolResult(success=False, content=output, error=f"Command failed with exit code {result.returncode}")
            
            return ToolResult(success=True, content=output)

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Command timed out.")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to execute command: {e}")

class CodeExecuteTool(BaseTool):
    name = "code_execute"
    description = "Executes Python code and returns the output. The code should be self-contained."
    args_schema = ExecuteCodeParams

    def run(self, code: str, timeout: int = 60) -> ToolResult:
        try:
            process = subprocess.run(
                ['python', '-c', code],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            output = f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"

            if process.returncode == 0:
                return ToolResult(success=True, content=output)
            else:
                return ToolResult(success=False, content=output, error=f"Code execution failed with exit code {process.returncode}")

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Code execution timed out.")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to execute code: {e}")
