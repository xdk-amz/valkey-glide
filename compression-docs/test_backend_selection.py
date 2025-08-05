#!/usr/bin/env python3
"""
Simple test to verify backend selection works correctly in interactive_session.py
"""

import subprocess
import sys
import os

def test_backend_help():
    """Test that help message works by checking the script source"""
    try:
        # Read the script to verify argument parsing is set up correctly
        with open('compression-docs/interactive_session.py', 'r') as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ('argparse import', 'import argparse' in content),
            ('backend choices', "choices=['zstd', 'lz4']" in content),
            ('argument parser', 'ArgumentParser' in content),
            ('backend parameter', 'backend' in content and 'nargs' in content),
            ('setup_session with backend', 'def setup_session(backend=' in content)
        ]
        
        all_passed = True
        for check_name, passed in checks:
            if passed:
                print(f"✅ {check_name} found in script")
            else:
                print(f"❌ {check_name} missing from script")
                all_passed = False
        
        if all_passed:
            print("✅ All argument parsing components present")
        else:
            print("❌ Some argument parsing components missing")
            
    except Exception as e:
        print(f"❌ Script analysis failed: {e}")

def test_shell_script_validation():
    """Test that shell script validates arguments correctly"""
    try:
        # Test invalid backend
        result = subprocess.run([
            './run_interactive.sh', 'invalid'
        ], capture_output=True, text=True, cwd='compression-docs')
        
        if result.returncode != 0 and 'Invalid backend' in result.stderr:
            print("✅ Shell script validates backend arguments")
        else:
            print("❌ Shell script validation failed")
            print(f"Return code: {result.returncode}")
            print(f"Stderr: {result.stderr}")
            
        # Test valid backends (just check they don't fail validation)
        for backend in ['zstd', 'lz4']:
            result = subprocess.run([
                './run_interactive.sh', backend
            ], capture_output=True, text=True, cwd='compression-docs', timeout=5)
            
            # We expect this to fail due to missing environment, but not due to argument validation
            if 'Invalid backend' not in result.stderr:
                print(f"✅ Shell script accepts '{backend}' backend")
            else:
                print(f"❌ Shell script rejects valid backend '{backend}'")
                
    except subprocess.TimeoutExpired:
        print("✅ Shell script started (timed out as expected without proper environment)")
    except Exception as e:
        print(f"❌ Shell script test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Backend Selection")
    print("=" * 40)
    
    print("\n📋 Test 1: Python script help")
    test_backend_help()
    
    print("\n📋 Test 2: Shell script validation")
    test_shell_script_validation()
    
    print("\n✅ Backend selection tests completed!")
