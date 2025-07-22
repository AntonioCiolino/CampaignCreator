# Campaign Crafter MCP Server Tests

## Overview

This directory contains test scripts for the Campaign Crafter MCP (Model Context Protocol) server. These tests validate the functionality of the MCP server's integration with the Campaign Crafter API.

## Important Warning ⚠️

**These are LIVE integration tests, not mocks!**

These tests make actual API calls to both:
1. The MCP server running on port 4000
2. The Campaign Crafter API server running on port 8000

When executed, these tests will:
- Create real resources (campaigns, characters, sections)
- Modify those resources
- Delete those resources
- Generate content using LLM services

## Test Files

- `test_all_endpoints.py` - Comprehensive test of all MCP server endpoints
- `test_rpc.py` - Basic RPC functionality tests
- `test_sections.py` - Tests for campaign section endpoints
- `test_linking.py` - Tests for character-campaign linking endpoints
- `test_toc.py` - Tests for table of contents generation
- `test_titles.py` - Tests for title generation
- `debug_section.py` - Debugging tool for campaign section creation issues (compares direct API calls vs. MCP calls)

## Usage

To run these tests, both the MCP server and the Campaign Crafter API server must be running:

```bash
# Run a specific test
python tests/test_all_endpoints.py

# Run a specific test with detailed output
python tests/test_sections.py
```

## Authentication

These tests authenticate with the Campaign Crafter API using credentials from environment variables:
- `CAMPAIGN_CRAFTER_USERNAME` (default: "admin")
- `CAMPAIGN_CRAFTER_PASSWORD` (default: "changeme")
- `CAMPAIGN_CRAFTER_TOKEN` (optional, will be obtained via login if not provided)

## Purpose

These tests serve several purposes:
1. Validate that the MCP server correctly forwards requests to the Campaign Crafter API
2. Ensure that all endpoints are properly implemented and working
3. Provide examples of how to use the MCP server's tools
4. Serve as regression tests when making changes to the MCP server

## Best Practices

- Run these tests in a development environment, not production
- Consider creating a dedicated test user in the Campaign Crafter API
- Review the test output to ensure resources are properly cleaned up