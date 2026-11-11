# Test Configuration for DaVinci MCP Professional

This directory contains test suites for the DaVinci MCP Professional project.

## Test Structure

- `test_security.py` - Security-focused tests including dependency scanning, secret detection, and vulnerability checks
- `__init__.py` - Makes this directory a Python package
- `conftest.py` - Pytest configuration and shared fixtures

## Running Tests

### All Tests
```bash
pytest
```

### Security Tests Only
```bash
pytest tests/test_security.py -v
```

### With Coverage
```bash
pytest --cov=src/davinci_mcp --cov-report=html
```

## Security Test Categories

1. **Secret Detection**: Scans for hardcoded secrets in code and git history
2. **Dependency Security**: Checks for known vulnerabilities using uv audit
3. **File Permissions**: Ensures sensitive files have appropriate permissions
4. **Import Security**: Identifies potentially dangerous imports
5. **Configuration Security**: Scans config files for exposed secrets
6. **Input Validation**: Tests for injection vulnerabilities

## Test Dependencies

Install test dependencies:
```bash
pip install pytest pytest-cov bandit
```

## Continuous Integration

These tests are automatically run in GitHub Actions on:
- Every push to main branch
- Every pull request
- Weekly scheduled runs for dependency updates
