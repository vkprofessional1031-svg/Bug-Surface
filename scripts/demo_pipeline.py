from orchestrator.graph import run_pipeline

result = run_pipeline(
    repo_path="tests/fixtures/sample_repo",
    issue_text="subtract(a, b) returns a + b instead of a - b",
    target_files=["calculator.py"],
)

if result["success"]:
    print(f"Fixed in {result['attempts']} attempt(s)")
    print("\nDiff:\n")
    print(result["diff"])
else:
    print(f"Failed after {result['attempts']} attempts")
    print(result["last_feedback"])
