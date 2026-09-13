from dict_utils import merge_dicts, count_word_frequency


def test_merge_dicts():
    assert merge_dicts({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_merge_dicts_overlap():
    assert merge_dicts({"a": 1}, {"a": 2}) == {"a": 2}


def test_count_word_frequency():
    assert count_word_frequency(["a", "b", "a", "a", "c"]) == {"a": 3, "b": 1, "c": 1}
