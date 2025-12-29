"""
Pytest configuration and fixtures for ktml-agent test suite.

Provides:
- Sandbox workspace management
- Agent wrapper for capturing commands
- Performance tracking utilities
- Logging configuration
"""

import pytest
import tempfile
import shutil
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_kernel import core


class AgentWrapper:
    """Wrapper around ktml-agent for testing."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.history: List[Dict[str, Any]] = []
        
    def run(self, nl_input: str) -> Dict[str, Any]:
        """
        Run natural language input through agent.
        
        Returns:
            {
                'nl_input': str,
                'command': str,
                'inverse': str,
                'safety_warning': str or None,
                'llm_latency': float,
                'execution_latency': float,
                'total_latency': float,
                'exit_code': int,
                'stdout': str,
                'stderr': str,
                'error': str or None
            }
        """
        start_time = time.time()
        
        # Call agent core
        llm_start = time.time()
        try:
            result = core.process_query(nl_input)
        except Exception as e:
            return {
                'nl_input': nl_input,
                'error': str(e),
                'total_latency': time.time() - start_time
            }
        llm_latency = time.time() - llm_start
        
        # Check for errors
        if 'error' in result:
            return {
                'nl_input': nl_input,
                'error': result['error'],
                'llm_latency': llm_latency,
                'total_latency': time.time() - start_time
            }
        
        # Handle both old 'command' format and new 'plan' format
        command = result.get('command', '')
        
        # If no command but there's a plan, execute the plan
        if not command and 'plan' in result:
            plan = result['plan']
            # Execute each step in the plan
            commands_to_run = []
            for step in plan:
                if isinstance(step, list) and len(step) > 0:
                    commands_to_run.append(step[0])
            
            # Join commands with && for sequential execution
            if commands_to_run:
                command = ' && '.join(commands_to_run)
        
        inverse = result.get('inverse')
        safety_warning = result.get('safety_warning')
        
        # Execute command in workspace
        exec_start = time.time()
        import subprocess
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=60
            )
            exit_code = process.returncode
            stdout = process.stdout
            stderr = process.stderr
        except subprocess.TimeoutExpired:
            exit_code = -1
            stdout = ""
            stderr = "Command timed out"
        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = str(e)
        exec_latency = time.time() - exec_start
        
        total_latency = time.time() - start_time
        
        result_dict = {
            'nl_input': nl_input,
            'command': command,
            'inverse': inverse,
            'safety_warning': safety_warning,
            'llm_latency': llm_latency,
            'execution_latency': exec_latency,
            'total_latency': total_latency,
            'exit_code': exit_code,
            'stdout': stdout,
            'stderr': stderr,
            'error': None
        }
        
        self.history.append(result_dict)
        return result_dict


@pytest.fixture
def workspace(tmp_path):
    """
    Create isolated test workspace.
    
    Yields:
        Path: Temporary directory for test execution
    """
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    
    # Change to workspace directory
    original_cwd = os.getcwd()
    os.chdir(workspace_dir)
    
    yield workspace_dir
    
    # Restore original directory
    os.chdir(original_cwd)
    
    # Cleanup is automatic with tmp_path


@pytest.fixture
def agent(workspace):
    """
    Create agent wrapper for testing.
    
    Args:
        workspace: Test workspace fixture
        
    Yields:
        AgentWrapper: Agent wrapper instance
    """
    return AgentWrapper(workspace)


@pytest.fixture
def git_repo(workspace):
    """
    Initialize git repository in workspace.
    
    Args:
        workspace: Test workspace fixture
        
    Yields:
        Path: Workspace with initialized git repo
    """
    import subprocess
    
    # Initialize repo
    subprocess.run(['git', 'init'], cwd=workspace, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=workspace, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=workspace, check=True, capture_output=True)
    
    # Create initial commit
    (workspace / "README.md").write_text("# Test Repo")
    subprocess.run(['git', 'add', '.'], cwd=workspace, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=workspace, check=True, capture_output=True)
    
    yield workspace


@pytest.fixture
def sample_python_files(workspace):
    """
    Create sample Python files for testing.
    
    Args:
        workspace: Test workspace fixture
        
    Yields:
        Path: Workspace with sample Python files
    """
    # Create directory structure
    src_dir = workspace / "src"
    src_dir.mkdir()
    
    # Create sample files
    (src_dir / "main.py").write_text("""
def old_function():
    return "Hello"

def another_function():
    result = old_function()
    return result
""")
    
    (src_dir / "utils.py").write_text("""
from main import old_function

def helper():
    return old_function()
""")
    
    yield workspace


@pytest.fixture
def sample_requirements(workspace):
    """
    Create sample requirements.txt.
    
    Args:
        workspace: Test workspace fixture
        
    Yields:
        Path: Workspace with requirements.txt
    """
    (workspace / "requirements.txt").write_text("""
requests==2.31.0
pytest==7.4.0
""")
    
    yield workspace


@pytest.fixture
def performance_tracker():
    """
    Track performance metrics across tests.
    
    Yields:
        dict: Performance metrics storage
    """
    metrics = {
        'latencies': [],
        'llm_latencies': [],
        'exec_latencies': []
    }
    
    yield metrics
    
    # Calculate statistics
    if metrics['latencies']:
        latencies = sorted(metrics['latencies'])
        n = len(latencies)
        
        stats = {
            'count': n,
            'mean': sum(latencies) / n,
            'median': latencies[n // 2],
            'p95': latencies[int(n * 0.95)] if n > 1 else latencies[0],
            'p99': latencies[int(n * 0.99)] if n > 1 else latencies[0],
            'min': min(latencies),
            'max': max(latencies)
        }
        
        # Save to file
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        with open(reports_dir / "performance_metrics.json", 'w') as f:
            json.dump(stats, f, indent=2)


def pytest_configure(config):
    """Create logs and reports directories."""
    test_dir = Path(__file__).parent
    (test_dir / "logs").mkdir(exist_ok=True)
    (test_dir / "reports").mkdir(exist_ok=True)
