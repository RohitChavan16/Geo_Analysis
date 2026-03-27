#!/usr/bin/env python3
"""
End-to-End Test Suite for GeoShop Engine

Tests all components from end-to-end:
1. Data pipeline with mock data
2. API endpoints
3. Frontend connectivity
4. Real-time updates
"""

import sys
import time
import requests
import json
from typing import Dict, Any
import subprocess
import os


class TestRunner:
    """Comprehensive test runner for GeoShop Engine."""

    def __init__(self):
        self.api_url = "http://localhost:8000/api"
        self.tests_passed = 0
        self.tests_failed = 0

    def print_header(self, text: str):
        """Print formatted header."""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60)

    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result."""
        symbol = "✅" if status == "PASS" else "❌"
        print(f"{symbol} {name}")
        if details:
            print(f"   {details}")

    def test_pipeline_with_mock_data(self):
        """Test the data pipeline with mock data."""
        self.print_header("TEST 1: Data Pipeline with Mock Data")

        try:
            print("\n📥 Running pipeline with mock data...")
            result = subprocess.run(
                [sys.executable, "main.py", "demo"],
                cwd="e:\\test\\geoshop_engine",
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                if "PIPELINE COMPLETE" in result.stdout or "📍" in result.stdout:
                    self.print_test("Pipeline Execution", "PASS", "Successfully processed mock data")
                    self.tests_passed += 1
                    return True
                else:
                    self.print_test("Pipeline Execution", "FAIL", "Pipeline ran but output unclear")
                    self.tests_failed += 1
                    return False
            else:
                error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                self.print_test("Pipeline Execution", "FAIL", error_msg)
                self.tests_failed += 1
                return False

        except Exception as e:
            self.print_test("Pipeline Execution", "FAIL", str(e))
            self.tests_failed += 1
            return False

    def test_api_endpoints(self):
        """Test all API endpoints."""
        self.print_header("TEST 2: API Endpoints")

        # Give server time to start if needed
        time.sleep(2)

        endpoints = [
            ("GET", "/health", None),
            ("GET", "/shops/stats", None),
            ("GET", "/shops?limit=5", None),
            ("GET", "/sync/status", None),
        ]

        for method, endpoint, body in endpoints:
            try:
                url = self.api_url + endpoint
                if method == "GET":
                    response = requests.get(url, timeout=5)
                elif method == "POST":
                    response = requests.post(url, json=body, timeout=5)

                if response.status_code in [200, 201]:
                    try:
                        data = response.json()
                        self.print_test(
                            f"API {method} {endpoint}",
                            "PASS",
                            f"Status: {response.status_code}"
                        )
                        self.tests_passed += 1
                    except:
                        self.print_test(
                            f"API {method} {endpoint}",
                            "PASS",
                            f"Status: {response.status_code} (non-JSON response)"
                        )
                        self.tests_passed += 1
                else:
                    self.print_test(
                        f"API {method} {endpoint}",
                        "FAIL",
                        f"Status: {response.status_code}"
                    )
                    self.tests_failed += 1

            except requests.exceptions.ConnectionError:
                # Server might not be running, that's OK for this test
                self.print_test(
                    f"API {method} {endpoint}",
                    "FAIL",
                    "Cannot connect to API (server not running)"
                )
                self.tests_failed += 1
            except Exception as e:
                self.print_test(
                    f"API {method} {endpoint}",
                    "FAIL",
                    str(e)[:100]
                )
                self.tests_failed += 1

    def test_frontend_files(self):
        """Test frontend files exist and are valid."""
        self.print_header("TEST 3: Frontend Files")

        files_to_check = [
            ("e:\\test\\geoshop_engine\\frontend\\index.html", "Frontend HTML"),
        ]

        for filepath, name in files_to_check:
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if len(content) > 100:  # Basic check
                            self.print_test(f"{name} exists", "PASS", f"{len(content)} bytes")
                            self.tests_passed += 1
                        else:
                            self.print_test(f"{name} exists", "FAIL", "File too small")
                            self.tests_failed += 1
                else:
                    self.print_test(f"{name} exists", "FAIL", "File not found")
                    self.tests_failed += 1

            except Exception as e:
                self.print_test(f"{name} check", "FAIL", str(e))
                self.tests_failed += 1

    def test_project_structure(self):
        """Test project structure is complete."""
        self.print_header("TEST 4: Project Structure")

        required_dirs = [
            "e:\\test\\geoshop_engine\\api",
            "e:\\test\\geoshop_engine\\data_fetchers",
            "e:\\test\\geoshop_engine\\processors",
            "e:\\test\\geoshop_engine\\signal_engine",
            "e:\\test\\geoshop_engine\\db",
            "e:\\test\\geoshop_engine\\scheduler",
            "e:\\test\\geoshop_engine\\frontend",
        ]

        required_files = [
            "e:\\test\\geoshop_engine\\main.py",
            "e:\\test\\geoshop_engine\\run_api.py",
            "e:\\test\\geoshop_engine\\requirements.txt",
            "e:\\test\\geoshop_engine\\.env",
            "e:\\test\\geoshop_engine\\README.md",
        ]

        for dir_path in required_dirs:
            if os.path.isdir(dir_path):
                self.print_test(f"Directory: {os.path.basename(dir_path)}", "PASS")
                self.tests_passed += 1
            else:
                self.print_test(f"Directory: {os.path.basename(dir_path)}", "FAIL", "Not found")
                self.tests_failed += 1

        for file_path in required_files:
            if os.path.isfile(file_path):
                self.print_test(f"File: {os.path.basename(file_path)}", "PASS")
                self.tests_passed += 1
            else:
                self.print_test(f"File: {os.path.basename(file_path)}", "FAIL", "Not found")
                self.tests_failed += 1

    def test_imports(self):
        """Test all Python modules can be imported."""
        self.print_header("TEST 5: Python Module Imports")

        modules = [
            "main",
            "db.database",
            "db.crud",
            "db.models",
            "data_fetchers.osm_fetcher",
            "data_fetchers.datagov_fetcher",
            "data_fetchers.onemap_fetcher",
            "processors.normalizer",
            "processors.matcher",
            "signal_engine.signal_calculator",
            "api.main",
        ]

        for module in modules:
            try:
                __import__(module)
                self.print_test(f"Import {module}", "PASS")
                self.tests_passed += 1
            except ImportError as e:
                self.print_test(f"Import {module}", "FAIL", str(e)[:100])
                self.tests_failed += 1
            except Exception as e:
                self.print_test(f"Import {module}", "FAIL", str(e)[:100])
                self.tests_failed += 1

    def run_all_tests(self):
        """Run all tests."""
        self.print_header("GeoShop Engine - End-to-End Test Suite")

        print("\n🧪 Running comprehensive tests...\n")

        # Run tests
        self.test_project_structure()
        self.test_imports()
        self.test_pipeline_with_mock_data()
        self.test_frontend_files()
        self.test_api_endpoints()

        # Print summary
        self.print_header("TEST SUMMARY")
        total = self.tests_passed + self.tests_failed
        percentage = (self.tests_passed / total * 100) if total > 0 else 0

        print(f"\n✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Total:   {total}")
        print(f"Success Rate: {percentage:.1f}%\n")

        if self.tests_failed == 0:
            print("🎉 All tests passed! Your GeoShop Engine is ready to go!\n")
            return True
        elif percentage >= 70:
            print("⚠️  Most tests passed. Please review failures above.\n")
            return False
        else:
            print("❌ Several tests failed. Please review the issues above.\n")
            return False


def main():
    """Run the test suite."""
    os.chdir("e:\\test\\geoshop_engine")
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
