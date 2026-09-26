"""Reference answers to ORIGINAL Anthropic ICA practice, not assessment questions.

Attempt anthropic-codesignal-practice.py before reading this file.
Verify: python3 -m unittest discover -s tests -p 'test_anthropic_codesignal.py' -v
"""
from collections import Counter


def ranked_counts(events, k):
    """IDs ordered by frequency descending, then ID ascending; k <= 0 => []."""
    counts = Counter(events)
    return sorted(counts, key=lambda key: (-counts[key], key))[:max(0, k)]


def merge_windows(windows):
    """Merge overlapping half-open intervals; touching endpoints stay separate.

    Inputs have start < end. Do not mutate input. Return list of tuples.
    """
    result = []
    for start, end in sorted(windows):
        if result and start < result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result


def accepted_requests(events, gap):
    """Events are (user, timestamp), in nondecreasing timestamp order; gap >= 0.

    Accept first request per user, then only if >= gap since that user's last
    ACCEPTED request. Return accepted events, in original order. No mutation.
    """
    last = {}
    accepted = []
    for user, timestamp in events:
        if user not in last or timestamp - last[user] >= gap:
            accepted.append((user, timestamp))
            last[user] = timestamp
    return accepted


class ReviewQueue:
    """Four-level original practice project. IDs/workers are nonempty strings.

    Priorities are nonnegative integers. Timed calls receive integer `now` in
    nondecreasing order globally. TTL and k are integers. No real clock needed.
    Expire leases at deadline <= now BEFORE any timed operation, even failures.
    L1/L2 methods are timeless; deleting a task also deletes its lease.
    """

    def __init__(self):
        self.tasks = {}
        self.leases = {}

    # Level 1: exact contracts and independent queue instances.
    def add(self, task_id, priority):
        if task_id in self.tasks:
            return False
        self.tasks[task_id] = priority
        return True

    def get(self, task_id):
        return self.tasks.get(task_id)

    def set_priority(self, task_id, priority):
        if task_id not in self.tasks:
            return False
        self.tasks[task_id] = priority
        return True

    def delete(self, task_id):
        if task_id not in self.tasks:
            return False
        del self.tasks[task_id]
        self.leases.pop(task_id, None)
        return True

    # Level 2: include leased tasks too, preserving this contract in later levels.
    def top(self, k):
        return self._rank(self.tasks, k)

    def _rank(self, ids, k):
        return sorted(ids, key=lambda key: (-self.tasks[key], key))[:max(0, k)]

    # Level 3: a lease is active for [now, now + ttl).
    def _expire(self, now):
        for task_id, (_, deadline) in list(self.leases.items()):
            if deadline <= now:
                del self.leases[task_id]

    def claim(self, task_id, worker, now, ttl):
        self._expire(now)
        if ttl <= 0 or task_id not in self.tasks or task_id in self.leases:
            return False
        self.leases[task_id] = (worker, now + ttl)
        return True

    def complete(self, task_id, worker, now):
        self._expire(now)
        lease = self.leases.get(task_id)
        if lease is None or lease[0] != worker:
            return False
        return self.delete(task_id)

    def ready(self, now, k):
        self._expire(now)
        return self._rank((key for key in self.tasks if key not in self.leases), k)

    # Level 4: validate the whole batch BEFORE taking any new lease.
    def bulk_claim(self, task_ids, worker, now, ttl):
        self._expire(now)
        if not task_ids or ttl <= 0 or len(set(task_ids)) != len(task_ids):
            return False
        if any(key not in self.tasks or key in self.leases for key in task_ids):
            return False
        for key in task_ids:
            self.leases[key] = (worker, now + ttl)
        return True
