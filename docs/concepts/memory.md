# Memory: Persistent Agent Learning

Memory is what makes agents truly powerful. **Without memory, agents are just chatbots.**

---

## The Memory Problem

Imagine a consultant who shows up every day with zero memory.

You explain your situation: "We're a Python/React startup, 10 engineers, building an AI assistant."

The consultant helps you build architecture, make decisions, write code.

Next day: consultant returns completely blank. You explain everything again. Again and again.

**This is an agent without memory.**

---

## The Solution: Persistent Memory

Logicore agents automatically remember:

```python
agent = Agent(memory=True)

# Session 1
agent.chat("My company uses Python and React for our stack")
agent.chat("We have 10 engineers. How should we structure our repos?")

# Later... completely new process
agent2 = Agent(memory=True)

# Session 2
response = agent2.chat("What tech stack does my company use?")
# Output: "Your company uses Python and React"

response = agent2.chat("How many engineers does my company have?")
# Output: "Your company has 10 engineers"
```

No configuration needed. It just works.

---

## How Memory Works

### Step 1: Receive Input
```python
agent.chat("I'm frustrated with performance issues")
```

### Step 2: Agent Searches Memory
```
Search: "Is this related to anything I've learned before?"
Found: Previous "performance optimization" conversations
Relevant? Yes! Similar context
```

### Step 3: Retrieve & Inject Context
```
Memory insight: "Last time user had performance issues, it was 
query optimization. They use PostgreSQL. Fixed with indexing."
```

### Step 4: LLM Uses Context
```
LLM prompt now includes memory context
→ "The user had similar issues before..."
→ Makes smarter decision with context
```

### Step 5: Store New Information
```
After responding, new facts are stored:
- "User experiencing performance issues again"
- "Mentioned N+1 queries in code"
- Store in memory for future reference
```

---

## Memory Types

### Session Memory (Default)
Short-term, within one chat session:

```python
agent = Agent()

agent.chat("My name is Alice")
agent.chat("What's my name?")  # Alice (in memory)
response = agent.chat("What's my name?")  # Alice, still in memory

# But next process:
agent2 = Agent()
response = agent2.chat("What's my name?")  # No memory, blank
```

### Persistent Memory (Recommended)
Long-term, across sessions and processes:

```python
agent = Agent(memory=True)

# Session 1
agent.chat("My name is Alice")
agent.chat("I build AI systems")

# Kill the process, restart later
agent2 = Agent(memory=True)

# Session 2
response = agent2.chat("What's my name?")
# Output: "Alice"

response = agent2.chat("What do you know about me?")
# Output: "You build AI systems"
```

---

## Enabling Memory

### Local (File-Based)
```python
agent = Agent(
    memory=True,  # Uses local SQLite by default
)

# Memory stored in: ~/.logicore/memory/
```

### Custom Storage
```python
agent = Agent(
    memory_provider="pinecone",  # Vector database
    memory_config={
        "api_key": "...",
        "index": "my-agents"
    }
)
```

### Disable Memory
```python
agent = Agent(memory=False)  # No persistence
```

---

## Memory in Practice

### Use Case 1: Multi-turn Conversation
```python
agent = Agent(memory=True)

# Turn 1
agent.chat("I'm learning machine learning")

# Turn 2
response = agent.chat("Can you recommend resources for beginners?")
# Remembers: User is learning ML
# Adapts: Recommends beginner-friendly resources

# Turn 3
response = agent.chat("I've mastered the basics. What's next?")
# Remembers: User is now past basics
# Adapts: Recommends intermediate resources
```

### Use Case 2: Customer Support
```python
conversation_history = []
agent = Agent(memory=True, role="customer_support")

# User: Day 1
agent.chat("I have an issue with order #123")
agent.chat("I need a refund")

# User: Day 7 (forgot about their issue)
response = agent.chat("Can you help me?")
# Remembers: This user had order issue #123
# Mentions: "I see you had an issue with order #123. How can I help?"
```

### Use Case 3: Research Agent
```python
agent = Agent(memory=True, role="researcher")

# Query 1
agent.chat("Find information about quantum computing")

# Query 2
response = agent.chat("What about practical applications?")
# Remembers: Context on quantum computing
# Skips: Redundant background, focuses on applications

# Query 3
response = agent.chat("Compare with classical computing")
# Remembers: Both quantum AND classical contexts
# Provides: Informed comparison
```

