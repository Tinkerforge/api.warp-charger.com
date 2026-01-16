#!/bin/bash

# Run all unit tests for api.warp-charger.com
# Usage: ./run_all_tests.sh [pytest options]
#
# Examples:
#   ./run_all_tests.sh           # Run all tests with verbose output
#   ./run_all_tests.sh -x        # Stop on first failure
#   ./run_all_tests.sh -k "api"  # Run only tests matching "api"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running all tests..."
echo "===================="

python3 -m pytest tests/ -v "$@"
