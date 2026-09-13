def merge_dicts(d1, d2):
    # BUG: doesn't actually merge, just returns d1 unchanged
    return d1


def count_word_frequency(words):
    # BUG: overwrites counts instead of accumulating them
    freq = {}
    for w in words:
        freq[w] = 1
    return freq
