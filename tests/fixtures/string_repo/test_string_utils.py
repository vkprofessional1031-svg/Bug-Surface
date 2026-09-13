from string_utils import reverse_words, count_vowels


def test_reverse_words():
    assert reverse_words("hello world") == "world hello"


def test_count_vowels():
    assert count_vowels("Hello") == 2
