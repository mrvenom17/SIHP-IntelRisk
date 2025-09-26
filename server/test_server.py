#!/usr/bin/env python3
"""
Test script for the SIEM Server
"""

import requests
import json
import time
from typing import Dict, Any

def test_server_health(base_url: str = "http://localhost:8000"):
    """Test server health endpoint"""
    print("🏥 Testing server health...")

    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy")
            print(f"   Components: {data['components']}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_extract_endpoint(base_url: str = "http://localhost:8000"):
    """Test the extract endpoint"""
    print("\n🔍 Testing extract endpoint...")

    test_data = {
        "text": "Heavy flooding reported in Chennai last night. Water levels rising rapidly in downtown areas.",
        "source": "test_input"
    }

    try:
        response = requests.post(f"{base_url}/extract", json=test_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Extract endpoint working")
            print(f"   Success: {data['success']}")
            print(f"   Reports extracted: {len(data['reports'])}")
            if data['reports']:
                report = data['reports'][0]
                print(f"   Sample report: {report['event_type']} in {report['location']}")
            return True
        else:
            print(f"❌ Extract endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Extract test failed: {e}")
        return False

def test_analyze_endpoint(base_url: str = "http://localhost:8000"):
    """Test the full analyze endpoint"""
    print("\n🔬 Testing analyze endpoint...")

    test_data = {
        "text": "Heavy flooding reported in Chennai last night. Water levels rising rapidly in downtown areas. Multiple reports from residents about water entering homes in T. Nagar and Adyar areas.",
        "source": "test_input"
    }

    try:
        response = requests.post(f"{base_url}/analyze", json=test_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Analyze endpoint working")
            print(f"   Success: {data['success']}")
            print(f"   Reports: {len(data['reports'])}")
            print(f"   Hotspots: {len(data['hotspots'])}")
            print(f"   Verified reports: {len(data['verified_reports'])}")

            if data['reports']:
                report = data['reports'][0]
                print(f"   Sample report: {report['event_type']} in {report['location']}")

            return True
        else:
            print(f"❌ Analyze endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Analyze test failed: {e}")
        return False

def test_different_inputs(base_url: str = "http://localhost:8000"):
    """Test with different types of input"""
    print("\n📝 Testing different input types...")

    test_cases = [
        {
            "name": "Simple flood report",
            "text": "Flood in Mumbai today"
        },
        {
            "name": "Detailed disaster report",
            "text": "Major earthquake hit Delhi at 3:45 PM. Buildings damaged in Connaught Place area. Multiple injuries reported. Emergency services responding."
        },
        {
            "name": "Multiple events",
            "text": "Storm surge warning for Kerala coast. Heavy rainfall expected in Bangalore. Flooding reported in Hyderabad."
        }
    ]

    results = []

    for test_case in test_cases:
        print(f"\n   Testing: {test_case['name']}")
        try:
            response = requests.post(f"{base_url}/extract", json=test_case)
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "name": test_case['name'],
                    "success": data['success'],
                    "reports_count": len(data['reports'])
                })
                print(f"   ✅ Success: {data['success']}, Reports: {len(data['reports'])}")
            else:
                results.append({
                    "name": test_case['name'],
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                print(f"   ❌ Failed: HTTP {response.status_code}")
        except Exception as e:
            results.append({
                "name": test_case['name'],
                "success": False,
                "error": str(e)
            })
            print(f"   ❌ Error: {e}")

    return results

def run_full_test_suite(base_url: str = "http://localhost:8000"):
    """Run the complete test suite"""
    print("🧪 SIEM SERVER TEST SUITE")
    print("=" * 50)

    tests = [
        ("Health Check", test_server_health),
        ("Extract Endpoint", test_extract_endpoint),
        ("Analyze Endpoint", test_analyze_endpoint),
        ("Different Inputs", test_different_inputs)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_name == "Different Inputs":
                result = test_func(base_url)
                results.append((test_name, True, result))
            else:
                result = test_func(base_url)
                results.append((test_name, result, None))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False, str(e)))

    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, success, details in results:
        if success:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            if details:
                if isinstance(details, list):
                    for detail in details:
                        print(f"   - {detail['name']}: {detail['success']} ({detail.get('reports_count', 'N/A')} reports)")
                else:
                    print(f"   Error: {details}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Server is working perfectly!")
        return True
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    import sys

    # Allow custom base URL
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print(f"🌐 Testing server at: {base_url}")

    # Wait a bit for server to start
    print("⏳ Waiting 2 seconds for server to be ready...")
    time.sleep(2)

    success = run_full_test_suite(base_url)

    if success:
        print("\n🎉 Server test completed successfully!")
        print("Your SIEM server is ready to process disaster reports!")
    else:
        print("\n❌ Server test completed with failures.")
        print("Check the error messages above and fix any issues.")
