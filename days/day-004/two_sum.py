"""LeetCode 1: Two Sum.

Given an array of integers nums and an integer target, return the indices
of the two numbers that add up to target. Each input has exactly one
solution, and the same element can't be used twice.
"""


def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}  # value -> index
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return [seen[complement], i]
        seen[n] = i
    return []


if __name__ == "__main__":
    print(two_sum([2, 7, 11, 15], 9))  # [0, 1]
    print(two_sum([3, 2, 4], 6))  # [1, 2]
    print(two_sum([3, 3], 6))  # [0, 1]
