"""Defines the benchmark: a fixed set of known bugs across small repos,
each with an issue description an agent has to work from, and the specific
test(s) that determine success -- scoped to that issue only, so an agent
isn't penalized (or accidentally credited) for unrelated bugs in the same
test file."""

BENCHMARK_ISSUES = [
    {
        "name": "calculator_subtract",
        "repo_path": "tests/fixtures/sample_repo",
        "issue_text": "subtract(a, b) returns a + b instead of a - b",
        "target_files": ["calculator.py"],
        "test_cmd": "pytest -q -k test_subtract",
    },
    {
        "name": "calculator_divide_zero",
        "repo_path": "tests/fixtures/sample_repo",
        "issue_text": "divide(a, b) crashes when b is zero. It should raise "
                       "a clear, descriptive error instead of crashing.",
        "target_files": ["calculator.py"],
        "test_cmd": "pytest -q -k test_divide",
    },
    {
        "name": "string_reverse_words",
        "repo_path": "tests/fixtures/string_repo",
        "issue_text": "reverse_words(sentence) is supposed to reverse the "
                       "order of words in a sentence, but it currently "
                       "returns the sentence unchanged.",
        "target_files": ["string_utils.py"],
        "test_cmd": "pytest -q -k test_reverse_words",
    },
    {
        "name": "list_unique_items",
        "repo_path": "tests/fixtures/list_repo",
        "issue_text": "unique_items(lst) is supposed to remove duplicate "
                       "values while preserving order, but it currently "
                       "returns the list unchanged.",
        "target_files": ["list_utils.py"],
        "test_cmd": "pytest -q -k test_unique_items",
    },
    {
        "name": "dict_merge",
        "repo_path": "tests/fixtures/dict_repo",
        "issue_text": "merge_dicts(d1, d2) is supposed to combine both "
                       "dictionaries (with d2's values taking priority on "
                       "overlapping keys), but it currently just returns "
                       "d1 unchanged.",
        "target_files": ["dict_utils.py"],
        "test_cmd": "pytest -q -k test_merge_dicts",
    },
    {
        "name": "dict_word_frequency",
        "repo_path": "tests/fixtures/dict_repo",
        "issue_text": "count_word_frequency(words) is supposed to count how "
                       "many times each word appears in the list, but it "
                       "currently just sets each word's count to 1, "
                       "overwriting instead of accumulating.",
        "target_files": ["dict_utils.py"],
        "test_cmd": "pytest -q -k test_count_word_frequency",
    },
    {
        "name": "range_sum_off_by_one",
        "repo_path": "tests/fixtures/range_repo",
        "issue_text": "sum_range(start, end) is supposed to sum all integers "
                       "from start to end INCLUSIVE, but it currently "
                       "excludes the end value due to an off-by-one error.",
        "target_files": ["range_utils.py"],
        "test_cmd": "pytest -q -k test_sum_range",
    },
]
