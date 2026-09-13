from range_utils import sum_range, is_palindrome


def test_sum_range_inclusive():
    assert sum_range(1, 5) == 15  # 1+2+3+4+5


def test_is_palindrome():
    assert is_palindrome("racecar") is True


def test_is_palindrome_false():
    assert is_palindrome("hello") is False
