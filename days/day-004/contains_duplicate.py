"""LeetCode 217: Contains Duplicate.

Given an integer array nums, return True if any value appears at least
twice, and False if every element is distinct.
"""


def contains_duplicate(nums: list[int]) -> bool:
    seen = set()
    for n in nums:
        if n in seen:
            return True
        seen.add(n)
    return False


if __name__ == "__main__":
    print(contains_duplicate([1, 2, 3, 1]))  # True
    print(contains_duplicate([1, 2, 3, 4]))  # False
    print(contains_duplicate([1, 1, 1, 3, 3, 4, 3, 2, 4, 2]))  # True
    print(contains_duplicate([]))  # False
