"""
Backend API Test Script
========================
Tests the modularized backend routes:
1. Login with existing user (Rudra/123456)
2. Logout
3. Signup with existing and new credentials
4. Test agent endpoints

Run with: python tests/test_backend_api.py
"""

import requests
import json
import time
import os

# Configuration
BASE_URL = "http://localhost:8000"

# Test credentials
EXISTING_USER = {"username": "Rudra", "password": "123456"}
NEW_USER = {"username": "TestUser_" + str(int(time.time())), "password": "test123"}

# Store results
results = []
auth_token = None
user_info = None


def log_result(test_name: str, success: bool, message: str, response_data=None):
    """Log test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    results.append({
        "test": test_name,
        "success": success,
        "message": message,
        "response": response_data
    })
    print(f"\n{status} | {test_name}")
    print(f"   └─ {message}")
    if response_data and not success:
        print(f"   └─ Response: {json.dumps(response_data, indent=2)[:500]}")


def test_health_check():
    """Test if the server is running."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code in [200, 302, 307]:
            log_result("Health Check", True, f"Server is running. Status: {response.status_code}")
            return True
        else:
            log_result("Health Check", False, f"Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        log_result("Health Check", False, f"Server not reachable: {str(e)}")
        return False


def test_login(username: str, password: str):
    """Test login endpoint."""
    global auth_token, user_info
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200 and "token" in data:
            auth_token = data.get("token")
            user_info = data.get("user", {})
            log_result(
                f"Login ({username})",
                True,
                f"Successfully logged in. User ID: {user_info.get('id', 'N/A')}",
                {"token": auth_token[:20] + "..." if auth_token else None, "user": user_info}
            )
            return True
        else:
            log_result(
                f"Login ({username})",
                False,
                f"Login failed. Status: {response.status_code}",
                data
            )
            return False
    except Exception as e:
        log_result(f"Login ({username})", False, f"Error: {str(e)}")
        return False


def test_logout():
    """Test logout endpoint."""
    global auth_token
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            log_result("Logout", True, "Successfully logged out.")
            return True
        else:
            data = response.json() if response.content else {}
            log_result("Logout", False, f"Logout failed. Status: {response.status_code}", data)
            return False
    except Exception as e:
        log_result("Logout", False, f"Error: {str(e)}")
        return False


def test_signup(username: str, password: str):
    """Test signup/register endpoint."""
    try:
        payload = {"username": username, "password": password}
            
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=payload,
            timeout=10
        )
        data = response.json()
        
        if response.status_code in [200, 201]:
            log_result(
                f"Signup ({username})",
                True,
                f"Successfully registered user.",
                data
            )
            # Save new user credentials
            with open("tests/test_credentials.txt", "a") as f:
                f.write(f"{username}:{password}\n")
            return True
        elif response.status_code == 400 and "exists" in str(data).lower():
            log_result(
                f"Signup ({username})",
                True,
                f"User already exists (expected for existing user test).",
                data
            )
            return True
        else:
            log_result(
                f"Signup ({username})",
                False,
                f"Signup failed. Status: {response.status_code}",
                data
            )
            return False
    except Exception as e:
        log_result(f"Signup ({username})", False, f"Error: {str(e)}")
        return False


