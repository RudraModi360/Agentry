"""
Query Analyzer for Agentry Framework
Analyzes user queries to determine optimal tool usage and reasoning approach.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import re


class QueryType(Enum):
    """Types of user queries"""
    FACTUAL = "factual"  # Needs current facts/data
    RECOMMENDATION = "recommendation"  # Asking for suggestions
    HOW_TO = "how_to"  # Tutorial/guide requests
    COMPARISON = "comparison"  # Comparing options
    TEMPORAL = "temporal"  # Current/recent events
    RESOURCE = "resource"  # Requesting files/downloads
    CODING = "coding"  # Programming questions
    REASONING = "reasoning"  # Pure logic/math
    CONVERSATIONAL = "conversational"  # General chat


@dataclass
class QueryAnalysis:
    """Results of query analysis"""
    query_type: QueryType
    confidence: float  # 0.0 to 1.0
    suggested_tools: List[str]  # Recommended tools to use
    reasoning: str  # Why these suggestions
    keywords: List[str]  # Extracted keywords
    needs_web_search: bool  # Should web_search be called?
    needs_current_info: bool  # Requires up-to-date data?
    complexity_score: float  # How complex is the query (0-1)


class QueryAnalyzer:
    """
    Analyzes user queries to determine:
    - What type of query it is
    - Which tools should be used
    - Whether web search is needed
    - Complexity level for reasoning approach
    """
    
    # Pattern definitions for different query types
    RECOMMENDATION_PATTERNS = [
        r'\b(best|top|recommend|suggest|should i use|which is better|what to use)\b',
        r'\b(favorite|preferred|optimal|ideal)\b',
    ]
    
    TEMPORAL_PATTERNS = [
        r'\b(latest|current|recent|new|2024|2025|today|this year)\b',
        r'\b(update|news|what happened|now)\b',
    ]
    
    RESOURCE_PATTERNS = [
        r'\b(download|free|get|obtain|access|where to find)\b',
        r'\b(book|library|resource|tool|software|package)\b',
    ]
    
    HOW_TO_PATTERNS = [
        r'\b(how to|how do i|tutorial|guide|walkthrough|setup|configure)\b',
        r'\b(step by step|instructions|teach me)\b',
    ]
    
    COMPARISON_PATTERNS = [
        r'\b(vs|versus|compare|difference|better than|or)\b',
        r'\b(which one|what\'s the difference)\b',
    ]
    
    CODING_PATTERNS = [
        r'\b(code|function|class|debug|error|bug|implement)\b',
        r'\b(python|javascript|java|react|api|sql)\b',
        r'\b(syntax|compile|runtime)\b',
    ]
    
    REASONING_PATTERNS = [
        r'\b(explain|why|how does|what is|define|concept)\b',
        r'\b(calculate|solve|prove|derive)\b',
    ]
    
    # Web search mandatory triggers
    WEB_SEARCH_TRIGGERS = [
        'best', 'top', 'recommend', 'latest', 'current', 'recent', 
        '2024', '2025', 'download', 'free', 'how to', 'tutorial',
        'vs', 'versus', 'compare', 'news', 'update', 'documentation'
    ]
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query and return structured analysis.
        
        Args:
            query: User's input text
            
        Returns:
            QueryAnalysis with recommendations
        """
        query_lower = query.lower()
        
        # Detect query type
        query_type, confidence = self._detect_query_type(query_lower)
        
        # Extract keywords
        keywords = self._extract_keywords(query)
        
        # Determine if web search is needed
        needs_web_search = self._needs_web_search(query_lower, keywords)
        
        # Check if current information is needed
        needs_current_info = self._needs_current_info(query_lower)
        
        # Calculate complexity
        complexity_score = self._calculate_complexity(query, keywords)
        
        # Suggest tools
        suggested_tools = self._suggest_tools(
            query_type, needs_web_search, query_lower
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            query_type, needs_web_search, suggested_tools
        )
        
        analysis = QueryAnalysis(
            query_type=query_type,
            confidence=confidence,
            suggested_tools=suggested_tools,
            reasoning=reasoning,
            keywords=keywords,
            needs_web_search=needs_web_search,
            needs_current_info=needs_current_info,
            complexity_score=complexity_score
        )
        
        if self.debug:
            print(f"[QueryAnalyzer] Type: {query_type.value}, Confidence: {confidence:.2f}")
            print(f"[QueryAnalyzer] Tools: {suggested_tools}")
            print(f"[QueryAnalyzer] Web Search: {needs_web_search}")
        
        return analysis
    
    def _detect_query_type(self, query: str) -> tuple[QueryType, float]:
        """Detect the primary type of query"""
        scores = {
            QueryType.RECOMMENDATION: self._match_patterns(query, self.RECOMMENDATION_PATTERNS),
            QueryType.TEMPORAL: self._match_patterns(query, self.TEMPORAL_PATTERNS),
            QueryType.RESOURCE: self._match_patterns(query, self.RESOURCE_PATTERNS),
            QueryType.HOW_TO: self._match_patterns(query, self.HOW_TO_PATTERNS),
            QueryType.COMPARISON: self._match_patterns(query, self.COMPARISON_PATTERNS),
            QueryType.CODING: self._match_patterns(query, self.CODING_PATTERNS),
            QueryType.REASONING: self._match_patterns(query, self.REASONING_PATTERNS),
        }
        
        # Find highest score
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        
        # If no strong match, classify as conversational
        if max_score < 0.3:
            return QueryType.CONVERSATIONAL, 0.5
        
        # Check if it's factual (needs verification)
        factual_indicators = ['what is', 'who is', 'when did', 'where is']
        if any(ind in query for ind in factual_indicators):
            return QueryType.FACTUAL, max_score * 0.8
        
        return max_type, max_score
    
    def _match_patterns(self, text: str, patterns: List[str]) -> float:
        """Match text against regex patterns and return score"""
        matches = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        return min(matches / len(patterns), 1.0) if patterns else 0.0
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'can', 'may', 'might', 'must', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:10]  # Return top 10
    
    def _needs_web_search(self, query: str, keywords: List[str]) -> bool:
        """Determine if web search should be used"""
        # Check for mandatory triggers
        for trigger in self.WEB_SEARCH_TRIGGERS:
            if trigger in query:
                return True
        
        # Check keywords
        web_keywords = {
            'documentation', 'library', 'framework', 'package', 'api',
            'example', 'github', 'stackoverflow', 'package'
        }
        
        return bool(web_keywords.intersection(set(keywords)))
    
    def _needs_current_info(self, query: str) -> bool:
        """Check if query requires up-to-date information"""
        temporal_indicators = [
            'latest', 'current', 'recent', 'now', 'today',
            '2024', '2025', 'this year', 'update', 'news'
        ]
        return any(ind in query for ind in temporal_indicators)
    
    def _calculate_complexity(self, query: str, keywords: List[str]) -> float:
        """Calculate query complexity (0.0 to 1.0)"""
        complexity = 0.0
        
        # Length factor
        word_count = len(query.split())
        complexity += min(word_count / 50, 0.3)  # Max 0.3 for length
        
        # Keyword density
        complexity += min(len(keywords) / 15, 0.3)  # Max 0.3 for keywords
        
        # Multi-part questions
        if '?' in query:
            question_count = query.count('?')
            complexity += min(question_count * 0.15, 0.2)
        
        # Technical terms
        technical_terms = [
            'api', 'framework', 'algorithm', 'optimize', 'async',
            'architecture', 'database', 'deployment', 'performance'
        ]
        tech_count = sum(1 for term in technical_terms if term in query.lower())
        complexity += min(tech_count * 0.05, 0.2)
        
        return min(complexity, 1.0)
    
    def _suggest_tools(
        self, 
        query_type: QueryType, 
        needs_web: bool,
        query: str
    ) -> List[str]:
        """Suggest which tools should be used"""
        tools = []
        
        # Web search for most information-seeking queries
        if needs_web or query_type in [
            QueryType.FACTUAL, QueryType.RECOMMENDATION, 
            QueryType.HOW_TO, QueryType.COMPARISON,
            QueryType.TEMPORAL, QueryType.RESOURCE
        ]:
            tools.append('web_search')
        
        # File tools for coding
        if query_type == QueryType.CODING:
            if 'read' in query or 'check' in query:
                tools.extend(['list_files', 'read_file'])
            if 'create' in query or 'write' in query:
                tools.append('create_file')
            if 'fix' in query or 'debug' in query:
                tools.extend(['fast_grep', 'edit_file'])
        
        # Bash for system operations
        if any(word in query for word in ['run', 'execute', 'install', 'command']):
            tools.append('bash')
        
        # Memory for learning/recall
        if any(word in query for word in ['remember', 'recall', 'learned', 'past']):
            tools.append('memory')
        
        # Default to web_search if no tools suggested
        if not tools and query_type != QueryType.CONVERSATIONAL:
            tools.append('web_search')
        
        return tools
    
    def _generate_reasoning(
        self,
        query_type: QueryType,
        needs_web: bool,
        tools: List[str]
    ) -> str:
        """Generate explanation for tool suggestions"""
        reasons = []
        
        if needs_web:
            reasons.append("Query requires current/factual information")
        
        if query_type == QueryType.RECOMMENDATION:
            reasons.append("User seeking recommendations (needs web search)")
        elif query_type == QueryType.HOW_TO:
            reasons.append("Tutorial request (needs current best practices)")
        elif query_type == QueryType.COMPARISON:
            reasons.append("Comparison query (needs up-to-date data)")
        elif query_type == QueryType.CODING:
            reasons.append("Coding task (may need file operations)")
        
        if 'web_search' in tools:
            reasons.append("web_search recommended for grounded response")
        
        return "; ".join(reasons) if reasons else "General query"
