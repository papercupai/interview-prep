"""
6. Worker hours: simplest timed-test answer

- Each worker keeps a list of COMPLETED shifts as (start, end, rate). The open shift is just clock_in (None when clocked out), so "only completed shifts count" is automatic.
- Stamp the rate onto the shift at clock-OUT, and apply a queued promotion at clock-IN. The promotion can never land mid-shift.
- Pay: cut each shift down to the part inside [start, end) (lo, hi), pay those minutes once, then pay again for every minute of that part that falls in a double-pay period. That's why double pay needs no special case when a shift crosses a boundary.
- Half-open intervals everywhere ([start, end)), so [1,5) and [5,7) touch without overlapping. overlap() returns 0 for an empty or backwards interval, so no extra if is needed.
"""


class Worker:
    def __init__(self, position, rate):
        self.position, self.rate = position, rate
        self.promotion = None  # (position, rate), applied at the next clock-in
        self.clock_in = None   # start of the open shift, or None
        self.shifts = []       # completed shifts: (start, end, rate)


def overlap(a, b, c, d):  # length of [a, b) intersected with [c, d)
    return max(0, min(b, d) - max(a, c))


class WorkerHours:
    def __init__(self):
        self.workers = {}  # id -> Worker
        self.doubles = []  # double-pay periods: (start, end)

    # Level 1
    def add_worker(self, wid, position, rate):
        if wid in self.workers:
            return False
        self.workers[wid] = Worker(position, rate)
        return True

    def register(self, wid, now):
        w = self.workers.get(wid)
        if w is None:
            return False
        if w.clock_in is None:  # clock in
            if w.promotion:
                w.position, w.rate = w.promotion
                w.promotion = None
            w.clock_in = now
        else:                   # clock out
            w.shifts.append((w.clock_in, now, w.rate))
            w.clock_in = None
        return True

    # Level 2
    def total_time(self, wid):
        w = self.workers.get(wid)
        if w is None:
            return None
        total = 0
        for start, end, rate in w.shifts:
            total += end - start
        return total

    def top_k(self, k):
        if k <= 0:
            return []
        ranked = sorted(self.workers, key=lambda wid: (-self.total_time(wid), wid))
        return ranked[:k]

    # Level 3
    def promote(self, wid, new_position, new_rate):
        if wid not in self.workers:
            return False
        self.workers[wid].promotion = (new_position, new_rate)
        return True

    def pay(self, wid, start, end):
        w = self.workers.get(wid)
        if w is None:
            return None
        total = 0
        for s, e, rate in w.shifts:
            lo, hi = max(s, start), min(e, end)  # the part of this shift inside [start, end)
            total += max(0, hi - lo) * rate      # 0 when the shift is outside the window
            for ds, de in self.doubles:  # Level 4: double-pay minutes are paid once more
                total += overlap(lo, hi, ds, de) * rate
        return total

    # Level 4
    def add_double_period(self, start, end):
        if start >= end:
            return False
        for ds, de in self.doubles:
            if overlap(start, end, ds, de) > 0:
                return False
        self.doubles.append((start, end))
        return True


# ---- tests: python3 worker_hours.py ----
if __name__ == "__main__":
    wh = WorkerHours()
    # Level 1
    assert wh.add_worker("ann", "dev", 10) is True and wh.add_worker("ann", "x", 1) is False
    assert wh.register("zz", 1) is False
    # Level 3: the page's "check yourself" (rate 10, in at 2, out at 7)
    assert wh.register("ann", 2) is True
    assert wh.total_time("ann") == 0                    # open shift doesn't count yet
    assert wh.register("ann", 7) is True
    assert wh.total_time("ann") == 5 and wh.total_time("zz") is None
    assert wh.pay("ann", 4, 9) == 30 and wh.pay("zz", 0, 9) is None
    assert wh.pay("ann", 7, 9) == 0 and wh.pay("ann", 0, 100) == 50
    assert wh.pay("ann", 8, 9) == 0                     # window entirely after the shift
    # Level 2
    wh.add_worker("bob", "dev", 1); wh.add_worker("cal", "dev", 1)
    wh.register("bob", 10); wh.register("bob", 15)      # 5, ties with ann
    wh.register("cal", 10); wh.register("cal", 30)      # 20
    assert wh.top_k(3) == ["cal", "ann", "bob"] and wh.top_k(1) == ["cal"] and wh.top_k(0) == []
    # Level 3: a promotion waits for the next clock-in
    wh.register("bob", 40)                              # bob clocks in at rate 1
    assert wh.promote("bob", "lead", 5) is True and wh.promote("zz", "x", 1) is False
    wh.register("bob", 50)                              # this shift is still paid at rate 1
    wh.register("bob", 60); wh.register("bob", 62)      # new rate from here
    assert wh.pay("bob", 40, 70) == 10 * 1 + 2 * 5
    # Level 4: double pay, including a shift that crosses a boundary
    assert wh.add_double_period(5, 7) is True
    assert wh.pay("ann", 4, 9) == 50                    # the page's check: 30 + 2 * 10
    assert wh.add_double_period(6, 8) is False          # overlaps [5, 7)
    assert wh.add_double_period(7, 7) is False          # empty
    assert wh.add_double_period(7, 8) is True           # touching is not overlapping
    assert wh.pay("ann", 0, 100) == 50 + 20             # [5, 7) doubled; ann left at 7
    assert wh.pay("cal", 0, 100) == 20                  # cal worked 10-30: no double periods
    print("worker_hours: all checks passed")