def test_get_provider():
    """Test getting current provider info."""
    global auth_token
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        response = requests.get(
            f"{BASE_URL}/api/provider/current",
            headers=headers,
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200:
            log_result(
                "Get Provider",
                True,
                f"Provider: {data.get('provider', 'N/A')} | Model: {data.get('model', 'N/A')}",
                data
            )
            return True
        else:
            log_result("Get Provider", False, f"Failed. Status: {response.status_code}", data)
            return False
    except Exception as e:
        log_result("Get Provider", False, f"Error: {str(e)}")
        return False


def test_get_tools():
    """Test getting available tools."""
    global auth_token
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        response = requests.get(
            f"{BASE_URL}/api/tools",
            headers=headers,
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200:
            tools = data.get("tools", data) if isinstance(data, dict) else data
            tool_count = len(tools) if isinstance(tools, list) else "N/A"
            log_result(
                "Get Tools",
                True,
                f"Found {tool_count} tools available",
                {"sample": tools[:3] if isinstance(tools, list) else tools}
            )
            return True
        else:
            log_result("Get Tools", False, f"Failed. Status: {response.status_code}", data)
            return False
    except Exception as e:
        log_result("Get Tools", False, f"Error: {str(e)}")
        return False


def test_get_sessions():
    """Test getting user sessions."""
    global auth_token
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        response = requests.get(
            f"{BASE_URL}/api/sessions",
            headers=headers,
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200:
            sessions = data.get("sessions", [])
            log_result(
                "Get Sessions",
                True,
                f"Found {len(sessions)} sessions",
                {"count": len(sessions)}
            )
            return True
        else:
            log_result("Get Sessions", False, f"Failed. Status: {response.status_code}", data)
            return False
    except Exception as e:
        log_result("Get Sessions", False, f"Error: {str(e)}")
        return False


def test_agent_config():
    """Test getting agent configuration."""
    global auth_token
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        response = requests.get(
            f"{BASE_URL}/api/agent/config",
            headers=headers,
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200:
            log_result(
                "Get Agent Config",
                True,
                f"Agent type: {data.get('agent_type', 'N/A')}",
                data
            )
            return True
        else:
            log_result("Get Agent Config", False, f"Failed. Status: {response.status_code}", data)
            return False
    except Exception as e:
        log_result("Get Agent Config", False, f"Error: {str(e)}")
        return False


def save_results_to_file():
    """Save test results to a file."""
    os.makedirs("tests", exist_ok=True)
    with open("tests/test_results.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": BASE_URL,
            "results": results,
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"])
            }
        }, f, indent=2)
    print(f"\n📄 Results saved to tests/test_results.json")


def main():
    print("=" * 60)
    print("🧪 BACKEND API TEST SUITE")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n📍 Step 1: Health Check")
    if not test_health_check():
        print("\n❌ Server not running. Aborting tests.")
        save_results_to_file()
        return
    
    # Test 2: Login with existing user (Rudra)
    print("\n📍 Step 2: Login with existing user (Rudra)")
    test_login(EXISTING_USER["username"], EXISTING_USER["password"])
    
    # Test 3: Test authenticated endpoints
    print("\n📍 Step 3: Get Provider Info")
    test_get_provider()
    
    print("\n📍 Step 4: Get Available Tools")
    test_get_tools()
    
    print("\n📍 Step 5: Get Sessions")
    test_get_sessions()
    
    print("\n📍 Step 6: Get Agent Config")
    test_agent_config()
    
    # Test 7: Logout
    print("\n📍 Step 7: Logout")
    test_logout()
    
    # Test 8: Signup with existing user (should show already exists)
    print("\n📍 Step 8: Signup with existing user (Rudra) - should fail/show exists")
    test_signup(EXISTING_USER["username"], EXISTING_USER["password"])
    
    # Test 9: Signup with new user
    print("\n📍 Step 9: Signup with new user")
    test_signup(NEW_USER["username"], NEW_USER["password"])
    
    # Test 10: Login again with Rudra
    print("\n📍 Step 10: Login again with Rudra")
    test_login(EXISTING_USER["username"], EXISTING_USER["password"])
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print("=" * 60)
    
    # Save results
    save_results_to_file()
    
    # Also save test credentials file header
    os.makedirs("tests", exist_ok=True)
    if not os.path.exists("tests/test_credentials.txt"):
        with open("tests/test_credentials.txt", "w") as f:
            f.write("# Test Credentials\n")
            f.write("# Format: username:password\n")
            f.write("# ========================\n")


if __name__ == "__main__":
    main()
