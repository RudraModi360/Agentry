"""
Advanced Reasoning Engines for Agentry Framework
Implements Chain of Thought (CoT), Tree of Thoughts (ToT), and other reasoning strategies.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import json


class ReasoningStrategy(Enum):
    """Available reasoning strategies"""
    DIRECT = "direct"  # Direct answer, no special reasoning
    CHAIN_OF_THOUGHT = "chain_of_thought"  # Step-by-step linear reasoning
    TREE_OF_THOUGHTS = "tree_of_thoughts"  # Explore multiple reasoning paths
    SELF_REFLECTION = "self_reflection"  # Critique and refine answers
    DECOMPOSITION = "decomposition"  # Break into subproblems


@dataclass
class ReasoningStep:
    """Single step in a reasoning chain"""
    step_number: int
    description: str
    thought: str
    action: Optional[str] = None
    result: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ReasoningPath:
    """A complete reasoning path (for Tree of Thoughts)"""
    path_id: int
    steps: List[ReasoningStep]
    final_answer: str
    total_confidence: float
    rationale: str


class ChainOfThought:
    """
    Chain of Thought (CoT) Reasoning
    Encourages step-by-step logical thinking before answering.
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def generate_prompt(self, query: str, context: Optional[str] = None) -> str:
        """
        Generate a CoT-enhanced prompt that encourages step-by-step reasoning.
        
        Args:
            query: User's question
            context: Optional context information
            
        Returns:
            Enhanced prompt with CoT instructions
        """
        prompt = f"""Think through this problem step by step before providing your final answer.

<query>
{query}
</query>

{f'<context>{context}</context>' if context else ''}

<reasoning_instructions>
Use this format for your reasoning:

<thinking>
Step 1: [Understand the problem]
- What is being asked?
- What information do I have?
- What information do I need?

Step 2: [Break down the approach]
- What steps are needed?
- What tools might help?
- What's the logical sequence?

Step 3: [Consider edge cases]
- What could go wrong?
- What assumptions am I making?
- What alternatives exist?

Step 4: [Arrive at solution]
- Based on the above reasoning...
- The best approach is...
</thinking>

<answer>
[Your final, well-reasoned answer]
</answer>
</reasoning_instructions>

Now, think through the query step by step:"""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse CoT response to extract thinking and answer"""
        import re
        
        # Extract thinking section
        thinking_match = re.search(
            r'<thinking>(.*?)</thinking>', 
            response, 
            re.DOTALL | re.IGNORECASE
        )
        thinking = thinking_match.group(1).strip() if thinking_match else ""
        
        # Extract answer section
        answer_match = re.search(
            r'<answer>(.*?)</answer>',
            response,
            re.DOTALL | re.IGNORECASE
        )
        answer = answer_match.group(1).strip() if answer_match else response
        
        # Extract steps
        steps = re.findall(
            r'Step \d+:.*?(?=Step \d+:|</thinking>|$)',
            thinking,
            re.DOTALL
        )
        
        return {
            'thinking': thinking,
            'answer': answer,
            'steps': [s.strip() for s in steps],
            'step_count': len(steps)
        }


class TreeOfThoughts:
    """
    Tree of Thoughts (ToT) Reasoning
    Explores multiple reasoning paths and selects the best one.
    """
    
    def __init__(self, num_paths: int = 3, debug: bool = False):
        self.num_paths = num_paths
        self.debug = debug
    
    def generate_prompt(
        self, 
        query: str, 
        context: Optional[str] = None,
        exploration_depth: int = 2
    ) -> str:
        """
        Generate ToT prompt that explores multiple reasoning paths.
        
        Args:
            query: User's question
            context: Optional context
            exploration_depth: How many levels deep to explore
            
        Returns:
            ToT-enhanced prompt
        """
        prompt = f"""Explore multiple reasoning paths to solve this problem comprehensively.

<query>
{query}
</query>

{f'<context>{context}</context>' if context else ''}

<tree_of_thoughts_instructions>
Generate {self.num_paths} different approaches to solve this problem:

**Path 1: [Name of approach]**
<thinking_path_1>
- Initial hypothesis: ...
- Reasoning steps: ...
- Potential outcome: ...
- Confidence: [0-1]
</thinking_path_1>

**Path 2: [Alternative approach]**
<thinking_path_2>
- Initial hypothesis: ...
- Reasoning steps: ...
- Potential outcome: ...
- Confidence: [0-1]
</thinking_path_2>

**Path 3: [Another alternative]**
<thinking_path_3>
- Initial hypothesis: ...
- Reasoning steps: ...
- Potential outcome: ...
- Confidence: [0-1]
</thinking_path_3>

<evaluation>
Compare the paths:
- Path 1 strengths/weaknesses: ...
- Path 2 strengths/weaknesses: ...
- Path 3 strengths/weaknesses: ...

Best path: [1/2/3] because...
</evaluation>

<final_answer>
Based on the exploration, the best solution is:
[Your answer incorporating insights from all paths]
</final_answer>
</tree_of_thoughts_instructions>

