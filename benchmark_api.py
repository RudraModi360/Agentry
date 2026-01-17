"""
Performance benchmark script to measure API response times.
Run: python benchmark_api.py
"""
import time
import httpx
import statistics

BASE_URL = "http://localhost:8000"
# You need to get a valid token from the browser
AUTH_TOKEN = None  # Will skip auth-required endpoints if None

def benchmark_endpoint(client, method, path, iterations=10, **kwargs):
    """Benchmark a single endpoint."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        if method == "GET":
            response = client.get(f"{BASE_URL}{path}", **kwargs)
        elif method == "POST":
            response = client.post(f"{BASE_URL}{path}", **kwargs)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    
    return {
        "min": min(times),
        "max": max(times),
        "avg": statistics.mean(times),
        "median": statistics.median(times),
        "p95": sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
        "status": response.status_code
    }

def main():
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    client = httpx.Client(timeout=30.0, headers=headers)
    
    print("=" * 60)
    print("Backend API Performance Benchmark")
    print("=" * 60)
    print()
    
    # Public endpoints
    print("Testing public endpoints (no auth)...")
    print("-" * 40)
    
    result = benchmark_endpoint(client, "GET", "/api/providers")
    print(f"GET /api/providers:")
    print(f"  Avg: {result['avg']:.2f}ms | Min: {result['min']:.2f}ms | Max: {result['max']:.2f}ms")
    
    if AUTH_TOKEN:
        print()
        print("Testing authenticated endpoints...")
        print("-" * 40)
        
        result = benchmark_endpoint(client, "GET", "/api/sessions")
        print(f"GET /api/sessions:")
        print(f"  Avg: {result['avg']:.2f}ms | Min: {result['min']:.2f}ms | Max: {result['max']:.2f}ms")
        
        result = benchmark_endpoint(client, "GET", "/api/provider/current")
        print(f"GET /api/provider/current:")
        print(f"  Avg: {result['avg']:.2f}ms | Min: {result['min']:.2f}ms | Max: {result['max']:.2f}ms")
        
        result = benchmark_endpoint(client, "GET", "/api/tools")
        print(f"GET /api/tools:")
        print(f"  Avg: {result['avg']:.2f}ms | Min: {result['min']:.2f}ms | Max: {result['max']:.2f}ms")
    else:
        print()
        print("Skipping authenticated endpoints (no AUTH_TOKEN set)")
        print("To test authenticated endpoints, set AUTH_TOKEN in this script")
    
    print()
    print("=" * 60)
    print("Benchmark complete!")
    
    client.close()

if __name__ == "__main__":
    main()
