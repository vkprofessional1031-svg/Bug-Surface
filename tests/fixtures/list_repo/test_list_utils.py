from list_utils import unique_items, find_max


def test_unique_items():
    assert unique_items([1, 2, 2, 3, 3, 3]) == [1, 2, 3]


def test_find_max():
    assert find_max([3, 1, 4, 1, 5]) == 5