Explore multiple approaches:"""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse ToT response to extract all paths and evaluation"""
        import re
        
        # Extract thinking paths
        paths = []
        for i in range(1, self.num_paths + 1):
            path_match = re.search(
                f'<thinking_path_{i}>(.*?)</thinking_path_{i}>',
                response,
                re.DOTALL | re.IGNORECASE
            )
            if path_match:
                paths.append({
                    'path_id': i,
                    'content': path_match.group(1).strip()
                })
        
        # Extract evaluation
        eval_match = re.search(
            r'<evaluation>(.*?)</evaluation>',
            response,
            re.DOTALL | re.IGNORECASE
        )
        evaluation = eval_match.group(1).strip() if eval_match else ""
        
        # Extract final answer
        answer_match = re.search(
            r'<final_answer>(.*?)</final_answer>',
            response,
            re.DOTALL | re.IGNORECASE
        )
        answer = answer_match.group(1).strip() if answer_match else response
        
        return {
            'paths': paths,
            'evaluation': evaluation,
            'answer': answer,
            'num_paths_explored': len(paths)
        }


class SelfReflection:
    """
    Self-Reflection Reasoning
    Agent critiques its own answer and refines it.
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def generate_critique_prompt(
        self, 
        query: str, 
        initial_answer: str
    ) -> str:
        """Generate prompt for self-critique"""
        prompt = f"""Critically evaluate and improve this answer.

<original_query>
{query}
</original_query>

<initial_answer>
{initial_answer}
</initial_answer>

<self_critique_instructions>
Evaluate the answer across these dimensions:

<critique>
1. **Accuracy**: Are the facts correct? Any errors?
2. **Completeness**: Did it address all parts of the query?
3. **Clarity**: Is it well-explained and easy to understand?
4. **Relevance**: Does it stay focused on the question?
5. **Sources**: If factual claims, are they grounded?

Issues found:
- [List any issues]

Suggestions for improvement:
- [List improvements]
</critique>

<improved_answer>
[Provide a refined, better answer incorporating the critique]
</improved_answer>
</self_critique_instructions>

Now critique and improve:"""
        
        return prompt


class ReasoningEngine:
    """
    Main reasoning engine that orchestrates different reasoning strategies.
    Automatically selects the best strategy based on query complexity.
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.cot = ChainOfThought(debug=debug)
        self.tot = TreeOfThoughts(num_paths=3, debug=debug)
        self.reflection = SelfReflection(debug=debug)
    
    def select_strategy(
        self, 
        query: str, 
        complexity: float
    ) -> ReasoningStrategy:
        """
        Automatically select reasoning strategy based on query complexity.
        
        Args:
            query: User's query
            complexity: Complexity score from QueryAnalyzer (0-1)
            
        Returns:
            Best reasoning strategy
        """
        query_lower = query.lower()
        
        # Very complex problems → Tree of Thoughts
        if complexity > 0.7 or any(word in query_lower for word in [
            'compare', 'evaluate', 'analyze', 'complex', 'multiple'
        ]):
            return ReasoningStrategy.TREE_OF_THOUGHTS
        
        # Moderate complexity → Chain of Thought
        elif complexity > 0.3 or any(word in query_lower for word in [
            'how', 'why', 'explain', 'step', 'solve', 'best', 'find', 'search', 'what', 'where'
        ]):
            return ReasoningStrategy.CHAIN_OF_THOUGHT
        
        # Refinement needed → Self Reflection
        elif any(word in query_lower for word in [
            'improve', 'better', 'refine', 'critique'
        ]):
            return ReasoningStrategy.SELF_REFLECTION
        
        # Simple queries → Direct
        else:
            return ReasoningStrategy.DIRECT
    
    def enhance_prompt(
        self,
        query: str,
        strategy: Optional[ReasoningStrategy] = None,
        complexity: float = 0.5,
        context: Optional[str] = None
    ) -> str:
        """
        Enhance a prompt with the appropriate reasoning strategy.
        
        Args:
            query: User's query
            strategy: Specific strategy to use (None = auto-select)
            complexity: Query complexity score
            context: Optional context information
            
        Returns:
            Enhanced prompt with reasoning instructions
        """
        # Auto-select strategy if not specified
        if strategy is None:
            strategy = self.select_strategy(query, complexity)
        
        if self.debug:
            print(f"[ReasoningEngine] Selected strategy: {strategy.value}")
        
        # Apply strategy
        if strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return self.cot.generate_prompt(query, context)
        
        elif strategy == ReasoningStrategy.TREE_OF_THOUGHTS:
            return self.tot.generate_prompt(query, context)
        
        elif strategy == ReasoningStrategy.DIRECT:
            # Just return query with minimal structure
            return f"<query>{query}</query>\n\nProvide a clear, direct answer:"
        
        else:
            # Default to CoT
            return self.cot.generate_prompt(query, context)
    
    def parse_reasoning_response(
        self,
        response: str,
        strategy: ReasoningStrategy
    ) -> Dict[str, Any]:
        """Parse response based on the reasoning strategy used"""
        if strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return self.cot.parse_response(response)
        elif strategy == ReasoningStrategy.TREE_OF_THOUGHTS:
            return self.tot.parse_response(response)
        else:
            return {'answer': response}
    
    def get_strategy_description(self, strategy: ReasoningStrategy) -> str:
        """Get human-readable description of a reasoning strategy"""
        descriptions = {
            ReasoningStrategy.DIRECT: "Direct answer without special reasoning",
            ReasoningStrategy.CHAIN_OF_THOUGHT: "Step-by-step logical reasoning (CoT)",
            ReasoningStrategy.TREE_OF_THOUGHTS: "Multiple path exploration (ToT)",
            ReasoningStrategy.SELF_REFLECTION: "Self-critique and refinement",
            ReasoningStrategy.DECOMPOSITION: "Problem decomposition"
        }
        return descriptions.get(strategy, "Unknown strategy")
