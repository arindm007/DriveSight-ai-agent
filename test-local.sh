#!/bin/bash
# DriveSight - Local Testing Script
# This script tests all critical functionality

set -e

echo "🧪 DriveSight Testing Suite"
echo "============================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${1:-http://localhost:8080}"
SAMPLE_IMAGE="${2:-sample.jpg}"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_status=$4
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $http_code)"
        echo "Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

test_image_upload() {
    local name=$1
    local image_path=$2
    
    echo -n "Testing $name... "
    
    if [ ! -f "$image_path" ]; then
        echo -e "${YELLOW}⊘ SKIP${NC} (File not found: $image_path)"
        return
    fi
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -F "image=@$image_path" \
        "$API_URL/analyze")
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        # Check if response contains required fields
        if echo "$body" | grep -q "risk_score" && echo "$body" | grep -q "risk_label"; then
            echo -e "${GREEN}✓ PASS${NC} (HTTP 200)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ FAIL${NC} (Missing required fields)"
            echo "Response: $body"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo "Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# ============================================================================
# Test Suite
# ============================================================================

echo -e "${YELLOW}System Health Checks${NC}"
echo "---"

test_endpoint "Health Check" "GET" "/health" "200"
test_endpoint "Root Endpoint" "GET" "/" "200"
test_endpoint "API Docs" "GET" "/docs" "200"
test_endpoint "OpenAPI Schema" "GET" "/openapi.json" "200"

echo ""
echo -e "${YELLOW}Analysis Endpoints${NC}"
echo "---"

test_endpoint "History (empty)" "GET" "/history" "200"
test_endpoint "Statistics" "GET" "/stats" "200"
test_endpoint "Invalid Analysis ID" "GET" "/analysis/invalid-id" "404"

echo ""
echo -e "${YELLOW}Image Upload Tests${NC}"
echo "---"

test_image_upload "Analyze Sample Image" "$SAMPLE_IMAGE"

# Test missing image
echo -n "Testing Missing Image Upload... "
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/analyze")
http_code=$(echo "$response" | tail -n 1)

if [ "$http_code" = "422" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP 422 - validation error)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected 422, got $http_code)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${YELLOW}Error Handling${NC}"
echo "---"

# Test oversized image creation
echo -n "Testing Image Size Validation... "
# Create 25MB test file (should fail at 20MB limit)
if command -v dd &> /dev/null; then
    dd if=/dev/zero bs=1M count=25 of=oversized.bin 2>/dev/null
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -F "image=@oversized.bin" \
        "$API_URL/analyze")
    http_code=$(echo "$response" | tail -n 1)
    rm -f oversized.bin
    
    if [ "$http_code" = "413" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP 413 - payload too large)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected 413, got $http_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⊘ SKIP${NC} (dd command not available)"
fi

echo ""
echo -e "${YELLOW}Performance Tests${NC}"
echo "---"

if [ -f "$SAMPLE_IMAGE" ]; then
    # First request (cold)
    echo -n "Testing First Request Latency... "
    start_time=$(date +%s%N)
    curl -s -X POST -F "image=@$SAMPLE_IMAGE" "$API_URL/analyze" > /dev/null
    end_time=$(date +%s%N)
    duration=$((($end_time - $start_time) / 1000000))  # Convert to milliseconds
    
    if [ "$duration" -lt 5000 ]; then
        echo -e "${GREEN}✓ PASS${NC} (${duration}ms)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⊘ WARN${NC} (${duration}ms - slower than expected)"
    fi
    
    # Second request (cached)
    echo -n "Testing Cached Request Latency... "
    start_time=$(date +%s%N)
    response=$(curl -s -X POST -F "image=@$SAMPLE_IMAGE" "$API_URL/analyze")
    end_time=$(date +%s%N)
    duration=$((($end_time - $start_time) / 1000000))
    
    # Check if response indicates cache hit
    if echo "$response" | grep -q '"cached": true'; then
        echo -e "${GREEN}✓ PASS${NC} (${duration}ms - cached)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⊘ INFO${NC} (${duration}ms - cache miss)"
    fi
else
    echo -e "${YELLOW}⊘ SKIP${NC} (Sample image not found)"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "============================"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo "============================"

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
