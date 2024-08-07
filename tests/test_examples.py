from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch
from interact.handlers import OpenAiLLM

import pytest

EXAMPLES_DIR = Path("examples")
llm_call_count = 0


def get_example_files():
    return list(EXAMPLES_DIR.glob("*.py"))

def openai_llm_init_side_effect(self, *args, **kwargs):
    self.role = "llm"

async def dummy_openai_llm_process_side_effect(hanlder, msg, csd):
    return msg


async def company_name_openai_llm_process_side_effect(hanlder, msg, csd):
    global llm_call_count
    if llm_call_count == 0:
        llm_call_count += 1
        return "The Sock Spot"
    else:
        return "The Sock Spot: Step into Comfort"


def import_module_from_path(path: Path):
    spec = spec_from_file_location(path.stem, path)
    assert spec is not None, f"Could not load {path}"
    module = module_from_spec(spec)
    assert spec.loader is not None, f"Could not load {path}"
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("example_file", get_example_files())
def test_example(example_file: Path):
    global llm_call_count
    llm_call_count = 0

    side_effect = dummy_openai_llm_process_side_effect
    if "company_name" in example_file.stem:
        side_effect = company_name_openai_llm_process_side_effect
    with patch.object(OpenAiLLM, "__init__", openai_llm_init_side_effect):
        with patch("interact.handlers.OpenAiLLM.process", side_effect):
            module = import_module_from_path(example_file)
            module.main()
