# ktml-agent Test Suite

Comprehensive test suite for validating correctness, reliability, and performance of ktml-agent.

## Overview

This test suite includes:
- **7 Integration Tests**: Real-world scenarios with natural language input
- **Reliability Testing**: 100-run consistency test with retry logic
- **Performance Benchmarking**: Latency tracking with percentile reporting

## Prerequisites

### Required
- Python 3.8+
- Git (for git workflow tests)
- ktml-agent installed with valid Gemini API key

### Optional
- Docker (for PostgreSQL container test)
- sudo/admin access (for service restart test)
- pylint (for lint & zip test)

## Installation

```bash
cd c:\Users\avime\Documents\vsCode\kernel
pip install -r tests/requirements-test.txt
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Integration Tests Only
```bash
pytest tests/test_integration.py -v
```

### Run Specific Test
```bash
pytest tests/test_integration.py::TestGitWorkflow::test_create_and_push_branch -v
```

### Run Reliability Test (100 runs)
```bash
pytest tests/test_reliability.py -v
```

**Note**: This will take ~5-10 minutes and make 100+ API calls.

### Run Performance Benchmarking
```bash
pytest tests/test_performance.py -v
```

### Skip Slow Tests
```bash
pytest tests/ -v -m "not slow"
```

### Skip Tests Requiring Docker
```bash
pytest tests/ -v -m "not requires_docker"
```

### Skip Tests Requiring Sudo
```bash
pytest tests/ -v -m "not requires_sudo"
```

## Test Descriptions

### Integration Tests (`test_integration.py`)

#### 1. Git Branch Workflow
- **NL Input**: "create a new branch called test-feature"
- **Verifies**: Branch exists locally, command succeeds
- **Prerequisites**: Git repository initialized

#### 2. Search and Replace
- **NL Input**: "rename function old_function to new_function in all Python files"
- **Verifies**: All occurrences changed, no unintended modifications
- **Prerequisites**: Sample Python files created

#### 3. Python Virtual Environment
- **NL Input**: "create a virtual environment and install dependencies from requirements.txt"
- **Verifies**: venv created, dependencies installed
- **Prerequisites**: requirements.txt exists

#### 4. Docker PostgreSQL
- **NL Input**: "run a PostgreSQL container on port 5432"
- **Verifies**: Container running, port reachable, connection succeeds
- **Prerequisites**: Docker daemon running
- **Marker**: `@pytest.mark.requires_docker`

#### 5. Lint and Zip
- **NL Input**: "lint all Python files and zip the results"
- **Verifies**: Command generated correctly
- **Prerequisites**: pylint installed (optional)

#### 6. Restart Service
- **NL Input**: "restart nginx service"
- **Verifies**: Command generated correctly
- **Prerequisites**: sudo access, nginx installed
- **Marker**: `@pytest.mark.requires_sudo`

#### 7. Directory Backup
- **NL Input**: "backup the src directory to backup/src"
- **Verifies**: Backup created, files match, hashes match
- **Prerequisites**: Source directory exists

### Reliability Test (`test_reliability.py`)

- **Runs**: 100 iterations of git branch creation
- **Tracks**:
  - First attempt success rate
  - Final success rate (with retries)
  - Error categories
  - Retry improvements
- **Generates**: `reports/reliability_report.json` and `reports/reliability_report.md`
- **Marker**: `@pytest.mark.reliability`, `@pytest.mark.slow`

### Performance Test (`test_performance.py`)

- **Runs**: 5 different queries
- **Tracks**:
  - LLM response latency
  - Command execution latency
  - Total end-to-end latency
- **Calculates**: Mean, median, p50, p95, p99, min, max, stdev
- **Generates**: `reports/performance_report.json` and `reports/performance_report.md`
- **Marker**: `@pytest.mark.performance`

## Output and Logging

### Console Output
Each test logs:
- Natural language input
- Generated command
- Exit code
- Stdout/stderr
- Latency metrics

Example:
```
============================================================
NL Input: create a new branch called test-feature
Generated Command: git checkout -b test-feature
Exit Code: 0
Stdout: Switched to a new branch 'test-feature'
Stderr: 
LLM Latency: 1.234s
Exec Latency: 0.056s
Total Latency: 1.290s
============================================================
```

### Log Files
- `tests/logs/pytest.log`: Detailed pytest logs

### Reports
- `tests/reports/reliability_report.json`: Reliability test results (JSON)
- `tests/reports/reliability_report.md`: Reliability test results (Markdown)
- `tests/reports/performance_report.json`: Performance metrics (JSON)
- `tests/reports/performance_report.md`: Performance metrics (Markdown)
- `tests/reports/performance_metrics.json`: Aggregated performance data

## Example Logs

### Integration Test Log
```
tests/test_integration.py::TestGitWorkflow::test_create_and_push_branch 
============================================================
NL Input: create a new branch called test-feature
Generated Command: git checkout -b test-feature
Exit Code: 0
Stdout: Switched to a new branch 'test-feature'
LLM Latency: 1.234s
Exec Latency: 0.056s
Total Latency: 1.290s
============================================================
PASSED
```

### Reliability Test Summary
```
============================================================
RELIABILITY TEST SUMMARY
============================================================
Total Runs: 100
First Attempt Success: 92 (92.0%)
Final Success: 97 (97.0%)
Retry Improvements: 5
Average Latency: 1.456s
============================================================
```

### Performance Test Summary
```
============================================================
PERFORMANCE SUMMARY
============================================================
Total Latency:
  Mean: 1.523s
  Median (p50): 1.456s
  p95: 2.134s
  p99: 2.567s