### Use Case 4: Onboarding
```python
agent = Agent(memory=True, role="onboarding_manager")

# Week 1
agent.chat("I'm new to the company")
agent.chat("Tell me about our tech stack")
agent.chat("Who are the team leads?")

# Week 4
agent.chat("I remember learning about Python. Who specializes in it?")
# Remembers: User learned about Python in week 1
# Connects: With team info learned earlier
# Answers: "John and Sarah specialize in Python"
```

---

## Managing Memory

### View Memory
```python
agent = Agent(memory=True)
agent.chat("My favorite color is blue")

# Retrieve stored memories
memories = agent.memory.search("color")
for memory in memories:
    print(memory)
    # Output: "User's favorite color is blue"
```

### Clear Memory
```python
agent = Agent(memory=True)
agent.memory.clear()  # Forget everything

# Or selective clear
agent.memory.clear_topic("old_conversati")
```

### Export Memory
```python
agent = Agent(memory=True)
memories = agent.memory.export()
print(memories)  # JSON or CSV
```

### Import Memory
```python
agent = Agent(memory=True)
agent.memory.import_from_file("memories.json")
```

---

## Memory Configuration

### Importance Threshold
```python
agent = Agent(
    memory=True,
    memory_importance_threshold=0.5  # Only store important facts
)

# Stores: "User has 10 years experience" (high importance)
# Ignores: "User mentioned it's Tuesday" (low importance)
```

### Retention Policy
```python
agent = Agent(
    memory=True,
    memory_retention_days=90  # Forget after 90 days
)

# Old memories automatically expire
```

### Maximum Memory Size
```python
agent = Agent(
    memory=True,
    memory_max_size_mb=500  # Limit memory to 500MB
)
```

---

## Memory Best Practices

✅ **DO:**
- Enable memory for production agents
- Periodically export memories for backup
- Clear memory if starting fresh with different context
- Use memory for personalization
- Monitor memory growth

❌ **DON'T:**
- Rely on session memory alone in production
- Leave memory unbounded (set retention limits)
- Store sensitive data without encryption
- Mix unrelated conversations in same memory
- Disable memory for customer-facing agents

---

## Memory Under the Hood

### Vector Storage
Memories stored as embeddings in vector database:

```
User input: "I like Python"
           ↓
        Embed
           ↓
Stored as vector: [0.123, 0.456, ...]
           ↓
Later search: "What languages do you know?"
           ↓
        Embed
           ↓
Find similar: [0.125, 0.458, ...] ← Very similar!
           ↓
Retrieve: "I like Python"
```

### Similarity Matching
Only relevant memories surface:

```python
agent.chat("What's my career background?")

# Memory search finds related items:
# - "10 years as software engineer" (98% similar)
# - "CTO at TechCorp" (97% similar)
# - "I like Python" (42% similar - not retrieved)

# Result: Focused, relevant context
```

---

## Privacy & Security

### Data Storage
- By default: encrypted SQLite locally on your machine
- No data sent to cloud unless you choose a cloud provider

### Opt-in Cloud Storage
```python
# Local (secure, no cloud)
agent = Agent(memory=True)

# or Pinecone (cloud, encrypted in transit)
agent = Agent(memory_provider="pinecone")

# or Your own database
agent = Agent(memory_provider="custom", memory_endpoint="...")
```

### Compliance
- GDPR: Memories can be exported/deleted on request
- CCPA: User has right to access and delete
- SOC2: Use local storage for compliance

---

## Examples

### Personal Assistant
```python
agent = Agent(memory=True, role="personal_assistant")

# Day 1
agent.chat("Remind me: I'm vegetarian")
agent.chat("My wife's name is Sarah")

# Day 30
agent.chat("Plan a dinner")
# Remembers: User is vegetarian
# Remembers: Wife is Sarah
# Plans: Vegetarian dinner with both preferences
```

### Project Manager
```python
agent = Agent(memory=True, role="project_manager")

# Week 1
agent.chat("Starting project X with team of 5")
agent.chat("Budget is $50k")

# Week 5
agent.chat("Can we take on more work?")
# Remembers: Project X budget
# Remembers: Team size
# Answers: "Depends on current capacity"
```

### Learning Tutor
```python
agent = Agent(memory=True, role="tutor")

# Lesson 1
agent.chat("I'm learning Python basics")
agent.chat("Explain variables")

# Lesson 5
agent.chat("Explain decorators")
# Remembers: Already learned basics
# Adapts: Teaches decorators in context of what you know
# Skips: Redundant basics
```

---

## Next Steps

- [Agents](agents.md) — Core agent architecture
- [Tools](tools.md) — Combine tools + memory
- [Guides: Memory Management](../../guides/memory-management.md) — Real examples
