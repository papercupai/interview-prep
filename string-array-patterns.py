#!/usr/bin/env python3
"""The eight string/array patterns worth having in muscle memory.

Format for each: the three-line English skeleton you rebuild the code from,
the shortest correct implementation, and THE TOKEN THAT BREAKS IT with a
failing example attached. Memorising code fails under time pressure;
memorising a skeleton plus its two failure modes does not.

Run to verify:  python3 string-array-patterns.py
"""
from collections import Counter, defaultdict
import bisect


# 1 -- LONGEST SUBSTRING WITHOUT REPEATING CHARACTERS -------------------------
# Skeleton: walk right. If this char was seen INSIDE the window, jump left past
#           it. Record the width.
# O(n) time, O(min(n, alphabet)) space.
def longest_unique_substring(s):
    last = {}                       # char -> most recent index
    left = best = 0
    for right, ch in enumerate(s):
        if ch in last and last[ch] >= left:      # <-- THE TOKEN
            left = last[ch] + 1
        last[ch] = right
        best = max(best, right - left + 1)
    return best
# BREAKS IF: you drop `and last[ch] >= left`. Then a repeat from BEFORE the
# window drags `left` backwards and the window grows wrong.
#   "abba" -> without the guard you get 3, correct answer is 2.
# The dict keeps stale indices on purpose; the >= left test is what ignores them.


# 2 -- GROUP ANAGRAMS ---------------------------------------------------------
# Skeleton: build a canonical key per word. Bucket by key. Return the buckets.
# O(n * k log k) with the sorted key, k = word length.
def group_anagrams(words):
    buckets = defaultdict(list)
    for w in words:
        buckets[tuple(sorted(w))].append(w)      # <-- THE TOKEN
    return list(buckets.values())
# BREAKS IF: you use sorted(w) as the key directly -- a list is unhashable,
# TypeError. tuple() or "".join() both fix it.
# O(n*k) alternative when the alphabet is fixed: key on a 26-length count tuple.


# 3 -- VALID PALINDROME (alphanumeric only, case-insensitive) -----------------
# Skeleton: pointer at each end. Skip non-alphanumeric. Compare, then step in.
# O(n) time, O(1) space -- the whole point vs the one-liner.
def is_palindrome(s):
    i, j = 0, len(s) - 1
    while i < j:
        while i < j and not s[i].isalnum():      # <-- THE TOKEN: i < j in BOTH
            i += 1
        while i < j and not s[j].isalnum():
            j -= 1
        if s[i].lower() != s[j].lower():
            return False
        i, j = i + 1, j - 1
    return True
# BREAKS IF: you drop `i < j` from the inner whiles -- a string of only
# punctuation walks the pointer off the end. ",,," -> IndexError.
# The one-liner `t = [c.lower() for c in s if c.isalnum()]; return t == t[::-1]`
# is correct and fine to write, but it is O(n) SPACE. Say which you chose.


# 4 -- RUN-LENGTH ENCODE ------------------------------------------------------
# Skeleton: track the current char and its count. On change, flush. Flush at end.
def rle(s):
    if not s:
        return ""
    out = []
    cur, count = s[0], 0
    for ch in s:
        if ch == cur:
            count += 1
        else:
            out.append(cur + str(count))
            cur, count = ch, 1
    out.append(cur + str(count))                 # <-- THE TOKEN: final flush
    return "".join(out)
# BREAKS IF: you forget the flush after the loop -- the LAST run is silently
# dropped. "aab" -> "a2" instead of "a2b1". This off-by-one-run is the single
# most common bug in this shape, and it is invisible on inputs ending in a
# change. Always test an input whose last run is length 1.
# Build with a list + join, never `out += ...` on a str (that is O(n^2)).


# 5 -- TWO SUM (one pass) -----------------------------------------------------
# Skeleton: for each number, ask whether its complement was already seen.
# O(n) time, O(n) space.
def two_sum(nums, target):
    seen = {}                       # value -> index
    for i, n in enumerate(nums):
        if target - n in seen:                   # <-- THE TOKEN: check BEFORE insert
            return (seen[target - n], i)
        seen[n] = i
    return None
# BREAKS IF: you insert before checking. Then a single 4 with target 8 matches
# ITSELF and you return (0, 0). Check-then-insert is the whole trick.


# 6 -- MAXIMUM SUBARRAY (Kadane) ----------------------------------------------
# Skeleton: at each element, either extend the running sum or restart from here.
#           Keep the best seen.
# O(n) time, O(1) space.
def max_subarray(nums):
    if not nums:
        return 0                    # CONTRACT: or raise -- say which you chose
    best = cur = nums[0]                         # <-- THE TOKEN: seed from nums[0]
    for n in nums[1:]:
        cur = max(n, cur + n)
        best = max(best, cur)
    return best
# BREAKS IF: you seed best = 0. On an all-negative array that returns 0, which
# is not a subarray sum at all. [-3,-1,-2] -> should be -1, you get 0.
# Seeding from nums[0] is what makes all-negative work.


