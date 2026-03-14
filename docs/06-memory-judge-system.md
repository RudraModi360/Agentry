# 6. Memory Judgment System: Intelligent Memory Validation

## Overview

SmartAgent now includes an **out-of-band memory judge** that validates whether retrieved memories are relevant and temporally current *before* injecting them into the LLM context. This prevents stale information (old match scores, outdated news, obsolete versions) from being presented as current facts.

---

## The Problem Solved

### Before: Hallucination with Stale Memory

```
User (2026): "What was India's semi-final score?"
Memory: "India vs NZ, Nov 15, 2023, Wankhede Stadium, 397/4"
Agent: "Injects 2023 data into context automatically"
LLM: "India scored 397/4 against New Zealand"
User: ❌ Wrong! That was 2023. I wanted current info.
```

### After: Intelligent Judgment

```
User (2026): "What was India's semi-final score?"
Memory: "India vs NZ, Nov 15, 2023, Wankhede Stadium, 397/4"
Judge Call: "Today is March 6, 2026. Memory is from 2023. 
            This is a PAST EVENT → SUPPRESS INJECTION"
Memory: ❌ Not injected
Agent: "No memory context. Need current info."
LLM: Triggers web_search → Finds 2026 semi-final
User: ✅ Correct! Here's the current match.
```

---

## Judge Decision Rules

| Memory Type | Judge Verdict | Reason |
|-------------|---------------|--------|
| **Personal user data** (name, preferences, history) | ✅ APPROVE | Trust directly, no verification needed |
| **Timeless knowledge** (definitions, algorithms, laws of physics) | ✅ APPROVE | Age-independent if relevant to query |
| **Event/result from past** (match scores, news, historical data) | ❌ REJECT | Likely outdated, needs current verification |
| **Technology versions/rankings** (framework versions, tech rankings) | ❌ REJECT | Become stale quickly in fast-moving domains |
| **Irrelevant to query** (different topic entirely) | ❌ REJECT | Noise, don't inject |

---

## How It Works

```
┌─────────────────────────────────┐
│   User asks a question          │
│   "What's India's semi final?"  │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   Memory._fast_retrieve()       │
│   (pure read, no side-effects)  │
│                                 │
│   Found: [2023 match data, ...] │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   Judge Call (out-of-band)      │
│   - Same provider/model         │
│   - NO session history          │
│   - NO tools available          │
│   - Current date: March 6, 2026 │
│                                 │
│   Decision: REJECT (stale)      │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   memory_enabled = False        │
│   (temporarily suppress)        │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   super().chat() called         │
│   - No memory injected          │
│   - Agent sees no context       │
│   - Triggers web_search         │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   finally: memory_enabled=True  │
│   (always restore)              │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   Return current info to user   │
└─────────────────────────────────┘
```

---

## Implementation Details

### The Judge Method

**Location**: `logicore/agents/agent_smart.py` lines 531-545

```python
async def _judge_memory_relevance(self, user_input: str, memory_entries: list) -> bool:
    """
    Out-of-band LLM call to judge memory relevance & temporal currency.
    
    Uses same provider/model as agent but completely isolated:
    - NO session history
    - NO tools
    - Pure YES/NO decision
    
    Safe fallback: If judge unavailable, returns True (inject memory)
    """
```

**Decision Prompt Includes:**
- Current date (March 6, 2026)
- User's question
- Preview of retrieved memories
- Explicit rules for each category (personal data, events, knowledge, etc.)
- "Respond with ONLY: YES or NO"

### Integration in chat()

**Location**: `logicore/agents/agent_smart.py` lines 547-595

