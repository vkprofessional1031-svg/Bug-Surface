def sum_range(start, end):
    # BUG: off-by-one, excludes `end` when it should be inclusive
    total = 0
    for i in range(start, end):
        total += i
    return total


def is_palindrome(s):
    return s == s[::-1]
