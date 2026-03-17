import pytest
import os
import shutil
from application.agent.tool_registry import ToolRegistry
from application.constants import WORKSPACE_DIR

TEST_WORKSPACE = os.path.join(os.path.dirname(__file__), "test_workspace")


@pytest.fixture(autouse=True)
def clean_workspace(monkeypatch):
    monkeypatch.setattr(
        "application.agent.tool_registry.WORKSPACE_DIR", TEST_WORKSPACE
    )
    os.makedirs(TEST_WORKSPACE, exist_ok=True)
    yield
    shutil.rmtree(TEST_WORKSPACE, ignore_errors=True)


@pytest.mark.asyncio
async def test_write_and_read_file():
    registry = ToolRegistry()
    result = await registry.write_file("hello.txt", "Hello, world!")
    assert "hello.txt" in result

    content = await registry.read_file("hello.txt")
    assert content == "Hello, world!"


@pytest.mark.asyncio
async def test_read_nonexistent_file():
    registry = ToolRegistry()
    result = await registry.read_file("doesnotexist.txt")
    assert "Error" in result


@pytest.mark.asyncio
async def test_path_traversal_blocked():
    registry = ToolRegistry()
    result = await registry.write_file("../../evil.txt", "bad content")
    assert "Error" in result


@pytest.mark.asyncio
async def test_run_python():
    registry = ToolRegistry()
    await registry.write_file("test_script.py", "print('hello from test')")
    result = await registry.run_python("test_script.py")
    assert "hello from test" in result


@pytest.mark.asyncio
async def test_run_python_with_error():
    registry = ToolRegistry()
    await registry.write_file("bad_script.py", "raise ValueError('intentional error')")
    result = await registry.run_python("bad_script.py")
    assert "STDERR" in result or "Error" in result


@pytest.mark.asyncio
async def test_list_files_empty():
    registry = ToolRegistry()
    result = await registry.list_files()
    assert "empty" in result.lower() or result == ""


@pytest.mark.asyncio
async def test_list_files_after_write():
    registry = ToolRegistry()
    await registry.write_file("file1.py", "x = 1")
    await registry.write_file("file2.py", "y = 2")
    result = await registry.list_files()
    assert "file1.py" in result
    assert "file2.py" in result
