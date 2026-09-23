# Day 7

## 1. Valid Anagram (LeetCode 242)

**Approach.** First the one-line check: if the lengths differ, it can't be an anagram. Then count each character of `s` in a dict and walk `t`, decrementing; if any character's count is already 0 when `t` needs it, return False. The second approach sorts both strings and compares them.

**Complexity** (n = length of each string, k = number of distinct characters):

| Approach | Time | Space |
|---|---|---|
| Frequency count (dict) | O(n) | O(k), which is O(1) for a–z since k ≤ 26 |
| Sorting | O(n log n) | O(n), because Python strings are immutable, so `sorted()` builds new lists |

Counting wins on time; for a–z it also wins on space. Sorting is shorter to write and needs no counting logic at all.

**Mistake I'd likely make under pressure.** Only checking that each character of `t` *exists* in `s`, instead of decrementing counts. That passes `"rat"` / `"car"` but wrongly accepts `"aacc"` / `"ccac"` (same letters, different counts), which is why that case is in my asserts.

**Follow-up: what changes if the input can contain any Unicode character, not just a–z?**

- A fixed 26-slot array (`ord(ch) - ord("a")`) breaks: anything outside a–z lands in the wrong slot or goes out of range. A dict works for any character, which is why I used one; space becomes O(k) distinct characters instead of O(1). Sorting still works unchanged.
- Characters that look the same can be different code points. `é` can be one code point (U+00E9) or `e` + a combining accent (2 code points). I checked: they compare unequal and have lengths 1 vs 2, but become equal after `unicodedata.normalize("NFC", ...)`. So normalize both strings first.
- If upper and lowercase should match, use `str.casefold()` rather than `lower()`. Casefolding can change the length (`"Straße"` goes from 6 to 7 characters as `"strasse"`), so the length check has to happen **after** normalizing, not before.
- Some things a user sees as one character, like family emoji joined by zero-width joiners, are several code points. Counting code points could call two strings anagrams just by rearranging pieces of an emoji. Handling that properly means counting grapheme clusters, which needs a library such as `regex` with `\X`.

## 2. Group Anagrams (LeetCode 49)

**Approach.** Anagrams share a *canonical key*, so group words by it in a dict of `key → list of words`. I used the count-based key: a tuple of 26 letter counts per word. Every anagram produces the same tuple, so `setdefault(key, []).append(word)` groups them in one pass.

**Complexity** (n = number of strings, k = length of the longest string):

| Key | Time | Space |
|---|---|---|
| Sorted string, `"".join(sorted(w))` | O(n · k log k) | O(n · k) |
| 26-count tuple (implemented) | O(n · k), plus O(26) per word to build and hash the tuple, which is a constant | O(n · k) for the output, plus O(n · 26) for keys |

**The count key is faster asymptotically**: O(nk) vs O(nk log k). I timed both on 2,000 random words to see if that holds in practice:

| k (word length) | sort key | count key |
|---|---|---|
| 5 | 0.002 s | 0.003 s |
| 100 | 0.043 s | 0.023 s |
| 1000 | 0.505 s | 0.193 s |

For short words the sort key is actually a little faster, because `sorted()` runs in C while my counting loop is pure Python. The log k advantage only shows once words get long. Big-O tells you how the cost grows, not which version wins at every size.

**The trap: why a list can't be a dict key.** Dict keys must be *hashable*: the dict stores each key by its hash and relies on that hash never changing. A list is mutable, so you could change it after inserting it and the dict would look in the wrong place. Python refuses up front with `TypeError: unhashable type: 'list'`. The fix is `tuple(counts)`, since tuples are immutable and hashable. My file asserts that hashing a list raises this error.

**Mistake I'd likely make under pressure.** Either the list-as-key `TypeError` above, or the sneakier fix of turning the counts into a string *without a separator*. Counts `[1, 11]` and `[11, 1]` both become `"111"`, so two non-anagrams silently land in the same group with no error. Use a tuple, or join with a separator like `"#"`.

## Recall quiz

**(Day 6) Why does a timer wrapped around `call_next` in `BaseHTTPMiddleware` give the wrong latency for an SSE endpoint?**

Because `call_next` returns as soon as the response *starts* (status and headers are ready). What comes back is a response whose body hasn't been streamed yet; the tokens flow *after* your `dispatch` has already stopped the timer. So the timer measures neither time-to-first-token nor total latency, only "how long until headers."

I measured it rather than guessing (Starlette 1.6.0, a streaming endpoint yielding 3 chunks 0.3 s apart): the client received chunks at 0.32 s, 0.62 s and 0.92 s, but the timer around `call_next` read **0.00 s**. To time the stream correctly you have to hook the moment each body chunk is actually *sent*, which is what my raw ASGI middleware does by wrapping `send`.

**Correction to my Day 6 answer:** Day 6 said `BaseHTTPMiddleware` buffers the whole response. On this Starlette version it doesn't: chunks still reached the client progressively. The real problem is that `call_next` hands back control before the body streams, so any timing or body inspection done there is wrong (and if you read the whole `body_iterator` to count tokens before returning, *you* create the buffering yourself). Raw ASGI middleware is still the right choice, just for this more accurate reason.

**(Day 6) Why should a logging failure in your middleware never cause `/chat` to fail, and how did you enforce that?**

Logging is there to *observe* the feature, not to be part of it. If Postgres being down could break chat, every monitoring outage would become a user-facing outage, and a missing log row is far cheaper than a failed answer. I enforced it two ways: the insert runs only **after** `await self.app(...)` returns (every response message has already gone through `send`, so the client already has the full answer), and the insert (including the lazy pool creation) is wrapped in `try/except Exception` that prints the error and returns normally. The Day 6 notebook demonstrates this with a fake DB that raises `ConnectionError`: the client still gets every chunk on time.

**(Day 4) In Two Sum, what does the hash map store as keys and values, and why does one pass over the array work?**

Keys are the **numbers seen so far**; values are their **indices**. At each position `i` I look up the complement `target - nums[i]`. One pass works because any valid pair `(j, i)` with `j < i` is found when the loop reaches `i`, since `nums[j]` was stored earlier. I check *before* storing the current number, so an element can't be paired with itself (for example `[3, 3]` with target 6 correctly returns `[0, 1]`).

**(Day 4) In Contains Duplicate, what do you trade by using a hash set instead of sorting first?**

**Memory for speed.** Hash set: O(n) time but O(n) extra memory for the set. Sort first, then compare neighbours: O(n log n) time, but it can use little extra memory (O(1) with an in-place sort, ignoring the sort's own working memory; Python's Timsort can use up to O(n)). Sorting in place also *changes the caller's list*, so you'd need a copy (and O(n) memory again) if the input must stay untouched. The set also returns as soon as it finds the first duplicate, while sorting has to finish the whole sort first.

## Reflection

Measuring beat remembering twice today: the sort key is faster than the "asymptotically better" count key on short words, and `BaseHTTPMiddleware` doesn't buffer the way my Day 6 answer claimed.
The habit to keep: when a claim is cheap to test, test it before writing it down.
