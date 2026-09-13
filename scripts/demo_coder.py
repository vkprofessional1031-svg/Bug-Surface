from tools.file_ops import Workspace
from agents.planner import run_planner
from agents.coder import run_coder

ws = Workspace(root="tests/fixtures/sample_repo")

issue_text = "subtract(a, b) returns a + b instead of a - b"
file_contents = {"calculator.py": ws.read_file("calculator.py")}

plan = run_planner(issue_text, file_contents)
print("PLAN:")
print(plan.model_dump_json(indent=2))

result = run_coder(plan, file_contents)
print("\nCODER OUTPUT:")
for change in result.changes:
    print(f"\n--- {change.file_path} ---")
    print(f"Explanation: {change.explanation}")
    print(change.new_content)
