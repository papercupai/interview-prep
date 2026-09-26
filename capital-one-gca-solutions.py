#!/usr/bin/env python3
"""Capital One / CodeSignal GCA — the four archetypes, solved and self-testing.

This file is the SOURCE OF TRUTH for capital-one-codesignal-assessment.html.
build-capital-one-page.py runs it first and REFUSES to generate the page if it
is red, so nothing reaches the page that has not passed its own tests.

  python3 capital-one-gca-solutions.py     # must exit 0
  python3 build-capital-one-page.py        # regenerates practice file + page
  ./build-standalone.sh                    # regenerates the -standalone twin

Sections are split on `# ==== name ====`. The region between `# >>> implement`
and `# <<< implement` is blanked in the generated practice file, so write the
solution INSIDE those markers and nowhere else.

Archetype mapping (CodeSignal GCA, 4 questions / 70 min, all visible at once):
  q1_warmup      string/array basics          ~ 8 min
  q2_ledger      reading-heavy conversion     ~15 min
  q3_matrix      matrix implementation        ~18 min
  q4_monotonic   optimization, monotonic      ~20 min
  q4_prefix      optimization, hashmap        ~15 min

The eight general patterns live in string-array-patterns.py; this file is the
Capital-One-shaped application of them, not a replacement.
"""
from collections import Counter, defaultdict


# ==== q1_warmup ====
def normalize_account_tags(tags):
    """Q1 ARCHETYPE — string/array basics, deliberately easy, ~5-8 min.

    Given raw tags, return the distinct tags in FIRST-SEEN order, lowercased
    and stripped. Ignore any tag that is empty after stripping.

    The GCA's Q1 is almost always this shape: trivial logic, but it rewards
    reading the spec exactly. "First-seen order" and "after stripping" are the
    two places people lose the points.
    """
    # >>> implement
    seen = set()
    out = []
    for raw in tags:
        t = raw.strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out
    # <<< implement


# ==== q2_ledger ====
def replay_ledger(events, opening_balance=0):
    """Q2 ARCHETYPE — reading-heavy conversion, ~15 min. Banking-flavoured,
    which is what Capital One tends to reach for.

    `events` is a list of "OP:ARG" strings applied in order to a balance:

      DEP:<int>    deposit, always applied
      WDR:<int>    withdraw, applied ONLY if it does not overdraw
      FEE:<int>    fee, applied even if it overdraws
      REV          reverse the most recent APPLIED event (no-op if none)

    Return (final_balance, applied_count).

    The trap: REV must reverse the last event that was actually APPLIED — a
    rejected WDR is not reversible, and a REV is itself not reversible. Keeping
    an explicit stack of applied deltas is what makes that correct; trying to
    track it with a single "last" variable fails on REV-after-REV.
    """
    # >>> implement
    balance = opening_balance
    applied = []                      # stack of deltas actually applied
    for event in events:
        if event == "REV":
            if applied:
                balance -= applied.pop()
            continue
        op, _, arg = event.partition(":")
        amount = int(arg)
        if op == "DEP":
            balance += amount
            applied.append(amount)
        elif op == "WDR":
            if amount <= balance:     # reject rather than overdraw
                balance -= amount
                applied.append(-amount)
        elif op == "FEE":
            balance -= amount         # applied even into overdraft
            applied.append(-amount)
    return balance, len(applied)
    # <<< implement


# ==== q3_matrix ====
def spiral_sums(grid):
    """Q3 ARCHETYPE — matrix implementation, ~18 min. No clever algorithm;
    it is pure boundary bookkeeping, and that is exactly why it is worth
    drilling: the bug is always an off-by-one on the last row or column.

    Walk `grid` in clockwise spiral order and return the running sums after
    each RING is completed (outermost ring first).

    The trap: after shrinking top/bottom/left/right you must re-check
    `top <= bottom` and `left <= right` BEFORE the reverse legs, or a single
    leftover row is emitted twice.
    """
    # >>> implement
    if not grid or not grid[0]:
        return []
    top, bottom = 0, len(grid) - 1
    left, right = 0, len(grid[0]) - 1
    running = 0
    out = []
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            running += grid[top][c]
        for r in range(top + 1, bottom + 1):
            running += grid[r][right]
        if top < bottom and left < right:          # the re-check that matters
            for c in range(right - 1, left - 1, -1):
                running += grid[bottom][c]
            for r in range(bottom - 1, top, -1):
                running += grid[r][left]
        out.append(running)
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return out
    # <<< implement


