"""
Execution Summary Module

Generates a narrative walkthrough of agent execution including:
- What the user asked for
- What tasks the agent identified
- Step-by-step walkthrough of execution
- Clarifications/counter-questions asked
- Task status (completed, in-progress, blocked, failed)
- Clear recommendations for next steps
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json
from enum import Enum


class TaskStatus(Enum):
    """Status of a task."""
    COMPLETED = "✅ Completed"
    IN_PROGRESS = "⏳ In Progress"
    BLOCKED = "🚫 Blocked"
    FAILED = "❌ Failed"
    NOT_STARTED = "⊘ Not Started"


class ToolCallStatus(Enum):
    """Status of a tool call execution."""
    SUCCESS = "✅ Success"
    FAILED = "❌ Failed"
    PARTIAL = "⚠️ Partial"
    SKIPPED = "⊘ Skipped"


@dataclass
class TaskRecord:
    """Records a single task/objective."""
    task_description: str
    status: TaskStatus = TaskStatus.NOT_STARTED
    started_at_iteration: Optional[int] = None
    completed_at_iteration: Optional[int] = None
    clarifications_asked: List[str] = field(default_factory=list)
    tool_calls_used: List[str] = field(default_factory=list)
    result_summary: Optional[str] = None
    error_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task_description,
            "status": self.status.value,
            "started": self.started_at_iteration,
            "completed": self.completed_at_iteration,
            "clarifications": self.clarifications_asked,
            "tools_used": self.tool_calls_used,
            "result": self.result_summary,
            "error": self.error_reason
        }


@dataclass
class ToolCallRecord:
    """Records a single tool call and its result."""
    iteration: int
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ToolCallStatus = ToolCallStatus.SUCCESS
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "tool": self.tool_name,
            "parameters": self.parameters,
            "status": self.status.value,
            "result": self.result[:200] if self.result else None,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2)
        }


@dataclass
class IterationRecord:
    """Records what happened in a single iteration."""
    iteration_number: int
    agent_thought: Optional[str] = None
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    response_generated: bool = False
    response_content: Optional[str] = None
    clarification_asked: Optional[str] = None
    decision_made: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration_number,
            "thought": self.agent_thought,
            "tool_calls": len(self.tool_calls),
            "response": self.response_generated,
            "clarification": self.clarification_asked,
            "decision": self.decision_made
        }


class ExecutionSummary:
    """
    Generates a narrative walkthrough of agent execution.
    
    Tracks:
    - User's original request
    - Tasks identified by agent
    - Step-by-step walkthrough
    - Clarifications asked
    - Task completions and failures
    - Recommendations
    """
    
    def __init__(self, agent_name: str = "Agent", session_id: str = "default"):
        self.agent_name = agent_name
        self.session_id = session_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        
        # User Input
        self.user_request: Optional[str] = None
        
        # Tasks identified
        self.identified_tasks: List[TaskRecord] = []
        
        # Tracking
        self.iterations: List[IterationRecord] = []
        self.tool_calls: List[ToolCallRecord] = []
        self.clarifications_asked: List[str] = []
        
        # Status
        self.execution_status: str = "in_progress"
        self.final_response: Optional[str] = None
        self.execution_error: Optional[str] = None
        
        # Counters
        self.total_iterations: int = 0
        self.total_tool_calls: int = 0
        self.successful_tool_calls: int = 0
        self.failed_tool_calls: int = 0
    
    def set_user_request(self, request: str):
        """Set the original user request."""
        self.user_request = request
    
    def identify_task(self, task: str):
        """Add an identified task/objective."""
        task_record = TaskRecord(task_description=task)
        self.identified_tasks.append(task_record)
    
    def task_started(self, task_index: int, iteration: int):
        """Mark when a task starts."""
        if task_index < len(self.identified_tasks):
            self.identified_tasks[task_index].status = TaskStatus.IN_PROGRESS
            self.identified_tasks[task_index].started_at_iteration = iteration
    
    def task_completed(self, task_index: int, iteration: int, result: str = ""):
        """Mark when a task completes."""
        if task_index < len(self.identified_tasks):
            self.identified_tasks[task_index].status = TaskStatus.COMPLETED
            self.identified_tasks[task_index].completed_at_iteration = iteration
            self.identified_tasks[task_index].result_summary = result
    
    def task_failed(self, task_index: int, reason: str):
        """Mark when a task fails."""
        if task_index < len(self.identified_tasks):
            self.identified_tasks[task_index].status = TaskStatus.FAILED
            self.identified_tasks[task_index].error_reason = reason
    
    def task_blocked(self, task_index: int, reason: str):
        """Mark when a task is blocked."""
        if task_index < len(self.identified_tasks):
            self.identified_tasks[task_index].status = TaskStatus.BLOCKED
            self.identified_tasks[task_index].error_reason = reason
    
    def add_clarification(self, question: str):
        """Record that the agent asked a clarification."""
        self.clarifications_asked.append(question)
        if self.iterations:
            last_iter = self.iterations[-1]
            last_iter.clarification_asked = question
    
    def start_iteration(self, iteration_number: int) -> IterationRecord:
        """Start tracking a new iteration."""
        record = IterationRecord(iteration_number=iteration_number)
        self.iterations.append(record)
        self.total_iterations = iteration_number
        return record
    
    def record_iteration_thought(self, thought: str):
        """Record what the agent was thinking."""
        if self.iterations:
            self.iterations[-1].agent_thought = thought
    
    def record_iteration_decision(self, decision: str):
        """Record what decision the agent made."""
        if self.iterations:
            self.iterations[-1].decision_made = decision
    
    def record_tool_call(
        self, 
        iteration: int, 
        tool_name: str, 
        parameters: Dict[str, Any],
        result: Optional[str] = None,
        error: Optional[str] = None,
        status: ToolCallStatus = ToolCallStatus.SUCCESS,
        duration_ms: float = 0.0
    ) -> ToolCallRecord:
        """Record a tool call and its result."""
        record = ToolCallRecord(
            iteration=iteration,
            tool_name=tool_name,
            parameters=parameters,
            status=status,
            result=result,
            error=error,
            duration_ms=duration_ms
        )
        self.tool_calls.append(record)
        self.total_tool_calls += 1
        
        if status == ToolCallStatus.SUCCESS:
            self.successful_tool_calls += 1
        elif status == ToolCallStatus.FAILED:
            self.failed_tool_calls += 1
        
        # Update iteration record
        if self.iterations and len(self.iterations) > 0:
            current_iter = self.iterations[-1]
            if current_iter.iteration_number == iteration:
                current_iter.tool_calls.append(record)
        
        return record
    
    def record_iteration_response(self, response: str):
        """Record the agent's response in this iteration."""
        if self.iterations and len(self.iterations) > 0:
            last_iter = self.iterations[-1]
            last_iter.response_generated = True
            last_iter.response_content = response
    
    def finalize(self, status: str = "completed", error: Optional[str] = None, final_response: Optional[str] = None):
        """Finalize the execution summary."""
        self.end_time = datetime.now()
        self.execution_status = status
        self.execution_error = error
        self.final_response = final_response
    
    @property
    def duration_seconds(self) -> float:
        """Total execution duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    def get_summary_text(self) -> str:
        """Generate a detailed narrative walkthrough."""
        lines = []
        
        lines.append("\n" + "="*80)
        lines.append("EXECUTION WALKTHROUGH")
        lines.append("="*80)
        
        # User's Request
        lines.append(f"\n📝 USER REQUEST")
        lines.append("─" * 80)
        if self.user_request:
            lines.append(f"  \"{self.user_request}\"")
        else:
            lines.append("  (No request recorded)")
        
        # Identified Tasks
        if self.identified_tasks:
            lines.append(f"\n🎯 TASKS IDENTIFIED")
            lines.append("─" * 80)
            for i, task in enumerate(self.identified_tasks, 1):
                status_icon = "✅" if task.status == TaskStatus.COMPLETED else \
                             "⏳" if task.status == TaskStatus.IN_PROGRESS else \
                             "🚫" if task.status == TaskStatus.BLOCKED else \
                             "❌" if task.status == TaskStatus.FAILED else "⊘"
                lines.append(f"  {i}. {status_icon} {task.task_description}")
                lines.append(f"     Status: {task.status.value}")
                if task.started_at_iteration:
                    lines.append(f"     Started at: Iteration {task.started_at_iteration}")
                if task.completed_at_iteration:
                    lines.append(f"     Completed at: Iteration {task.completed_at_iteration}")
                if task.clarifications_asked:
                    lines.append(f"     Questions asked: {', '.join(task.clarifications_asked)}")
                if task.tool_calls_used:
                    lines.append(f"     Tools used: {', '.join(task.tool_calls_used)}")
                if task.result_summary:
                    lines.append(f"     Result: {task.result_summary}")
                if task.error_reason:
                    lines.append(f"     Reason: {task.error_reason}")
                lines.append("")
        
        # Clarifications Asked
        if self.clarifications_asked:
            lines.append(f"\n❓ CLARIFICATIONS ASKED BY AGENT")
            lines.append("─" * 80)
            for i, clarification in enumerate(self.clarifications_asked, 1):
                lines.append(f"  {i}. {clarification}")
            lines.append("")
        
        # Iteration Walkthrough
        if self.iterations:
            lines.append(f"\n📊 ITERATION WALKTHROUGH (Total: {len(self.iterations)} iterations)")
            lines.append("─" * 80)
            
            for iteration in self.iterations[:15]:  # Show first 15 iterations
                lines.append(f"\n  Iteration {iteration.iteration_number}:")
                
                if iteration.agent_thought:
                    thought_preview = iteration.agent_thought[:100]
                    if len(iteration.agent_thought) > 100:
                        thought_preview += "..."
                    lines.append(f"    💭 Thought: {thought_preview}")
                
                if iteration.tool_calls:
                    lines.append(f"    🔧 Tools Called:")
                    for tc in iteration.tool_calls:
                        status_emoji = "✅" if tc.status == ToolCallStatus.SUCCESS else "❌"
                        lines.append(f"      {status_emoji} {tc.tool_name}")
                        if tc.error:
                            lines.append(f"         Error: {tc.error[:80]}")
                
                if iteration.clarification_asked:
                    lines.append(f"    ❓ Asked: {iteration.clarification_asked[:80]}")
                
                if iteration.decision_made:
                    lines.append(f"    🤔 Decision: {iteration.decision_made[:80]}")
                
                if iteration.response_generated:
                    if iteration.response_content:
                        content_preview = iteration.response_content[:100].replace('\n', ' ')
                        lines.append(f"    📝 Response: {content_preview}...")
                    else:
                        lines.append(f"    📝 Response generated")
            
            if len(self.iterations) > 15:
                lines.append(f"\n  ... and {len(self.iterations) - 15} more iterations")
        
        # Tool Statistics
        lines.append(f"\n📈 TOOL EXECUTION STATISTICS")
        lines.append("─" * 80)
        lines.append(f"  Total Tool Calls: {self.total_tool_calls}")
        lines.append(f"  ✅ Successful: {self.successful_tool_calls}")
        lines.append(f"  ❌ Failed: {self.failed_tool_calls}")
        if self.total_tool_calls > 0:
            success_rate = (self.successful_tool_calls / self.total_tool_calls) * 100
            lines.append(f"  📊 Success Rate: {success_rate:.1f}%")
        
        # Unique tools used
        if self.tool_calls:
            unique_tools = {}
            for tc in self.tool_calls:
                unique_tools[tc.tool_name] = unique_tools.get(tc.tool_name, 0) + 1
            
            lines.append(f"\n  Tools Used:")
            for tool_name, count in sorted(unique_tools.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"    • {tool_name}: {count} call(s)")
        
        # Task Summary
        lines.append(f"\n✨ TASK COMPLETION SUMMARY")
        lines.append("─" * 80)
        completed = sum(1 for t in self.identified_tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.identified_tasks if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self.identified_tasks if t.status == TaskStatus.BLOCKED)
        in_progress = sum(1 for t in self.identified_tasks if t.status == TaskStatus.IN_PROGRESS)
        
        lines.append(f"  ✅ Completed: {completed}/{len(self.identified_tasks)}")
        lines.append(f"  ⏳ In Progress: {in_progress}/{len(self.identified_tasks)}")
        lines.append(f"  🚫 Blocked: {blocked}/{len(self.identified_tasks)}")
        lines.append(f"  ❌ Failed: {failed}/{len(self.identified_tasks)}")
        
        # Execution Status
        lines.append(f"\n📋 EXECUTION STATUS")
        lines.append("─" * 80)
        lines.append(f"  Overall Status: {self.execution_status.upper()}")
        lines.append(f"  Duration: {self.duration_seconds:.2f} seconds")
        lines.append(f"  Total Iterations: {self.total_iterations}")
        
        if self.execution_error:
            lines.append(f"  ❌ Error: {self.execution_error}")
        
        # Next Steps
        lines.append(f"\n🚀 NEXT STEPS")
        lines.append("─" * 80)
        
        next_steps = self._generate_recommendations()
        for step in next_steps:
            lines.append(f"  {step}")
        
        lines.append("\n" + "="*80 + "\n")
        
        return "\n".join(lines)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        steps = []
        
        # Task-based recommendations
        failed_tasks = [t for t in self.identified_tasks if t.status == TaskStatus.FAILED]
        blocked_tasks = [t for t in self.identified_tasks if t.status == TaskStatus.BLOCKED]
        completed_tasks = [t for t in self.identified_tasks if t.status == TaskStatus.COMPLETED]
        
        if completed_tasks:
            steps.append(f"✅ {len(completed_tasks)} task(s) completed successfully")
        
        if blocked_tasks:
            steps.append(f"🚫 {len(blocked_tasks)} task(s) blocked:")
            for task in blocked_tasks:
                if task.error_reason:
                    steps.append(f"   • {task.task_description}: {task.error_reason}")
        
        if failed_tasks:
            steps.append(f"❌ {len(failed_tasks)} task(s) failed:")
            for task in failed_tasks:
                if task.error_reason:
                    steps.append(f"   • {task.task_description}: {task.error_reason}")
        
        if self.clarifications_asked:
            steps.append(f"❓ Agent asked for {len(self.clarifications_asked)} clarification(s)")
            steps.append("   Consider providing more details if tasks were blocked by missing info")
        
        # Status-specific recommendations
        if self.execution_status == "timeout":
            steps.append("⏱️  Execution timed out - try:")
            steps.append("   • Breaking the task into smaller, simpler requests")
            steps.append("   • Providing more specific constraints or examples")
            steps.append("   • Reducing the number of tools available via tool_search_regex patterns")
        
        elif self.execution_status == "completed":
            if len(completed_tasks) == len(self.identified_tasks):
                steps.append("✨ All tasks completed successfully!")
                steps.append("   You can now review and use the generated outputs")
            else:
                steps.append("⚠️  Some tasks incomplete - consider:")
                steps.append("   • Asking follow-up questions for the remaining tasks")
                steps.append("   • Clarifying requirements that blocked the agent")
        
        elif self.execution_status == "failed":
            steps.append("🔍 Troubleshooting steps:")
            steps.append("   • Check agent debug logs above for specific error messages")
            steps.append("   • Verify that all required tools are available")
            steps.append("   • Try with a simpler/more specific request")
        
        if not steps:
            steps.append("✅ Execution complete")
        
        return steps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request": self.user_request,
            "status": self.execution_status,
            "duration_seconds": self.duration_seconds,
            "iterations": self.total_iterations,
            "tool_calls": {
                "total": self.total_tool_calls,
                "successful": self.successful_tool_calls,
                "failed": self.failed_tool_calls
            },
            "tasks": [t.to_dict() for t in self.identified_tasks],
            "clarifications": self.clarifications_asked,
            "error": self.execution_error
        }
    
    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)
