# Multi-Provider Patterns

Master switching between LLMs without changing your code.

---

## Pattern 1: Provider Factory

Dynamically choose providers:

```python
from logicore import Agent
from logicore.providers import (
    OpenAIProvider,
    GroqProvider,
    OllamaProvider,
    GeminiProvider,
    AnthropicProvider,
)

class ProviderFactory:
    """Factory for creating providers on demand."""
    
    providers = {
        "openai": lambda: OpenAIProvider(model="gpt-4"),
        "groq": lambda: GroqProvider(model="llama-3.3-70b-versatile"),
        "ollama": lambda: OllamaProvider(model="llama3.2"),
        "gemini": lambda: GeminiProvider(model="gemini-2.0-flash"),
        "claude": lambda: AnthropicProvider(model="claude-3-sonnet"),
    }
    
    @classmethod
    def get_provider(cls, name: str):
        """Get provider by name."""
        if name not in cls.providers:
            raise ValueError(f"Unknown provider: {name}")
        return cls.providers[name]()

# Usage
for provider_name in ["groq", "ollama", "gemini"]:
    provider = ProviderFactory.get_provider(provider_name)
    agent = Agent(provider=provider)
    response = agent.chat("Hello!")
    print(f"{provider_name}: {response}")
```

---

## Pattern 2: Cost-Aware Routing

Route queries based on cost:

```python
from logicore import Agent
from logicore.providers import GroqProvider, OpenAIProvider

class CostAwareAgent:
    """Route expensive queries differently."""
    
    def __init__(self):
        self.cheap = GroqProvider(model="llama-3.3-70b")        # Free
        self.powerful = OpenAIProvider(model="gpt-4")           # Expensive
    
    def chat(self, query: str, budget: str = "low") -> str:
        """Chat with cost awareness."""
        
        # Simple queries → cheap provider
        if budget == "low" or len(query) < 50:
            agent = Agent(provider=self.cheap)
            return agent.chat(query)
        
        # Complex queries → powerful provider
        else:
            agent = Agent(provider=self.powerful)
            return agent.chat(query)

# Usage
router = CostAwareAgent()

# Simple query → Groq (free, fast)
response = router.chat("What's 2+2?", budget="low")

# Complex query → GPT-4 (better reasoning)
response = router.chat("""
Design a microservices architecture for a startup with
1000 DAU, strong consistency requirements, and limited budget
""", budget="high")
```

---

## Pattern 3: Latency-Optimized

Choose based on speed requirements:

```python
from logicore import Agent
from logicore.providers import (
    GroqProvider,        # Fastest (~100ms)
    OllamaProvider,      # Medium (~300ms)
    OpenAIProvider,      # Variable (~200-500ms)
)
import time

class LatencyOptimizedAgent:
    """Minimize response latency."""
    
    def __init__(self):
        self.fast = GroqProvider(model="llama-3.3-70b")
        self.medium = OllamaProvider(model="llama3.2")
        self.fallback = OpenAIProvider(model="gpt-4")
    
    def chat(self, query: str, max_latency_ms: int = 100) -> str:
        """Return within latency budget if possible."""
        
        providers = [self.fast, self.medium, self.fallback]
        
        for provider in providers:
            start = time.time()
            agent = Agent(provider=provider)
            
            try:
                response = agent.chat(query)
                elapsed = (time.time() - start) * 1000
                
                if elapsed <= max_latency_ms:
                    return response
            except:
                continue
        
        return "All providers unavailable"

# Usage
agent = LatencyOptimizedAgent()

# For real-time apps (chat, autocomplete)
response = agent.chat("Quick response needed", max_latency_ms=100)

# For background jobs (analysis, reports)
response = agent.chat("Complex analysis", max_latency_ms=5000)
```

---

## Pattern 4: Quality-Tiered

Use best model when accuracy matters:

