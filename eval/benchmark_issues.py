"""Defines the benchmark: a fixed set of known bugs across small repos,
each with an issue description an agent has to work from -- not the bug's
exact line number or fix, just a plain-English symptom report."""

BENCHMARK_ISSUES = [
    {
        "name": "calculator_subtract",
        "repo_path": "tests/fixtures/sample_repo",
        "issue_text": "subtract(a, b) returns a + b instead of a - b",
        "target_files": ["calculator.py"],
    },
    {
        "name": "calculator_divide_zero",
        "repo_path": "tests/fixtures/sample_repo",
        "issue_text": "divide(a, b) crashes when b is zero. It should raise "
                       "a clear, descriptive error instead of crashing.",
        "target_files": ["calculator.py"],
    },
    {
        "name": "string_reverse_words",
        "repo_path": "tests/fixtures/string_repo",
        "issue_text": "reverse_words(sentence) is supposed to reverse the "
                       "order of words in a sentence, but it currently "
                       "returns the sentence unchanged.",
        "target_files": ["string_utils.py"],
    },
    {
        "name": "list_unique_items",
        "repo_path": "tests/fixtures/list_repo",
        "issue_text": "unique_items(lst) is supposed to remove duplicate "
                       "values while preserving order, but it currently "
                       "returns the list unchanged.",
        "target_files": ["list_utils.py"],
    },
]
