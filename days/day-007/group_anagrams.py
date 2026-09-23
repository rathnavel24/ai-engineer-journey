"""LeetCode 49: Group Anagrams.

Given a list of strings, group the anagrams together, in any order.
LeetCode's constraint: every string contains only lowercase letters a-z.
"""


def group_anagrams(strs: list[str]) -> list[list[str]]:
    """Canonical key = tuple of 26 letter counts. O(n*k) time, O(n*k) space."""
    groups: dict[tuple[int, ...], list[str]] = {}
    for word in strs:
        counts = [0] * 26
        for ch in word:
            counts[ord(ch) - ord("a")] += 1
        key = tuple(counts)  # a list would be rejected: mutable -> unhashable
        groups.setdefault(key, []).append(word)
    return list(groups.values())


def _normalize(groups: list[list[str]]) -> list[list[str]]:
    """Answer order doesn't matter, so sort inside and across groups before comparing."""
    return sorted(sorted(g) for g in groups)


if __name__ == "__main__":
    assert _normalize(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])) == _normalize(
        [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]
    )
    assert group_anagrams([]) == []  # no strings at all
    assert group_anagrams([""]) == [[""]]  # single empty string
    assert group_anagrams(["", ""]) == [["", ""]]  # empty strings are anagrams of each other
    assert group_anagrams(["a"]) == [["a"]]  # single character
    assert group_anagrams(["abc", "bca", "cab", "bac"]) == [["abc", "bca", "cab", "bac"]]  # one group holds everything
    assert _normalize(group_anagrams(["ab", "ba", "abc"])) == [["ab", "ba"], ["abc"]]

    # The trap: a list can't be a dict key, because lists are mutable and so unhashable.
    list_key = [0] * 26
    try:
        hash(list_key)
    except TypeError as e:
        assert "unhashable" in str(e)
    else:
        raise AssertionError("expected TypeError when hashing a list")

    print("all group_anagrams tests passed")
