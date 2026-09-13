from orchestrator.graph import run_pipeline

result = run_pipeline(
    repo_path="tests/fixtures/sample_repo",
    issue_text="divide(a, b) crashes when b is zero. It should raise a clear, "
               "descriptive error instead of crashing.",
    target_files=["calculator.py"],
)

if result["success"]:
    print(f"Fixed in {result['attempts']} attempt(s)")
    print("\nDiff:\n")
    print(result["diff"])
else:
    print(f"Failed after {result['attempts']} attempts")
    print(result["last_feedback"])