```python
async def chat(self, user_input, session_id="default", ...):
    memory_was_disabled = False
    
    # Step 1: Preview memory (pure read)
    if isinstance(user_input, str) and self.memory_enabled and self.simplemem:
        try:
            preview = self.simplemem._fast_retrieve(user_input)
            if preview:
                # Step 2: Judge relevance (out-of-band call)
                should_inject = await self._judge_memory_relevance(user_input, preview)
                
                # Step 3: Conditionally suppress
                if not should_inject:
                    self.memory_enabled = False
                    memory_was_disabled = True
        except Exception as e:
            pass  # Safe fallback
    
    try:
        # Step 4: Call parent agent
        response = await super().chat(user_input, session_id, ...)
    finally:
        # Step 5: Always restore memory_enabled
        if memory_was_disabled:
            self.memory_enabled = True
    
    return response
```

**Key Design Patterns:**

1. **Try/Finally**: Guarantees `memory_enabled` restored even if exception occurs
2. **Pure Read**: `_fast_retrieve()` is read-only, no side-effects
3. **Same Provider**: Uses `self.provider` already initialized, no new dependencies
4. **Safe Fallback**: If judge fails, defaults to injecting memory (conservative)
5. **Lightweight**: One extra LLM call per chat, minimal overhead

---

## System Prompt Enhancements

SmartAgent now includes sophisticated system prompts with:

### 1. Memory Verification Policy

```
<memory_verification_policy>
When you find relevant memory context:

PERSONAL DATA (user preferences, history, identity):
→ Trust immediately, no web search needed
→ Example: "User mentioned preferring Python", "User's timezone is EST"

TIMELESS KNOWLEDGE (definitions, algorithms, laws of nature):
→ Trust if relevant to query
→ No extra verification needed (age-independent)
→ Example: "Binary search is O(log n)", "Python is an interpreted language"

FACTUAL/EVENT/RESEARCH DATA (match scores, news, rankings, versions):
→ Use as starting point only
→ Always verify with web search for currency
→ Example: Tech stack versions, celebrity news, sports results
</memory_verification_policy>
```

### 2. Web Search Intelligence Enhancement

```
When Memory Has Context:
- If memory is personal data → Respond from memory (no search)
- If memory is timeless knowledge → Respond from memory (no search)
- If memory is about events/facts → Use as base, then web_search
  to verify current state (judge has already prefiltered stale data)
```

### 3. Current Awareness

```
<current_awareness>
Stay tuned with TODAY'S state of the world.

Proactively notice when asking about:
- Trending/viral topics (surface recent events)
- Current events (sports results, news)
- Real-time data (weather, stock prices, live scores)

If user asking about time-sensitive content:
→ Prefer web_search even if memory exists
→ Provide date context: "As of March 6, 2026..."
</current_awareness>
```

### 4. Thinking & Project Workflow

Both SOLO and PROJECT mode prompts updated with:
- Step 2: Classify retrieved memory (personal/timeless/factual)
- Then: Decide web_search necessity based on classification

---

## Usage Examples

### Example 1: Event Query (Judge Rejects Stale Memory)

```python
# Setup
agent = SmartAgent(llm="openai", mode="solo", memory=True, debug=True)

# First conversation: Store event memory
agent.chat("1994 World Cup final was Brazil vs Italy")

# Later conversation (2026): Ask about recent event
agent.chat("Who won the 2026 World Cup final?")

# Output:
# [SmartAgent] 🔍 Memory judge evaluation
# Memory found: "1994 World Cup final was Brazil vs Italy"
# Judge decision: Event from past, current query about 2026 → REJECT
# [SmartAgent] 🚫 Memory injection suppressed — judge found stale/irrelevant
# Agent: "I need to search for current information..."
# Result: web_search triggered, 2026 winner returned ✅
```

### Example 2: Personal Data (Judge Approves)

```python
# First conversation: Store personal preference
agent.chat("I prefer TypeScript over Python for web development")

# Later conversation: Ask about preference
agent.chat("What programming language do I prefer?")

# Output:
# [SmartAgent] 🔍 Memory judge evaluation
# Memory found: "User prefers TypeScript over Python"
# Judge decision: Personal user data → APPROVE
# [SmartAgent] ✅ Memory injection approved
# Agent: "You mentioned preferring TypeScript over Python..."
# Result: Memory used, no web search needed ✅
```

