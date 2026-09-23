"""LeetCode 242: Valid Anagram.

Given two strings s and t, return True if t is an anagram of s - the same
characters with the same counts, in any order.
"""


def is_anagram(s: str, t: str) -> bool:
    """Frequency counting: O(n) time, O(k) space (k = distinct characters)."""
    if len(s) != len(t):
        return False

    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    for ch in t:
        if counts.get(ch, 0) == 0:
            return False
        counts[ch] -= 1
    return True


def is_anagram_sorted(s: str, t: str) -> bool:
    """Sorting: O(n log n) time, O(n) space (sorted() builds new lists)."""
    if len(s) != len(t):
        return False
    return sorted(s) == sorted(t)


if __name__ == "__main__":
    for fn in (is_anagram, is_anagram_sorted):
        assert fn("anagram", "nagaram") is True
        assert fn("rat", "car") is False
        assert fn("", "") is True  # empty strings
        assert fn("a", "a") is True  # single character
        assert fn("a", "b") is False
        assert fn("ab", "a") is False  # length check short-circuits
        assert fn("aacc", "ccac") is False  # same letters, different counts
        assert fn("café", "éfac") is True  # non a-z characters still work
    print("all valid_anagram tests passed")
