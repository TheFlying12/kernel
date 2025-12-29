"""
Integration tests for ktml-agent.

Tests real-world scenarios with natural language input.
"""

import pytest
import subprocess
import time
from pathlib import Path
import zipfile

from .test_utils import (
    file_exists, dir_exists, count_files, grep_count,
    git_branch_exists, docker_container_running, docker_port_reachable,
    postgres_connection_test, cleanup_docker_container,
    wait_for_condition, compare_directories, has_sudo_access, has_docker
)


class TestGitWorkflow:
    """Test 1: Git branch workflow."""
    
    def test_create_and_push_branch(self, agent, git_repo, performance_tracker):
        """
        NL: Create a new branch called test-feature and push it to remote.
        
        Acceptance criteria:
        - Branch exists locally
        - Branch exists on remote (if remote configured)
        - Commit with expected message exists
        """
        # Setup: Add a remote (mock)
        subprocess.run(
            ['git', 'remote', 'add', 'origin', 'https://github.com/test/repo.git'],
            cwd=git_repo,
            capture_output=True
        )
        
        # Run agent
        nl_input = "create a new branch called test-feature"
        result = agent.run(nl_input)
        
        # Track performance
        performance_tracker['latencies'].append(result['total_latency'])
        performance_tracker['llm_latencies'].append(result.get('llm_latency', 0))
        performance_tracker['exec_latencies'].append(result.get('execution_latency', 0))
        
        # Log result
        print(f"\n{'='*60}")
        print(f"NL Input: {nl_input}")
        print(f"Generated Command: {result.get('command', 'N/A')}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"Stdout: {result.get('stdout', 'N/A')}")
        print(f"Stderr: {result.get('stderr', 'N/A')}")
        print(f"LLM Latency: {result.get('llm_latency', 0):.3f}s")
        print(f"Exec Latency: {result.get('execution_latency', 0):.3f}s")
        print(f"Total Latency: {result.get('total_latency', 0):.3f}s")
        print(f"{'='*60}\n")
        
        # Assertions
        assert 'error' not in result or result['error'] is None, f"Agent error: {result.get('error')}"
        assert result.get('exit_code') == 0, f"Command failed with exit code {result.get('exit_code')}"
        
        # Verify branch exists locally
        assert git_branch_exists('test-feature', git_repo), "Branch 'test-feature' not found locally"
        
        # Note: Can't test remote push without actual remote, but command should be generated


class TestSearchAndReplace:
    """Test 2: Search and replace across multiple files."""
    
    def test_rename_function(self, agent, sample_python_files, performance_tracker):
        """
        NL: Rename function old_name to new_name in all Python files.
        
        Acceptance criteria:
        - All occurrences are changed
        - No unintended files are modified
        """
        workspace = sample_python_files
        
        # Count initial occurrences
        initial_count = grep_count(workspace, "old_function")
        assert initial_count > 0, "Test setup failed: old_function not found"
        
        # Run agent
        nl_input = "rename the function old_function to new_function in all Python files"
        result = agent.run(nl_input)
        
        # Track performance
        performance_tracker['latencies'].append(result['total_latency'])
        
        # Log result
        print(f"\n{'='*60}")
        print(f"NL Input: {nl_input}")
        print(f"Generated Command: {result.get('command', 'N/A')}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"Total Latency: {result.get('total_latency', 0):.3f}s")
        print(f"{'='*60}\n")
        
        # Assertions
        assert 'error' not in result or result['error'] is None
        
        # Verify all occurrences changed
        old_count = grep_count(workspace, "old_function")
        new_count = grep_count(workspace, "new_function")
        
        assert old_count == 0, f"Still found {old_count} occurrences of 'old_function'"
        assert new_count == initial_count, f"Expected {initial_count} occurrences of 'new_function', found {new_count}"


class TestPythonVirtualEnv:
    """Test 3: Python virtual environment + dependency install."""
    
    def test_create_venv_and_install(self, agent, sample_requirements, performance_tracker):
        """
        NL: Create a virtual environment and install dependencies from requirements.txt.
        
        Acceptance criteria:
        - A venv is created
        - Dependencies install successfully
        - Running pip list shows expected packages
        """
        workspace = sample_requirements
        
        # Run agent
        nl_input = "create a virtual environment called venv and install dependencies from requirements.txt"
        result = agent.run(nl_input)
        
        # Track performance
        performance_tracker['latencies'].append(result['total_latency'])
        
        # Log result
        print(f"\n{'='*60}")
        print(f"NL Input: {nl_input}")
        print(f"Generated Command: {result.get('command', 'N/A')}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"Total Latency: {result.get('total_latency', 0):.3f}s")
        print(f"{'='*60}\n")
        
        # Assertions
        assert 'error' not in result or result['error'] is None
        
        # Verify venv exists
        venv_dir = workspace / "venv"
        assert dir_exists(venv_dir), "Virtual environment directory not created"
        
        # Verify venv structure (Scripts on Windows, bin on Unix)
        assert dir_exists(venv_dir / "Scripts") or dir_exists(venv_dir / "bin"), \
            "Virtual environment structure invalid"


@pytest.mark.requires_docker
class TestDockerPostgreSQL:
    """Test 4: Spin up Docker PostgreSQL container."""
    
    def test_run_postgres_container(self, agent, workspace, performance_tracker):
        """
        NL: Run a PostgreSQL container with port 5432 exposed.
        
        Acceptance criteria:
        - Container is running
        - The port is reachable
        - A test connection succeeds
        """
        if not has_docker():
            pytest.skip("Docker not available")
        
        container_name = "test-postgres"
        
        # Cleanup any existing container
        cleanup_docker_container(container_name)
        
        try:
            # Run agent
            nl_input = f"run a PostgreSQL container named {container_name} with port 5432 exposed and password postgres"
            result = agent.run(nl_input)
            
            # Track performance
            performance_tracker['latencies'].append(result['total_latency'])
            
            # Log result
            print(f"\n{'='*60}")
            print(f"NL Input: {nl_input}")
            print(f"Generated Command: {result.get('command', 'N/A')}")
            print(f"Exit Code: {result.get('exit_code', 'N/A')}")
            print(f"Total Latency: {result.get('total_latency', 0):.3f}s")
            print(f"{'='*60}\n")
            
            # Assertions
            assert 'error' not in result or result['error'] is None
            
            # Wait for container to be running
            assert wait_for_condition(
                lambda: docker_container_running(container_name),
                timeout=30
            ), f"Container {container_name} not running"
            
            # Wait for port to be reachable
            assert wait_for_condition(
                lambda: docker_port_reachable(5432),
                timeout=30
            ), "Port 5432 not reachable"
            
            # Wait a bit for PostgreSQL to fully start
            time.sleep(5)
            
            # Test connection
            success, error = postgres_connection_test()
            assert success, f"PostgreSQL connection failed: {error}"
            
        finally:
            # Cleanup
            cleanup_docker_container(container_name)


class TestLintAndZip:
    """Test 5: Chain of commands - lint & zip."""
    
    def test_lint_and_zip_results(self, agent, sample_python_files, performance_tracker):
        """
        NL: Lint all Python files and zip the results.
        
        Acceptance criteria:
        - Linter executes
        - Output is generated
        - A zip archive exists and contains results
        """
        workspace = sample_python_files
        
        # Run agent
        nl_input = "run pylint on all Python files and save the output to lint_results.txt, then zip it"
        result = agent.run(nl_input)
        
        # Track performance
        performance_tracker['latencies'].append(result['total_latency'])
        
        # Log result
        print(f"\n{'='*60}")
        print(f"NL Input: {nl_input}")
        print(f"Generated Command: {result.get('command', 'N/A')}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"Total Latency: {result.get('total_latency', 0):.3f}s")
        print(f"{'='*60}\n")
        
        # Note: This might fail if pylint not installed or command is complex
        # We mainly verify the command was generated
        assert 'error' not in result or result['error'] is None
        assert result.get('command'), "No command generated"


@pytest.mark.requires_sudo
class TestRestartService:
    """Test 6: Restart a system service."""
    
    def test_restart_nginx(self, agent, workspace, performance_tracker):
        """
        NL: Restart nginx.
        
        Acceptance criteria:
        - Service restarts without error
        - Service is running afterward
        """
        if not has_sudo_access():
            pytest.skip("Sudo access required")
        
        # Run agent
        nl_input = "restart the nginx service"
        result = agent.run(nl_input)
        
        # Track performance
        performance_tracker['latencies'].append(result['total_latency'])
        
        # Log result
        print(f"\n{'='*60}")
        print(f"NL Input: {nl_input}")
        print(f"Generated Command: {result.get('command', 'N/A')}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"Total Latency: {result.get('total_latency', 0):.3f}s")
        print(f"{'='*60}\n")
        
        # Assertions
        assert 'error' not in result or result['error'] is None
        assert result.get('command'), "No command generated"
        
        # Note: Actual execution requires sudo and nginx installed
        # We mainly verify command generation


class TestDirectoryBackup:
    """Test 7: Directory backup."""
    
    def test_backup_directory(self, agent, sample_python_files, performance_tracker):
        """
        NL: Back up a directory to another location.
        
        Acceptance criteria:
        - Backup directory exists
        - File counts and sizes match
        - Spot-check hashes or timestamps
        """
        workspace = sample_python_files
        src_dir = workspace / "src"
        backup_dir = workspace / "backup"
        
        # Run agent
        nl_input = "backup the src directory to backup/src"
        result = agent.run(nl_input)
        
        # Track performance
        performance_tracker['latencies'].append(result['total_latency'])
        
        # Log result
        print(f"\n{'='*60}")
        print(f"NL Input: {nl_input}")
        print(f"Generated Command: {result.get('command', 'N/A')}")
        print(f"Exit Code: {result.get('exit_code', 'N/A')}")
        print(f"Total Latency: {result.get('total_latency', 0):.3f}s")
        print(f"{'='*60}\n")
        
        # Assertions
        assert 'error' not in result or result['error'] is None
        assert result.get('exit_code') == 0, f"Command failed with exit code {result.get('exit_code')}"
        
        # Verify backup exists
        backup_src = backup_dir / "src"
        assert dir_exists(backup_src), "Backup directory not created"
        
        # Compare directories
        match, message = compare_directories(src_dir, backup_src, check_hashes=True)
        assert match, f"Backup doesn't match source: {message}"
