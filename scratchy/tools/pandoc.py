import subprocess
import shutil
from typing import Optional, List
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult

class PandocConvertParams(BaseModel):
    input_path: str = Field(..., description="Absolute path to the input file.")
    output_path: str = Field(..., description="Absolute path to the output file.")
    input_format: Optional[str] = Field(None, description="Format of input file (e.g. 'markdown', 'docx', 'html'). If not provided, pandoc guesses from extension.")
    output_format: Optional[str] = Field(None, description="Format of output file. If not provided, pandoc guesses from extension.")
    extra_args: Optional[List[str]] = Field(None, description="Additional pandoc arguments (e.g. ['--standalone', '--table-of-contents', '--pdf-engine=xelatex']).")

class PandocConvertTool(BaseTool):
    name = "pandoc_convert"
    description = "Convert documents between formats using Pandoc (e.g., Markdown to PDF, DOCX to HTML). Requires Pandoc to be installed."
    args_schema = PandocConvertParams

    def run(self, input_path: str, output_path: str, input_format: str = None, output_format: str = None, extra_args: List[str] = None) -> ToolResult:
        # Check if pandoc is installed
        if not shutil.which("pandoc"):
            return ToolResult(success=False, error="Pandoc is not installed or not in the system PATH.")

        command = ["pandoc", input_path, "-o", output_path]

        if input_format:
            command.extend(["-f", input_format])
        
        if output_format:
            command.extend(["-t", output_format])

        if extra_args:
            command.extend(extra_args)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=300
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False, 
                    error=f"Pandoc conversion failed with exit code {result.returncode}",
                    content=f"STDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
                )

            return ToolResult(
                success=True, 
                content=f"Successfully converted '{input_path}' to '{output_path}'.\nSTDOUT:\n{result.stdout}"
            )

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Pandoc conversion timed out.")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to execute pandoc: {e}")