# 7 -- SUBARRAY SUM EQUALS K (prefix sums) ------------------------------------
# Skeleton: running total. How many earlier prefixes make (total - earlier) == k?
#           Count them, then record this prefix.
# O(n) time, O(n) space. The pattern that beats the O(n^2) double loop.
def subarray_sum_count(nums, k):
    counts = Counter({0: 1})                     # <-- THE TOKEN: seed {0: 1}
    total = found = 0
    for n in nums:
        total += n
        found += counts[total - k]
        counts[total] += 1
    return found
# BREAKS IF: you omit the {0: 1} seed. That seed represents the empty prefix,
# which is what lets a subarray STARTING AT INDEX 0 be counted.
#   [3], k=3 -> 0 instead of 1.
# Works with negative numbers, which is why this beats a sliding window here.


# 8 -- IN-PLACE DEDUPE OF A SORTED ARRAY --------------------------------------
# Skeleton: slow pointer marks the write position. Fast pointer scans. Write
#           only on a new value. Return the new length.
# O(n) time, O(1) space.
def dedupe_sorted(nums):
    if not nums:
        return 0
    write = 1
    for read in range(1, len(nums)):
        if nums[read] != nums[write - 1]:        # <-- THE TOKEN: compare to LAST WRITTEN
            nums[write] = nums[read]
            write += 1
    return write
# BREAKS IF: you compare nums[read] != nums[read-1] instead. That works here by
# luck on sorted input but is the wrong invariant -- it compares against the
# input, not against what you have kept. Comparing to the last WRITTEN element
# is the version that generalises (e.g. keep at most two of each).
# NOTE this MUTATES the caller's list by design; if the contract forbids that,
# it is the wrong function.


# -- two more worth knowing by name, not by heart -----------------------------
# Sorted-position lookups: bisect.bisect_left / bisect_right. Reach for these
# instead of hand-writing binary search -- hand-written bounds are the classic
# off-by-one and you gain nothing.
def first_index_ge(sorted_nums, target):
    i = bisect.bisect_left(sorted_nums, target)
    return i if i < len(sorted_nums) else -1

# Merging k sorted iterables lazily: heapq.merge(*iterables) -- O(1) memory,
# streams. Do not concatenate then sort if the inputs are already sorted.


# -- self-test ----------------------------------------------------------------
if __name__ == "__main__":
    fails = []

    def ck(label, got, want):
        if got != want:
            fails.append((label, got, want))
        print("  %s %-42s %r" % ("PASS" if got == want else "FAIL", label, got))

    print("1 longest_unique_substring")
    ck("abcabcbb", longest_unique_substring("abcabcbb"), 3)
    ck("bbbbb", longest_unique_substring("bbbbb"), 1)
    ck("pwwkew", longest_unique_substring("pwwkew"), 3)
    ck("abba  <- the >= left guard", longest_unique_substring("abba"), 2)
    ck("empty", longest_unique_substring(""), 0)

    print("2 group_anagrams")
    got = sorted(sorted(g) for g in group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))
    ck("classic", got, [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]])
    ck("empty", group_anagrams([]), [])

    print("3 is_palindrome")
    ck("A man, a plan, a canal: Panama", is_palindrome("A man, a plan, a canal: Panama"), True)
    ck("race a car", is_palindrome("race a car"), False)
    ck("empty", is_palindrome(""), True)
    ck(",,,  <- punctuation only", is_palindrome(",,,"), True)
    ck("single char", is_palindrome("a"), True)

    print("4 rle")
    ck("aab  <- final flush", rle("aab"), "a2b1")
    ck("aaabbc", rle("aaabbc"), "a3b2c1")
    ck("empty", rle(""), "")
    ck("single", rle("x"), "x1")

    print("5 two_sum")
    ck("classic", two_sum([2, 7, 11, 15], 9), (0, 1))
    ck("no self-match on [4], t=8", two_sum([4], 8), None)
    ck("duplicate values", two_sum([3, 3], 6), (0, 1))
    ck("no solution", two_sum([1, 2], 99), None)

    print("6 max_subarray")
    ck("mixed", max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]), 6)
    ck("all negative  <- seed matters", max_subarray([-3, -1, -2]), -1)
    ck("single", max_subarray([5]), 5)
    ck("all positive", max_subarray([1, 2, 3]), 6)

    print("7 subarray_sum_count")
    ck("[1,1,1] k=2", subarray_sum_count([1, 1, 1], 2), 2)
    ck("[3] k=3  <- the {0:1} seed", subarray_sum_count([3], 3), 1)
    ck("negatives", subarray_sum_count([1, -1, 0], 0), 3)
    ck("none", subarray_sum_count([1, 2, 3], 99), 0)

    print("8 dedupe_sorted")
    a = [1, 1, 2, 2, 2, 3]
    n = dedupe_sorted(a)
    ck("new length", n, 3)
    ck("prefix contents", a[:n], [1, 2, 3])
    ck("empty", dedupe_sorted([]), 0)
    b = [7]
    ck("single", dedupe_sorted(b), 1)

    print("bonus bisect")
    ck("first >= 4", first_index_ge([1, 3, 5, 7], 4), 2)
    ck("past the end", first_index_ge([1, 3], 9), -1)

    print("\nFAILURES: %d" % len(fails))
    for f in fails:
        print("   ", f)