LLM Latency:
  Mean: 1.234s
  p95: 1.890s

Execution Latency:
  Mean: 0.289s
  p95: 0.456s
============================================================
```

## Validation Explanation

### How This Validates Correctness

1. **Functional Correctness**: Each integration test verifies that the agent:
   - Generates syntactically valid commands
   - Commands execute successfully
   - Final system state matches expectations

2. **Safety**: Tests verify that:
   - Dangerous commands are flagged (if applicable)
   - Commands don't have unintended side effects
   - Cleanup happens properly

3. **Reliability**: 100-run test validates:
   - Consistency of LLM outputs
   - Retry logic effectiveness
   - Error handling robustness

4. **Performance**: Benchmarking validates:
   - Latency is within acceptable bounds
   - No performance regressions
   - LLM vs execution time breakdown

### Acceptance Criteria

#### Integration Tests
- ✅ All tests pass (or skip gracefully if prerequisites missing)
- ✅ Commands execute successfully (exit code 0)
- ✅ Final state matches expectations

#### Reliability Test
- ✅ First attempt success rate ≥80%
- ✅ Final success rate (with retries) ≥90%
- ✅ Retry logic improves success rate

#### Performance Test
- ✅ p95 latency <5s
- ✅ Mean latency <3s
- ✅ No outliers >10s

## Troubleshooting

### Test Failures

**"Docker not available"**
- Install Docker and start Docker daemon
- Or skip Docker tests: `pytest -m "not requires_docker"`

**"Sudo access required"**
- Run with sudo: `sudo pytest tests/`
- Or skip sudo tests: `pytest -m "not requires_sudo"`

**"API rate limit exceeded"**
- Wait a few minutes and retry
- Reduce number of runs in reliability test
- Add delays between API calls

**"Git repository not initialized"**
- Tests automatically initialize git repos in sandboxes
- Check that git is installed: `git --version`

### Common Issues

**Import errors**
- Ensure ktml-agent is installed: `pip install -e .`
- Check Python path includes src directory

**API key not found**
- Configure API key: Run `agent` once to set up
- Or set environment variable: `export GEMINI_API_KEY=your_key`

**Tests hang**
- Check pytest timeout setting (default: 300s)
- Some tests (Docker, venv) may take longer

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install -r tests/requirements-test.txt
    
    - name: Run integration tests
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        pytest tests/test_integration.py -v -m "not requires_sudo and not requires_docker"
    
    - name: Run performance tests
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        pytest tests/test_performance.py -v
    
    - name: Upload reports
      uses: actions/upload-artifact@v2
      with:
        name: test-reports
        path: tests/reports/
```

## Contributing

When adding new tests:
1. Follow existing test structure
2. Use appropriate pytest markers
3. Add cleanup in fixtures
4. Log NL input, command, and results
5. Update this README

## License

Same as ktml-agent (MIT)
