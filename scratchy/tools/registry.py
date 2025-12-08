from typing import Dict, Any, List, Type
from .base import BaseTool, ToolResult
from .filesystem import (
    ReadFileTool, CreateFileTool, EditFileTool, DeleteFileTool, 
    ListFilesTool, SearchFilesTool, FastGrepTool
)
from .execution import ExecuteCommandTool, CodeExecuteTool
from .web import WebSearchTool, UrlFetchTool
from .git import GitCommandTool
from .pandoc import PandocConvertTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_defaults()

    def register_tool(self, tool: BaseTool):
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered.")
        self._tools[tool.name] = tool

    def _register_defaults(self):
        self.register_tool(ReadFileTool())
        self.register_tool(CreateFileTool())
        self.register_tool(EditFileTool())
        self.register_tool(DeleteFileTool())
        self.register_tool(ListFilesTool())
        self.register_tool(SearchFilesTool())
        self.register_tool(FastGrepTool())
        self.register_tool(ExecuteCommandTool())
        self.register_tool(CodeExecuteTool())
        self.register_tool(WebSearchTool())
        self.register_tool(UrlFetchTool())
        self.register_tool(GitCommandTool())
        self.register_tool(PandocConvertTool())

    def get_tool(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")
        
        try:
            # Pydantic validation
            validated_args = tool.args_schema(**tool_args).model_dump()
            return tool.run(**validated_args)
        except Exception as e:
            return ToolResult(success=False, error=f"Error executing tool {tool_name}: {e}")

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        return [tool.schema for tool in self._tools.values()]

# Global registry instance
registry = ToolRegistry()

def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> ToolResult:
    return registry.execute_tool(tool_name, tool_args)

# Tool categories
SAFE_TOOLS = ['read_file', 'list_files', 'search_files', 'fast_grep']
APPROVAL_REQUIRED_TOOLS = ['create_file', 'edit_file', 'pandoc_convert', 'web_search', 'url_fetch']
DANGEROUS_TOOLS = ['delete_file', 'execute_command', 'git_command', 'code_execute']
