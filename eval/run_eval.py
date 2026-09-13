"""Runs the full agent pipeline against every benchmark issue and reports
success rate, attempts-to-fix, and wall-clock time per issue."""
import time
import pandas as pd

from orchestrator.graph import run_pipeline
from eval.benchmark_issues import BENCHMARK_ISSUES


def main():
    rows = []
    for issue in BENCHMARK_ISSUES:
        print(f"Running: {issue['name']}...")
        start = time.time()
        try:
            result = run_pipeline(
                repo_path=issue["repo_path"],
                issue_text=issue["issue_text"],
                target_files=issue["target_files"],
                test_cmd=issue.get("test_cmd", "pytest -q"),
            )
            elapsed = time.time() - start
            rows.append({
                "issue": issue["name"],
                "success": result["success"],
                "attempts": result["attempts"],
                "seconds": round(elapsed, 1),
            })
            status = "PASS" if result["success"] else "FAIL"
            print(f"  {status} in {result['attempts']} attempt(s), {elapsed:.1f}s")
        except Exception as e:
            elapsed = time.time() - start
            rows.append({
                "issue": issue["name"],
                "success": False,
                "attempts": None,
                "seconds": round(elapsed, 1),
                "error": str(e),
            })
            print(f"  ERROR: {e}")

    df = pd.DataFrame(rows)
    df.to_csv("eval/results.csv", index=False)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(df.to_string(index=False))
    success_rate = df["success"].mean() * 100
    avg_attempts = df[df["success"]]["attempts"].mean()
    print(f"\nSuccess rate: {success_rate:.0f}%")
    print(f"Avg attempts (successful runs): {avg_attempts:.1f}")


if __name__ == "__main__":
    main()