```python
from logicore import Agent
from logicore.providers import (
    GroqProvider,
    GeminiProvider,
    OpenAIProvider,
)

class QualityTieredAgent:
    """Quality-based provider selection."""
    
    # Tier 1: Draft/Quick feedback
    draft = GroqProvider(model="llama-3.3-70b")
    
    # Tier 2: Production
    production = GeminiProvider(model="gemini-2.0-flash")
    
    # Tier 3: Critical/High-stakes
    expert = OpenAIProvider(model="gpt-4")
    
    @classmethod
    def chat(cls, query: str, quality: str = "production") -> str:
        """Get response at specific quality level."""
        
        providers = {
            "draft": cls.draft,
            "production": cls.production,
            "expert": cls.expert,
        }
        
        provider = providers.get(quality, cls.production)
        agent = Agent(provider=provider)
        return agent.chat(query)

# Usage

# For brainstorming
response = QualityTieredAgent.chat(
    "Generate ideas for...",
    quality="draft"
)

# For normal use
response = QualityTieredAgent.chat(
    "Analyze the following...",
    quality="production"
)

# For medical/legal/financial
response = QualityTieredAgent.chat(
    "Critical analysis needed...",
    quality="expert"
)
```

---

## Pattern 5: Fallback/Failover

Gracefully handle provider failures:

```python
from logicore import Agent
from logicore.providers import (
    GroqProvider,
    OllamaProvider,
    OpenAIProvider,
)

class FailoverAgent:
    """Try providers in order until one works."""
    
    def __init__(self):
        self.providers_chain = [
            GroqProvider(model="llama-3.3-70b"),  # Fastest
            OllamaProvider(model="llama3.2"),     # Fallback 1
            OpenAIProvider(model="gpt-4"),        # Fallback 2
        ]
    
    def chat(self, query: str) -> str:
        """Try each provider until success."""
        
        for i, provider in enumerate(self.providers_chain):
            try:
                print(f"[{i+1}] Trying provider {provider.__class__.__name__}...")
                agent = Agent(provider=provider)
                response = agent.chat(query)
                print(f"✓ Success!")
                return response
            
            except Exception as e:
                print(f"✗ Failed: {e}")
                if i == len(self.providers_chain) - 1:
                    return "All providers failed"
                continue

# Usage
agent = FailoverAgent()
response = agent.chat("Hello!")

# Output:
# [1] Trying provider GroqProvider...
# ✓ Success!
# Response: ...

# If Groq fails:
# [1] Trying provider GroqProvider...
# ✗ Failed: Connection refused
# [2] Trying provider OllamaProvider...
# ✓ Success!
```

---

## Pattern 6: Provider Benchmark

Compare providers for your use case:

```python
import time
from logicore import Agent
from logicore.providers import (
    GroqProvider,
    OllamaProvider,
    GeminiProvider,
)

class ProviderBenchmark:
    """Benchmark providers."""
    
    @staticmethod
    def benchmark(query: str, providers_list: list):
        """Run benchmarks and show results."""
        
        results = {}
        
        for provider in providers_list:
            try:
                agent = Agent(provider=provider)
                
                # Measure latency
                start = time.time()
                response = agent.chat(query)
                latency = time.time() - start
                
                # Measure response length
                response_length = len(response)
                
                provider_name = provider.__class__.__name__
                results[provider_name] = {
                    "latency_ms": latency * 1000,
                    "response_length": response_length,
                    "sample": response[:100] + "..."
                }
            except Exception as e:
                results[provider.__class__.__name__] = {"error": str(e)}
        
        return results

# Usage
query = "Explain quantum computing in 100 words"

providers = [
    GroqProvider(model="llama-3.3-70b"),
    OllamaProvider(model="llama3.2"),
    GeminiProvider(model="gemini-2.0-flash"),
]

results = ProviderBenchmark.benchmark(query, providers)

for provider_name, metrics in results.items():
    print(f"\n{provider_name}:")
    if "error" in metrics:
        print(f"  Error: {metrics['error']}")
    else:
        print(f"  Latency: {metrics['latency_ms']:.0f}ms")
        print(f"  Response length: {metrics['response_length']} chars")

# Output:
# GroqProvider:
#   Latency: 145ms
#   Response length: 215 chars
# 
# OllamaProvider:
#   Latency: 320ms
#   Response length: 218 chars
# 
# GeminiProvider:
#   Latency: 280ms
#   Response length: 220 chars
```

---

## Pattern 7: A/B Testing

Compare provider outputs for same query:

