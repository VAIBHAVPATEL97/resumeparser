#!/usr/bin/env python3
"""
Test runner script for resume_parser.

This script provides convenient commands to run tests with different configurations.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --fast             # Run fast tests only (skip slow tests)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run resume_parser tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel with N workers")

    args = parser.parse_args()

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add test markers
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.fast:
        cmd.extend(["-m", "not slow"])

    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=resume_parser", "--cov-report=term-missing", "--cov-report=html"])

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Run the tests
    success = run_command(cmd, "Resume Parser Tests")

    if success:
        print(f"\n{'='*60}")
        print("✅ All tests passed!")
        if args.coverage:
            print("Coverage report generated in htmlcov/index.html")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print("❌ Some tests failed!")
        print("Check the output above for details.")
        print('='*60)
        sys.exit(1)


if __name__ == "__main__":
    main()