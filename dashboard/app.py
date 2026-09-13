"""Streamlit dashboard for the Autonomous Dev Agent.

Two views: benchmark results (from eval/results.csv) and a live
run panel that lets you submit a new issue and watch the pipeline
execute against one of the fixture repos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from orchestrator.graph import run_pipeline
from memory.store import _get_collection

st.set_page_config(page_title="Autonomous Dev Agent", layout="wide")
st.title("🤖 Autonomous Dev Agent")
st.caption("An AI agent that plans, codes, tests, self-corrects, and reviews bug fixes autonomously.")

tab1, tab2, tab3 = st.tabs(["📊 Benchmark Results", "🔴 Live Run", "🧠 Memory Store"])

with tab1:
    st.header("Evaluation Benchmark")
    results_path = Path("eval/results.csv")
    if results_path.exists():
        df = pd.read_csv(results_path)
        col1, col2, col3 = st.columns(3)
        success_rate = df["success"].mean() * 100
        avg_attempts = df[df["success"]]["attempts"].mean()
        col1.metric("Success Rate", f"{success_rate:.0f}%")
        col2.metric("Avg Attempts", f"{avg_attempts:.1f}")
        col3.metric("Issues Tested", len(df))

        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("issue")["attempts"])
    else:
        st.info("No results yet. Run `python -m eval.run_eval` first.")

with tab2:
    st.header("Run the Agent Live")
    st.write("Submit a new issue and watch the full pipeline execute.")

    repo_options = {
        "Calculator (arithmetic bugs)": "tests/fixtures/sample_repo",
        "String utils": "tests/fixtures/string_repo",
        "List utils": "tests/fixtures/list_repo",
        "Dict utils": "tests/fixtures/dict_repo",
        "Range utils": "tests/fixtures/range_repo",
    }

    repo_label = st.selectbox("Target repo", list(repo_options.keys()))
    issue_text = st.text_area(
        "Issue description",
        placeholder="e.g. subtract(a, b) returns a + b instead of a - b",
    )
    target_file = st.text_input("Target file (relative path)", placeholder="e.g. calculator.py")
    test_cmd = st.text_input("Test command", value="pytest -q")

    if st.button("Run agent", type="primary"):
        if not issue_text or not target_file:
            st.warning("Please fill in the issue description and target file.")
        else:
            with st.spinner("Planning, coding, testing, reviewing..."):
                result = run_pipeline(
                    repo_path=repo_options[repo_label],
                    issue_text=issue_text,
                    target_files=[target_file],
                    issue_name=f"live_run_{hash(issue_text) % 10000}",
                    test_cmd=test_cmd,
                )

            if result["success"]:
                st.success(f"✅ Fixed in {result['attempts']} attempt(s)")
                if result.get("used_memory"):
                    st.info("🧠 Used memory from a similar past fix")
                st.subheader("Plan")
                st.json(result["plan"].model_dump())
                st.subheader("Diff")
                st.code(result["diff"], language="diff")
                st.subheader("Review reasoning")
                st.write(result["review"].reasoning)
            else:
                st.error(f"❌ Failed after {result['attempts']} attempts")
                st.text(result["last_feedback"])

with tab3:
    st.header("Memory Store")
    try:
        collection = _get_collection()
        count = collection.count()
        st.metric("Stored fixes", count)
        if count > 0:
            all_items = collection.get()
            for i, (doc_id, meta) in enumerate(zip(all_items["ids"], all_items["metadatas"])):
                with st.expander(f"{doc_id}"):
                    st.write("**Issue:**", meta["issue_text"])
                    st.write("**Review notes:**", meta["review_reasoning"])
        else:
            st.info("No fixes stored yet. Run the benchmark or a live issue first.")
    except Exception as e:
        st.warning(f"Could not load memory store: {e}")