```python
from logicore import Agent
from logicore.providers import GroqProvider, GeminiProvider

class ABTester:
    """Compare outputs from different providers."""
    
    def __init__(self):
        self.provider_a = GroqProvider(model="llama-3.3-70b")
        self.provider_b = GeminiProvider(model="gemini-2.0-flash")
    
    def compare(self, query: str) -> dict:
        """Get same query from both providers."""
        
        agent_a = Agent(provider=self.provider_a)
        agent_b = Agent(provider=self.provider_b)
        
        response_a = agent_a.chat(query)
        response_b = agent_b.chat(query)
        
        return {
            "provider_a": response_a,
            "provider_b": response_b,
            "differences": self._compute_diff(response_a, response_b)
        }
    
    @staticmethod
    def _compute_diff(text_a: str, text_b: str) -> dict:
        """Compare responses."""
        return {
            "length_a": len(text_a),
            "length_b": len(text_b),
            "similarity": "similar" if text_a[:100] == text_b[:100] else "different"
        }

# Usage
tester = ABTester()

results = tester.compare("""
You are a technical writer. Explain REST API design in 3 sentences.
""")

print("Provider A (Groq):")
print(results["provider_a"])
print("\nProvider B (Gemini):")
print(results["provider_b"])
print("\nDifferences:")
print(results["differences"])
```

---

## Pattern 8: Load Balancing

Distribute queries across providers:

```python
from logicore import Agent
from logicore.providers import GroqProvider, OllamaProvider
import random

class LoadBalancedAgent:
    """Distribute load across providers."""
    
    def __init__(self):
        self.providers = [
            GroqProvider(model="llama-3.3-70b"),
            GroqProvider(model="llama-3.3-70b"),  # 2 instances
            OllamaProvider(model="llama3.2"),
        ]
        self.request_count = 0
    
    def chat(self, query: str) -> str:
        """Balance requests across providers."""
        
        # Round-robin or random selection
        provider = self.providers[self.request_count % len(self.providers)]
        # Or: provider = random.choice(self.providers)
        
        agent = Agent(provider=provider)
        response = agent.chat(query)
        self.request_count += 1
        
        return response

# Usage
lb_agent = LoadBalancedAgent()

# Requests distributed:
# Request 1 → Groq instance 1
# Request 2 → Groq instance 2
# Request 3 → Ollama
# Request 4 → Groq instance 1 (cycles)

for i in range(6):
    response = lb_agent.chat(f"Request {i+1}")
```

---

## Choosing the Right Pattern

| Pattern | When to Use |
|---------|-----------|
| **Factory** | Need flexibility to switch providers |
| **Cost-Aware** | Budget constraints, mixed workloads |
| **Latency-Optimized** | Real-time, user-facing applications |
| **Quality-Tiered** | Different quality needs for different tasks |
| **Failover** | Reliability-critical applications |
| **Benchmark** | Evaluating which provider works best |
| **A/B Test** | Comparing provider outputs |
| **Load Balanced** | High-traffic, distributed systems |

---

## Complete Example: Production Agent

```python
from logicore import Agent
from logicore.providers import (
    GroqProvider,
    OllamaProvider,
    OpenAIProvider,
)

class ProductionAgent:
    """Production-grade multi-provider agent."""
    
    def __init__(self):
        # Fast for simple queries
        self.fast_provider = GroqProvider(model="llama-3.3-70b")
        
        # Fallback
        self.fallback_provider = OllamaProvider(model="llama3.2")
        
        # High-stakes
        self.expert_provider = OpenAIProvider(model="gpt-4")
    
    def chat(self, query: str, priority: str = "normal") -> str:
        """Smart routing based on priority."""
        
        if priority == "low":
            provider = self.fast_provider
        elif priority == "high":
            provider = self.expert_provider
        else:
            provider = self.fast_provider
        
        try:
            agent = Agent(provider=provider, memory=True)
            return agent.chat(query)
        except Exception as e:
            # Fallback
            agent = Agent(provider=self.fallback_provider)
            return agent.chat(query)

# Usage
app = ProductionAgent()

# Routine query
response = app.chat("What's 2+2?", priority="low")

# Complex task
response = app.chat(
    "Design architecture for distributed system",
    priority="high"
)
```

---

## Next Steps

- [Your First Agent](your-first-agent.md)
- [Tool Integration](tool-integration.md)
- [Production Deployment](production-deployment.md)
