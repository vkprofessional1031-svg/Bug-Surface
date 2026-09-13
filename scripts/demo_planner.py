from tools.file_ops import Workspace
from agents.planner import run_planner

ws = Workspace(root="tests/fixtures/sample_repo")

issue_text = "subtract(a, b) returns a + b instead of a - b"
file_contents = {
    "calculator.py": ws.read_file("calculator.py")
}

plan = run_planner(issue_text, file_contents)
print(plan.model_dump_json(indent=2))
