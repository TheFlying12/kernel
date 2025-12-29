"""
Utility functions for ktml-agent tests.
"""

import os
import subprocess
import hashlib
import time
from pathlib import Path
from typing import List, Tuple, Optional
import docker


def file_exists(path: Path) -> bool:
    """Check if file exists."""
    return path.exists() and path.is_file()


def dir_exists(path: Path) -> bool:
    """Check if directory exists."""
    return path.exists() and path.is_dir()


def count_files(directory: Path, pattern: str = "*") -> int:
    """Count files matching pattern in directory."""
    return len(list(directory.rglob(pattern)))


def file_hash(path: Path) -> str:
    """Calculate SHA-256 hash of file."""
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def grep_count(directory: Path, pattern: str, file_pattern: str = "*.py") -> int:
    """Count occurrences of pattern in files."""
    count = 0
    for file_path in directory.rglob(file_pattern):
        if file_path.is_file():
            try:
                content = file_path.read_text()
                count += content.count(pattern)
            except Exception:
                pass
    return count


def git_branch_exists(branch_name: str, workspace: Path) -> bool:
    """Check if git branch exists locally."""
    try:
        result = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )
        return branch_name in result.stdout
    except Exception:
        return False


def git_remote_branch_exists(branch_name: str, workspace: Path, remote: str = "origin") -> bool:
    """Check if git branch exists on remote."""
    try:
        result = subprocess.run(
            ['git', 'ls-remote', '--heads', remote, branch_name],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )
        return branch_name in result.stdout
    except Exception:
        return False


def docker_container_running(container_name: str) -> bool:
    """Check if Docker container is running."""
    try:
        client = docker.from_env()
        containers = client.containers.list(filters={'name': container_name})
        return len(containers) > 0
    except Exception:
        return False


def docker_port_reachable(port: int, host: str = "localhost", timeout: int = 5) -> bool:
    """Check if Docker port is reachable."""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except Exception:
        return False
    finally:
        sock.close()


def postgres_connection_test(host: str = "localhost", port: int = 5432, 
                             user: str = "postgres", password: str = "postgres",
                             timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """Test PostgreSQL connection."""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=timeout
        )
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def service_is_running(service_name: str) -> bool:
    """Check if system service is running (Linux/macOS)."""
    try:
        # Try systemctl first (Linux)
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return 'active' in result.stdout
        
        # Try service command (older systems)
        result = subprocess.run(
            ['service', service_name, 'status'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def cleanup_docker_container(container_name: str):
    """Stop and remove Docker container."""
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True, filters={'name': container_name})
        for container in containers:
            container.stop()
            container.remove()
    except Exception:
        pass


def wait_for_condition(condition_func, timeout: int = 30, interval: float = 0.5) -> bool:
    """
    Wait for condition function to return True.
    
    Args:
        condition_func: Function that returns bool
        timeout: Maximum wait time in seconds
        interval: Check interval in seconds
        
    Returns:
        bool: True if condition met, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False


def compare_directories(dir1: Path, dir2: Path, check_hashes: bool = False) -> Tuple[bool, str]:
    """
    Compare two directories.
    
    Args:
        dir1: First directory
        dir2: Second directory
        check_hashes: Whether to compare file hashes
        
    Returns:
        Tuple of (match: bool, message: str)
    """
    # Check file counts
    files1 = list(dir1.rglob("*"))
    files2 = list(dir2.rglob("*"))
    
    if len(files1) != len(files2):
        return False, f"File count mismatch: {len(files1)} vs {len(files2)}"
    
    # Check file names
    names1 = sorted([f.relative_to(dir1) for f in files1 if f.is_file()])
    names2 = sorted([f.relative_to(dir2) for f in files2 if f.is_file()])
    
    if names1 != names2:
        return False, "File names don't match"
    
    # Check hashes if requested
    if check_hashes:
        for name in names1:
            file1 = dir1 / name
            file2 = dir2 / name
            
            if file_hash(file1) != file_hash(file2):
                return False, f"Hash mismatch for {name}"
    
    return True, "Directories match"


def has_sudo_access() -> bool:
    """Check if user has sudo access."""
    try:
        result = subprocess.run(
            ['sudo', '-n', 'true'],
            capture_output=True,
            timeout=1
        )
        return result.returncode == 0
    except Exception:
        return False


def has_docker() -> bool:
    """Check if Docker is available."""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False