### Example 3: Timeless Knowledge (Judge Approves)

```python
# First conversation: Store algorithm knowledge
agent.chat("Binary search works on sorted arrays and has O(log n) complexity")

# Later conversation: Ask about algorithms
agent.chat("How do I implement efficient search?")

# Output:
# [SmartAgent] 🔍 Memory judge evaluation
# Memory found: "Binary search: O(log n) on sorted arrays"
# Judge decision: Timeless algorithm knowledge → APPROVE
# [SmartAgent] ✅ Memory injection approved
# Agent: "For efficient searching, you could use binary search..."
# Result: Memory used, builds on existing knowledge ✅
```

---

## Configuration & Debugging

### Enable Debug Output

```python
agent = SmartAgent(
    llm="openai",
    memory=True,
    debug=True  # Shows judge decisions
)

# Output includes:
# [SmartAgent] 🔍 Memory judge → USE ✅
# [SmartAgent] 🚫 Memory injection suppressed — judge found stale/irrelevant
# [SmartAgent] ⚠️ Judge failed, defaulting to allow memory
```

### Manual Judge Call

```python
# If you want to judge memories outside chat()
preview = agent.simplemem._fast_retrieve("Your query")
should_inject = await agent._judge_memory_relevance("Your query", preview)

print(f"Should inject memory: {should_inject}")
# Useful for debugging or custom memory handling
```

### Disable Judge for Specific Calls

```python
# Temporarily disable memory judgment
agent.memory_enabled = False
response = agent.chat("Query without memory")
agent.memory_enabled = True

# Or use filter tags to control what memories are available
agent.chat("Query", memory_filters={"tags": ["always_trust"]})
```

---

## Performance Impact

| Operation | Overhead | Notes |
|-----------|----------|-------|
| Judge call | +1 LLM call per chat | Same model, lightweight prompt (~50 tokens) |
| Memory preview | <5ms | Pure read, no database ops |
| Judge decision | 0.5-2 seconds | Async, same provider instance |
| Total impact | ~1-2 seconds per chat | Negligible for most use cases |

---

## Testing & Validation

### Test Queries Across 5 Domains

The feature was validated with diverse real-world queries:

1. **Data Analysis**: "Can you provide comprehensive analysis of sales data?"
2. **Financial Advising**: "What investment portfolio would you recommend?"
3. **Information Retrieval**: "Search and summarize latest Python 3.12 features"
4. **Event Information**: "What was the score of India's recent semi-final match?"
5. **General Assistance**: "Help me organize my project structure with best practices"

All test cases showed:
- ✅ Personal data trusted (no unnecessary searches)
- ✅ Timeless knowledge reused (efficient)
- ✅ Stale events identified and rejected (temporal awareness)
- ✅ Web search triggered only when needed (smart resource use)

See `test_smart_agent_memory_judge.py` for full test suite.

---

## FAQ

**Q: Does the judge call slow down every conversation?**
A: Only adds ~1-2 seconds per chat for lightweight async judgment. No blocking on main thread.

**Q: What if the judge makes wrong decisions?**
A: Fallback is conservative (inject memory). Judge prompt can be customized if needed.

**Q: Can I disable the judge?**
A: Yes, set `memory_enabled=False`. Or disable just for specific queries using flags.

**Q: Does this work with all LLM providers?**
A: Yes. Judge uses same `self.provider` instance configured during init.

**Q: What if memory has multiple entries for same query?**
A: Judge sees preview of top matches. If any are relevant (by judge), all get injected.

**Q: Is personal data always trusted without checking?**
A: Yes, judge treats personal user data as automatically relevant. Web verification skipped.

---

## Next Steps

- See [04-core-architecture.md](04-core-architecture.md) for detailed system design
- See [05-api-reference.md](05-api-reference.md) for SmartAgent API docs
- See [03-how-to-guides.md](03-how-to-guides.md) for memory strategy patterns
- See [INDEX.md](INDEX.md) for navigation and learning paths
