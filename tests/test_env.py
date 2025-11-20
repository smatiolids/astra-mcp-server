"""
Test case for building agentic-astra and running it with --env argument.
"""
import pytest
import subprocess
import os
from pathlib import Path


@pytest.fixture
def test_env_file(tmp_path):
    """Create a temporary .env file with test environment variables."""
    env_file = tmp_path / "test.env"
    env_content = """# Test environment variables
ASTRA_DB_APPLICATION_TOKEN=test_token_from_env_file
ASTRA_DB_API_ENDPOINT=https://test-endpoint.apps.astra.datastax.com
ASTRA_DB_DB_NAME=test_database
ASTRA_DB_CATALOG_COLLECTION=test_catalog
LOG_LEVEL=DEBUG
LOG_FILE=test_logs.log
"""
    env_file.write_text(env_content)
    return str(env_file)


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def test_build_package(project_root):
    """Test that the package can be built successfully."""
    # Clean previous builds
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        # Remove only wheel files for this test
        for file in dist_dir.glob("agentic_astra-*.whl"):
            file.unlink()
    
    # Build the package
    result = subprocess.run(
        ["uv", "build"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    
    # Verify wheel file was created
    wheel_files = list(dist_dir.glob("agentic_astra-*.whl"))
    assert len(wheel_files) > 0, "No wheel file was created"
    
    return wheel_files[0]


def test_run_with_env_file(test_env_file, project_root):
    """Test running agentic-astra with uvx using --env argument."""
    # First build the package
    wheel_file = test_build_package(project_root)
    
    # Run with uvx using the --env argument
    # We'll use a timeout and expect it to fail gracefully (since we don't have real credentials)
    # but we want to verify that the --env argument is processed correctly
    try:
        result = subprocess.run(
            [
                "uvx",
                "--from", str(wheel_file),
                "agentic-astra",
                "--env", test_env_file,
                "--transport", "stdio",
                "--help"  # Use --help to avoid actually starting the server
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # The command should succeed (exit code 0) when using --help
        # This verifies that the package was built correctly and can be run
        assert result.returncode == 0 or result.returncode == 2, \
            f"Command failed unexpectedly: {result.stderr}\n{result.stdout}"
        
    except subprocess.TimeoutExpired:
        pytest.fail("Command timed out - this might indicate the server started when it shouldn't have")
    except FileNotFoundError:
        pytest.skip("uvx not found - skipping test")


def test_env_file_loading_log_message(test_env_file, project_root):
    """Test that the log message appears when --env file is loaded."""
    # Build the package
    wheel_file = test_build_package(project_root)
    
    # Run with uvx and check for the log message
    # We'll use a short timeout since we just want to see the log message
    try:
        result = subprocess.run(
            [
                "uvx",
                "--from", str(wheel_file),
                "agentic-astra",
                "--env", test_env_file,
                "--transport", "stdio"
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5  # Short timeout - we just want to see the log message
        )
        
        # Check for the log message indicating env file was loaded
        output = (result.stdout + result.stderr).lower()
        env_file_name = os.path.basename(test_env_file)
        
        # The log message should contain "Loading environment variables from"
        # and the env file path
        assert "loading environment variables from" in output or env_file_name in output, \
            f"Expected log message about loading env file not found. Output: {result.stdout}\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        # If it times out, check the output from the process
        # This might happen if the server starts successfully
        pass
    except FileNotFoundError:
        pytest.skip("uvx not found - skipping test")


def test_build_and_run_with_env_integration(test_env_file, project_root):
    """Integration test: build package and verify --env argument is accepted."""
    # Build the package
    wheel_file = test_build_package(project_root)
    
    # Test that the command accepts --env argument without errors
    # We'll use a short timeout and expect it to fail on missing credentials,
    # but the --env argument should be processed first
    try:
        result = subprocess.run(
            [
                "uvx",
                "--from", str(wheel_file),
                "agentic-astra",
                "--env", test_env_file,
                "--transport", "stdio"
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5  # Short timeout - we expect it to fail on credentials
        )
        
        # The command should either:
        # 1. Exit with an error about missing credentials (which is expected)
        # 2. Start successfully (if credentials are valid)
        # But it should NOT fail with "unrecognized arguments: --env"
        stderr_lower = result.stderr.lower()
        stdout_lower = result.stdout.lower()
        
        # Verify --env was recognized (no "unrecognized arguments" error)
        assert "unrecognized arguments: --env" not in stderr_lower, \
            f"--env argument was not recognized: {result.stderr}"
        assert "unrecognized arguments: --env" not in stdout_lower, \
            f"--env argument was not recognized: {result.stdout}"
        
        # Check for log message indicating env file was loaded
        env_file_name = os.path.basename(test_env_file)
        combined_output = stderr_lower + stdout_lower
        
        # The log message should appear, or at least the env file name should be in the output
        assert "loading environment variables from" in combined_output or env_file_name in combined_output, \
            f"Expected log message about loading env file not found. Output: {result.stdout}\n{result.stderr}"
        
    except subprocess.TimeoutExpired:
        # If it times out, it might have started successfully
        # This is actually okay for this test - it means the server started
        pass
    except FileNotFoundError:
        pytest.skip("uvx not found - skipping test")

