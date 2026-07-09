# tests/test_yaml.py
import yaml
from pathlib import Path

def test_all_workflow_yamls_parse():
    workflows = list(Path(".github/workflows").glob("*.yml")) + \
                list(Path(".github/workflows").glob("*.yaml"))
    assert workflows, "No workflow files found — wrong cwd?"
    for wf in workflows:
        with open(wf) as f:
            yaml.safe_load(f)  # raises on syntax errors

def test_workflow_has_required_structure():
    wf_path = Path(".github/workflows/sync_to_hf.yml")
    assert wf_path.exists(), f"{wf_path} not found — renamed?"
    wf = yaml.safe_load(wf_path.read_text())
    assert "jobs" in wf
    # PyYAML quirk: bare `on:` parses as boolean True, so check both
    assert "on" in wf or True in wf
