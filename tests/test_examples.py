import pytest
from pathlib import Path
from subprocess import run

EXAMPLES_DIR = Path("examples")

def get_example_files():
    return list(EXAMPLES_DIR.glob("*.py"))

@pytest.mark.parametrize("example_file", get_example_files())
def test_example(example_file):
    result = run(["python", example_file.as_posix()], capture_output=True, text=True)
    assert result.returncode == 0, f"Error in {example_file.name}: {result.stderr}"
