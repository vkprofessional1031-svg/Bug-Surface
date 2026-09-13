from orchestrator.graph import run_pipeline

result = run_pipeline(
    repo_path="tests/fixtures/sample_repo",
    issue_text="modulo(a, b) crashes when b is zero. It should raise a "
               "clear, descriptive error instead of crashing.",
    target_files=["calculator.py"],
    issue_name="calculator_modulo_zero",
    test_cmd="pytest -q -k test_modulo_by_zero",
)

if result["success"]:
    print(f"Success: {result['success']}")
    print(f"Attempts: {result['attempts']}")
    print(f"Used memory: {result.get('used_memory')}")
    print("\nDiff:\n")
    print(result["diff"])
else:
    print(f"Failed after {result['attempts']} attempts")
    print(result["last_feedback"])
