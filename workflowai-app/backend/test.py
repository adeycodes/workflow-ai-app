#!/usr/bin/env python3
"""
Test if backend is accessible from Codespaces
"""
import requests
import json
import time

def test_codespaces_access():
    print("🧪 Testing Codespaces backend accessibility...")
    
    # Your actual Codespaces backend URL
    backend_url = "https://fantastic-halibut-v9xx69w6vwqfxv7x-8000.app.github.dev"
    
    print(f"📍 Testing URL: {backend_url}")
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(backend_url + "/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("   ✅ Root endpoint working")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Root endpoint error: {e}")
    
    # Test 2: Health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(backend_url + "/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("   ✅ Health endpoint working")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
    
    # Test 3: API documentation
    print("\n3. Testing API documentation...")
    try:
        response = requests.get(backend_url + "/docs", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API docs accessible")
        else:
            print(f"   ❌ API docs failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API docs error: {e}")

if __name__ == "__main__":
    test_codespaces_access()