# ==== q4_monotonic ====
def days_until_higher_rate(rates):
    """Q4 ARCHETYPE — optimization via monotonic stack, ~20 min.

    For each day, how many days until a STRICTLY higher rate? 0 if none.

    The naive O(n^2) double loop is the thing to beat. The stack holds INDICES
    whose answer is still unknown, kept in decreasing rate order; a new higher
    rate resolves every index it beats.

    The trap: push the INDEX, not the value — you need the index to compute the
    distance. Storing values forces a second scan to find where they came from.
    """
    # >>> implement
    out = [0] * len(rates)
    stack = []                        # indices, rates[stack] non-increasing
    for i, rate in enumerate(rates):
        while stack and rates[stack[-1]] < rate:
            j = stack.pop()
            out[j] = i - j
        stack.append(i)
    return out
    # <<< implement


# ==== q4_prefix ====
def count_balanced_windows(deltas, target):
    """Q4 ARCHETYPE — optimization via prefix-sum hashmap, ~15 min.
    The same machinery as `subarray_sum_count`, which is the single highest-
    frequency non-obvious pattern in this whole assessment family.

    Count contiguous windows of `deltas` summing exactly to `target`.

    Two tokens carry it: the `{0: 1}` seed (the empty prefix, which is what
    lets a window starting at index 0 count) and looking up BEFORE inserting
    (which stops a window matching itself when target == 0).

    Negatives are why this beats a sliding window — a window's sum is not
    monotonic in its width, so there is no valid shrink rule.
    """
    # >>> implement
    counts = Counter({0: 1})
    running = 0
    found = 0
    for d in deltas:
        running += d
        found += counts[running - target]     # look up BEFORE inserting
        counts[running] += 1
    return found
    # <<< implement


# ==== selftest ====
if __name__ == "__main__":
    failures = []

    def ck(label, got, want):
        ok = got == want
        if not ok:
            failures.append((label, got, want))
        print("  %s %-46s %r" % ("PASS" if ok else "FAIL", label, got))

    print("q1_warmup — normalize_account_tags")
    ck("first-seen order preserved",
       normalize_account_tags(["Travel", "dining", "TRAVEL", "Gas"]),
       ["travel", "dining", "gas"])
    ck("strips then dedupes",
       normalize_account_tags(["  Fee ", "fee", "FEE"]), ["fee"])
    ck("drops empty-after-strip",
       normalize_account_tags(["", "   ", "cash"]), ["cash"])
    ck("empty input", normalize_account_tags([]), [])

    print("q2_ledger — replay_ledger")
    ck("deposits and fees", replay_ledger(["DEP:100", "FEE:30"]), (70, 2))
    ck("withdrawal rejected, not applied",
       replay_ledger(["DEP:50", "WDR:80"]), (50, 1))
    ck("fee may overdraw", replay_ledger(["DEP:10", "FEE:40"]), (-30, 2))
    ck("REV undoes last APPLIED",
       replay_ledger(["DEP:100", "WDR:200", "REV"]), (0, 0))
    ck("REV after REV walks the stack",
       replay_ledger(["DEP:100", "DEP:50", "REV", "REV"]), (0, 0))
    ck("REV with nothing applied is a no-op", replay_ledger(["REV"]), (0, 0))
    ck("opening balance honoured",
       replay_ledger(["WDR:40"], opening_balance=100), (60, 1))

    print("q3_matrix — spiral_sums")
    ck("3x3 two rings",
       spiral_sums([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), [40, 45])
    ck("single row emits once", spiral_sums([[1, 2, 3]]), [6])
    ck("single column emits once", spiral_sums([[1], [2], [3]]), [6])
    ck("2x2 one ring", spiral_sums([[1, 2], [3, 4]]), [10])
    ck("empty", spiral_sums([]), [])

    print("q4_monotonic — days_until_higher_rate")
    ck("classic", days_until_higher_rate([73, 74, 75, 71, 69, 72, 76, 73]),
       [1, 1, 4, 2, 1, 1, 0, 0])
    ck("monotonic decreasing -> all zero",
       days_until_higher_rate([5, 4, 3]), [0, 0, 0])
    ck("equal values are NOT strictly higher",
       days_until_higher_rate([3, 3, 4]), [2, 1, 0])
    ck("single", days_until_higher_rate([1]), [0])

    print("q4_prefix — count_balanced_windows")
    ck("[1,1,1] target 2", count_balanced_windows([1, 1, 1], 2), 2)
    ck("single element, the {0:1} seed",
       count_balanced_windows([3], 3), 1)
    ck("negatives, target 0",
       count_balanced_windows([1, -1, 0], 0), 3)
    ck("no window matches", count_balanced_windows([1, 2, 3], 99), 0)
    ck("all zeros counts every window",
       count_balanced_windows([0, 0], 0), 3)

    print("\nFAILURES: %d" % len(failures))
    for f in failures:
        print("   ", f)
    raise SystemExit(1 if failures else 0)
