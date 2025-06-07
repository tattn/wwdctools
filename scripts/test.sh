#!/usr/bin/env bash
set -o pipefail

# test.sh - Comprehensive lint and test script for wwdctools
# Usage: ./scripts/test.sh [options]
#   Options:
#     --lint-only: Run only linting checks, skip tests
#     --test-only: Run only tests, skip linting
#     --fix: Fix linting issues where possible
#     --help: Show this help message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Define color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_LINT=true
RUN_TESTS=true
FIX_ISSUES=false

# Process command line arguments
for arg in "$@"; do
  case $arg in
    --lint-only)
      RUN_TESTS=false
      ;;
    --test-only)
      RUN_LINT=false
      ;;
    --fix)
      FIX_ISSUES=true
      ;;
    --help)
      echo "Usage: ./scripts/test.sh [options]"
      echo "  Options:"
      echo "    --lint-only: Run only linting checks, skip tests"
      echo "    --test-only: Run only tests, skip linting"
      echo "    --fix: Fix linting issues where possible"
      echo "    --help: Show this help message"
      exit 0
      ;;
  esac
done

# Function to print section headers
print_header() {
  printf "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to check command result and print appropriate message
check_result() {
  if [ $? -eq 0 ]; then
    printf "${GREEN}✓ $1 passed${NC}\n"
  else
    printf "${RED}✗ $1 failed${NC}\n"
    if [ "$2" != "continue" ]; then
      exit 1
    fi
  fi
}

# Run linting checks
if [ "$RUN_LINT" = true ]; then
  print_header "Running Linting Checks"

  # Ruff Format
  printf "${YELLOW}Running Ruff Format...${NC}\n"
  if [ "$FIX_ISSUES" = true ]; then
    uv run --frozen ruff format .
    check_result "Ruff Format" "continue"
  else
    uv run --frozen ruff format --check .
    check_result "Ruff Format Check" "continue"
  fi

  # Ruff Lint
  printf "${YELLOW}Running Ruff Lint...${NC}\n"
  if [ "$FIX_ISSUES" = true ]; then
    uv run --frozen ruff check . --fix
    check_result "Ruff Lint" "continue"
  else
    uv run --frozen ruff check .
    check_result "Ruff Lint Check" "continue"
  fi

  # Pyright Type Checking
  printf "${YELLOW}Running Pyright Type Checking...${NC}\n"
  uv run --frozen pyright
  check_result "Pyright Type Checking" "continue"
fi

# Run tests
if [ "$RUN_TESTS" = true ]; then
  print_header "Running Tests"
  
  # Run pytest with anyio
  printf "${YELLOW}Running pytest...${NC}\n"
  PYTEST_DISABLE_PLUGIN_AUTOLOAD="" uv run --frozen pytest
  check_result "Pytest" "continue"
fi

# Final summary
print_header "Summary"
if [ $? -eq 0 ]; then
  printf "${GREEN}All checks passed!${NC}\n"
else
  printf "${RED}Some checks failed. Please fix the issues and try again.${NC}\n"
  exit 1
fi
