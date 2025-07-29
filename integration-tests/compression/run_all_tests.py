#!/usr/bin/env python3
"""
Comprehensive test runner for all compression integration tests.

This script runs all compression integration tests in sequence and provides
a summary of results. It can be used for automated testing and CI/CD pipelines.
"""

import asyncio
import os
import subprocess
import sys
import time
from typing import Dict, List, Tuple

# Add the Python client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../python"))

# Import test classes
from cross_language_compatibility_test import CrossLanguageCompressionTest
from backward_compatibility_test import BackwardCompatibilityTest
from performance_and_error_handling_test import PerformanceAndErrorHandlingTest


class ComprehensiveTestRunner:
    """Runs all compression integration tests and provides summary results."""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met before running tests."""
        print("Checking prerequisites...")
        
        # Check if Redis/Valkey server is running
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0 or result.stdout.strip() != "PONG":
                print("❌ Redis/Valkey server is not running on localhost:6379")
                print("   Please start a Redis or Valkey server before running tests")
                return False
            print("✅ Redis/Valkey server is running")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Cannot connect to Redis/Valkey server")
            print("   Please ensure redis-cli is installed and server is running")
            return False

        # Check Python environment
        try:
            import glide
            print("✅ Python Glide client is available")
        except ImportError:
            print("❌ Python Glide client is not available")
            print("   Please install the Python client dependencies")
            return False

        # Check Node.js environment
        node_build_path = os.path.join(os.path.dirname(__file__), "../../node/build-ts")
        if not os.path.exists(node_build_path):
            print("❌ Node.js build not found")
            print("   Please run 'npm run build' in the node directory")
            return False
        print("✅ Node.js build is available")

        return True

    async def run_python_tests(self) -> Dict[str, bool]:
        """Run all Python-based tests."""
        print("\n" + "="*60)
        print("RUNNING PYTHON TESTS")
        print("="*60)
        
        python_results = {}
        
        # Cross-language compatibility tests
        print("\n--- Cross-Language Compatibility Tests (Python) ---")
        try:
            cross_lang_test = CrossLanguageCompressionTest()
            result = await cross_lang_test.run_all_tests()
            python_results["cross_language"] = result
            print(f"Result: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"Cross-language tests failed with exception: {e}")
            python_results["cross_language"] = False

        # Backward compatibility tests
        print("\n--- Backward Compatibility Tests (Python) ---")
        try:
            backward_test = BackwardCompatibilityTest()
            result = await backward_test.run_all_tests()
            python_results["backward_compatibility"] = result
            print(f"Result: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"Backward compatibility tests failed with exception: {e}")
            python_results["backward_compatibility"] = False

        # Performance and error handling tests
        print("\n--- Performance and Error Handling Tests (Python) ---")
        try:
            perf_test = PerformanceAndErrorHandlingTest()
            result = await perf_test.run_all_tests()
            python_results["performance_error_handling"] = result
            print(f"Result: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"Performance and error handling tests failed with exception: {e}")
            python_results["performance_error_handling"] = False

        return python_results

    def run_nodejs_tests(self) -> Dict[str, bool]:
        """Run all Node.js-based tests."""
        print("\n" + "="*60)
        print("RUNNING NODE.JS TESTS")
        print("="*60)
        
        nodejs_results = {}
        
        test_files = [
            ("cross_language", "cross_language_compatibility_test.ts"),
            ("backward_compatibility", "backward_compatibility_test.ts"),
            ("performance_error_handling", "performance_and_error_handling_test.ts"),
        ]
        
        for test_name, test_file in test_files:
            print(f"\n--- {test_name.replace('_', ' ').title()} Tests (Node.js) ---")
            
            try:
                test_path = os.path.join(os.path.dirname(__file__), test_file)
                result = subprocess.run(
                    ["npx", "ts-node", test_path],
                    cwd=os.path.join(os.path.dirname(__file__), "../../node"),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                # Print the output
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                
                nodejs_results[test_name] = result.returncode == 0
                print(f"Result: {'PASS' if result.returncode == 0 else 'FAIL'}")
                
            except subprocess.TimeoutExpired:
                print(f"Test {test_name} timed out")
                nodejs_results[test_name] = False
            except Exception as e:
                print(f"Test {test_name} failed with exception: {e}")
                nodejs_results[test_name] = False

        return nodejs_results

    def print_summary(self, python_results: Dict[str, bool], nodejs_results: Dict[str, bool]):
        """Print a comprehensive summary of all test results."""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        print(f"Total execution time: {total_duration:.2f} seconds")
        
        print("\nPython Test Results:")
        python_passed = 0
        python_total = len(python_results)
        
        for test_name, result in python_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
            if result:
                python_passed += 1
        
        print(f"  Python Summary: {python_passed}/{python_total} tests passed")
        
        print("\nNode.js Test Results:")
        nodejs_passed = 0
        nodejs_total = len(nodejs_results)
        
        for test_name, result in nodejs_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
            if result:
                nodejs_passed += 1
        
        print(f"  Node.js Summary: {nodejs_passed}/{nodejs_total} tests passed")
        
        # Overall summary
        total_passed = python_passed + nodejs_passed
        total_tests = python_total + nodejs_total
        
        print(f"\nOverall Summary: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED! Compression integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the output above for details.")
            
        # Recommendations
        print("\nRecommendations:")
        if total_passed == total_tests:
            print("  - Compression feature is ready for production use")
            print("  - Cross-language compatibility is verified")
            print("  - Backward compatibility is maintained")
            print("  - Performance characteristics are acceptable")
        else:
            print("  - Review failed tests and fix issues before deployment")
            print("  - Check server connectivity and configuration")
            print("  - Verify client library installations")
            print("  - Consider running tests individually for detailed debugging")

    async def run_all_tests(self) -> bool:
        """Run all compression integration tests."""
        print("Starting comprehensive compression integration tests...")
        print("This will test cross-language compatibility, backward compatibility,")
        print("performance characteristics, and error handling.")
        
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please fix the issues above and try again.")
            return False
        
        self.start_time = time.time()
        
        try:
            # Run Python tests
            python_results = await self.run_python_tests()
            
            # Run Node.js tests
            nodejs_results = self.run_nodejs_tests()
            
            self.end_time = time.time()
            
            # Print comprehensive summary
            self.print_summary(python_results, nodejs_results)
            
            # Determine overall success
            all_python_passed = all(python_results.values())
            all_nodejs_passed = all(nodejs_results.values())
            overall_success = all_python_passed and all_nodejs_passed
            
            return overall_success
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Test runner failed with exception: {e}")
            return False


async def main():
    """Main entry point."""
    runner = ComprehensiveTestRunner()
    
    try:
        success = await runner.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
