#!/usr/bin/env python3
"""
Anthropic Technical Advisor — CodeSignal ICA
The task-management system: all four levels, to the brief's structure.

WHY THIS FILE EXISTS
--------------------
Per the Coachable brief this is the MOST RECENT sighting of the seven-system bank,
and the system behind the most recent reported pass at about 500. It is third by
overall frequency, after the key-value database and the bank.

It is also the system with the most format traps, which is why it is worth typing
rather than reading:
  L1  ids are task_id_1, task_id_2 IN CREATION ORDER, and get returns a
      JSON string with NO SPACES and the keys in a FIXED ORDER
  L2  substring search, priority DESC with ties by creation order, and a
      limit of zero or less returns an EMPTY LIST (not everything)
  L3  users with a quota; an assignment is active while start <= now < finish,
      and ONLY ACTIVE assignments count against the quota
  L4  find the assignments that expired without being completed

THE SHAPE: one class owns the state, `now` is the first argument of every
operation from Level 1 onward, and "active" is COMPUTED from the current time
rather than stored — which is what makes the Level 3 quota correct for free.

Run it:  python3 anthropic-ica-task-manager.py
Every check must print PASS. Exit code 0 means the reference is intact.
"""

import json
from bisect import bisect_right  # noqa: F401  (kept: the L4 variants use it)


class TaskManager:
    def __init__(self):
        # task_id -> {"task_id","name","priority","created_seq"}
        self.tasks = {}
        self._task_counter = 0
        # user_id -> quota
        self.users = {}
        # list of {"task_id","user_id","start","finish","completed_at"}
        self.assignments = []

    # --- internals -------------------------------------------------------

    @staticmethod
    def _is_active(assignment, now):
        """Active while start <= now < finish — the half-open interval is tested."""
        return assignment["start"] <= now < assignment["finish"]

    def _active_for_user(self, user_id, now):
        return [
            a for a in self.assignments
            if a["user_id"] == user_id
            and a["completed_at"] is None
            and self._is_active(a, now)
        ]

    # --- Level 1: initial design & basic functions -----------------------

    def add_task(self, now, name, priority):
        self._task_counter += 1
        task_id = f"task_id_{self._task_counter}"      # ordinal, in creation order
        self.tasks[task_id] = {
            "task_id": task_id,
            "name": name,
            "priority": priority,
            "created_seq": self._task_counter,
        }
        return task_id

    def get_task(self, now, task_id):
        """A JSON string with NO spaces and the keys in a fixed order."""
        t = self.tasks.get(task_id)
        if t is None:
            return ""
        ordered = {"task_id": t["task_id"], "name": t["name"], "priority": t["priority"]}
        # separators=(",",":") is the whole trick — json.dumps defaults to ", " and ": "
        return json.dumps(ordered, separators=(",", ":"))

    def update_task(self, now, task_id, name=None, priority=None):
        t = self.tasks.get(task_id)
        if t is None:
            return "false"
        if name is not None:
            t["name"] = name
        if priority is not None:
            t["priority"] = priority
        return "true"

    def delete_task(self, now, task_id):
        if task_id not in self.tasks:
            return "false"
        del self.tasks[task_id]
        self.assignments = [a for a in self.assignments if a["task_id"] != task_id]
        return "true"

    # --- Level 2: data structures & data processing ----------------------

    def _ranked(self, tasks):
        # priority DESCENDING, ties by CREATION ORDER ascending
        return sorted(tasks, key=lambda t: (-t["priority"], t["created_seq"]))

    def search_tasks(self, now, fragment):
        """Substring of the name — not a prefix."""
        hits = [t for t in self.tasks.values() if fragment in t["name"]]
        return [t["task_id"] for t in self._ranked(hits)]

    def list_tasks(self, now, limit):
        if limit <= 0:
            return []                       # zero or less returns EMPTY, not everything
        return [t["task_id"] for t in self._ranked(self.tasks.values())][:limit]

    # --- Level 3: refactoring & encapsulation (users, quota, time) -------

    def add_user(self, now, user_id, quota):
        if user_id in self.users:
            return "false"
        self.users[user_id] = quota
        return "true"

    def assign_task(self, now, task_id, user_id, finish):
        if task_id not in self.tasks or user_id not in self.users:
            return "false"
        if finish <= now:
            return "false"                  # an assignment that is already over
        # quota counts only what is ACTIVE RIGHT NOW — computed, never stored
        if len(self._active_for_user(user_id, now)) >= self.users[user_id]:
            return "false"
        self.assignments.append({
            "task_id": task_id,
            "user_id": user_id,
            "start": now,
            "finish": finish,
            "completed_at": None,
        })
        return "true"

    def list_user_tasks(self, now, user_id):
        """A user's active tasks, sorted by finish time."""
        if user_id not in self.users:
            return []
        active = self._active_for_user(user_id, now)
        return [a["task_id"] for a in sorted(active, key=lambda a: (a["finish"], a["task_id"]))]

    # --- Level 4: extending design & functionality -----------------------

    def complete_task(self, now, task_id, user_id):
        for a in self.assignments:
            if (a["task_id"] == task_id and a["user_id"] == user_id
                    and a["completed_at"] is None and self._is_active(a, now)):
                a["completed_at"] = now
                return "true"
        return "false"

    def expired_unfinished(self, now):
        """Assignments whose window closed with no completion."""
        expired = [
            a for a in self.assignments
            if a["completed_at"] is None and a["finish"] <= now
        ]
        expired.sort(key=lambda a: (a["finish"], a["task_id"]))
        return [f"{a['task_id']}({a['user_id']})" for a in expired]


# ---------------------------------------------------------------------------
# Self-test. Every check must print PASS.
# ---------------------------------------------------------------------------

_checks = 0
_failures = 0


def check(label, actual, expected):
    global _checks, _failures
    _checks += 1
    if actual == expected:
        print(f"PASS  {label}")
    else:
        _failures += 1
        print(f"FAIL  {label}\n        expected {expected!r}\n        actual   {actual!r}")


def level1():
    print("\n--- Level 1 · initial design & basic functions ---")
    tm = TaskManager()
    check("ids are ordinal in creation order", tm.add_task(1, "alpha", 5), "task_id_1")
    check("the second id follows", tm.add_task(1, "beta", 3), "task_id_2")

    # THE FORMAT TRAP: json.dumps defaults to ", " and ": " separators
    check("get returns JSON with NO SPACES, keys in a fixed order",
          tm.get_task(2, "task_id_1"),
          '{"task_id":"task_id_1","name":"alpha","priority":5}')
    check("no space after the colon", ": " in tm.get_task(2, "task_id_1"), False)
    check("no space after the comma", ", " in tm.get_task(2, "task_id_1"), False)
    check("get on a missing task is empty", tm.get_task(2, "task_id_99"), "")

    check("update returns 'true'", tm.update_task(3, "task_id_2", priority=9), "true")
    check("the update took", tm.get_task(3, "task_id_2"),
          '{"task_id":"task_id_2","name":"beta","priority":9}')
    check("update of a missing task is 'false'", tm.update_task(3, "nope", priority=1), "false")
    check("delete returns 'true'", tm.delete_task(4, "task_id_2"), "true")
    check("the task is gone", tm.get_task(4, "task_id_2"), "")
    check("deleting twice is 'false'", tm.delete_task(4, "task_id_2"), "false")
    check("ids do NOT get reused after a delete", tm.add_task(5, "gamma", 1), "task_id_3")


def level2():
    print("\n--- Level 2 · search, ranking, limits ---")
    tm = TaskManager()
    tm.add_task(1, "write report", 5)       # task_id_1
    tm.add_task(1, "review report", 5)      # task_id_2  — ties with 1 on priority
    tm.add_task(1, "ship release", 9)       # task_id_3
    tm.add_task(1, "report bug", 1)         # task_id_4

    check("priority DESC, ties by CREATION ORDER",
          tm.list_tasks(2, 10), ["task_id_3", "task_id_1", "task_id_2", "task_id_4"])
    check("the limit slices the ranking", tm.list_tasks(2, 2), ["task_id_3", "task_id_1"])

    # THE TRAP: zero or less means EMPTY, not "everything"
    check("a limit of zero returns an EMPTY list", tm.list_tasks(2, 0), [])
    check("a negative limit returns an EMPTY list", tm.list_tasks(2, -5), [])

    # substring, not prefix
    check("search matches a SUBSTRING anywhere in the name",
          tm.search_tasks(2, "report"), ["task_id_1", "task_id_2", "task_id_4"])
    check("a mid-word substring still matches", tm.search_tasks(2, "elea"), ["task_id_3"])
    check("search is ranked the same way as the listing",
          tm.search_tasks(2, "re"), ["task_id_3", "task_id_1", "task_id_2", "task_id_4"])
    check("no match returns an empty list", tm.search_tasks(2, "zzz"), [])


def level3():
    print("\n--- Level 3 · users, quota, and the active window ---")
    tm = TaskManager()
    for i, (name, pri) in enumerate([("a", 1), ("b", 2), ("c", 3), ("d", 4)], 1):
        tm.add_task(1, name, pri)
    check("add_user is 'true'", tm.add_user(1, "u1", 2), "true")
    check("a duplicate user is 'false'", tm.add_user(1, "u1", 5), "false")

    check("assign within quota", tm.assign_task(10, "task_id_1", "u1", 100), "true")
    check("assign a second within quota", tm.assign_task(10, "task_id_2", "u1", 200), "true")
    check("THE THIRD EXCEEDS THE QUOTA", tm.assign_task(10, "task_id_3", "u1", 300), "false")
    check("assigning an unknown task is 'false'", tm.assign_task(10, "nope", "u1", 300), "false")
    check("assigning to an unknown user is 'false'", tm.assign_task(10, "task_id_3", "u9", 300), "false")
    check("a finish at or before now is 'false'", tm.assign_task(10, "task_id_3", "u1", 10), "false")

    check("active tasks are sorted by finish time",
          tm.list_user_tasks(50, "u1"), ["task_id_1", "task_id_2"])

    # THE BOUNDARY: active while start <= now < finish
    check("active at exactly the start", tm.list_user_tasks(10, "u1"),
          ["task_id_1", "task_id_2"])
    check("task_id_1 is gone at EXACTLY its finish",
          tm.list_user_tasks(100, "u1"), ["task_id_2"])
    check("both gone once the later one finishes", tm.list_user_tasks(200, "u1"), [])

    # THE POINT OF THE LEVEL: quota is computed from what is ACTIVE NOW, so the
    # slot frees itself once an assignment's window closes — nothing is decremented.
    # At now=100 task_id_1 has just expired (freeing one slot) and task_id_2 is still
    # active, so exactly ONE slot is open — and it re-fills immediately.
    check("A FREED SLOT IS REUSABLE WITHOUT ANY BOOKKEEPING",
          tm.assign_task(100, "task_id_3", "u1", 400), "true")
    check("that single freed slot is now full again",
          tm.assign_task(100, "task_id_4", "u1", 400), "false")
    check("and the quota stays enforced on a retry",
          tm.assign_task(100, "task_id_1", "u1", 400), "false")
    # prove the slot really was the expired one, not an off-by-one in the counter
    check("the active set is exactly the two live assignments",
          sorted(a["task_id"] for a in tm._active_for_user("u1", 100)),
          ["task_id_2", "task_id_3"])
    check("an unknown user lists nothing", tm.list_user_tasks(100, "nobody"), [])


def level4():
    print("\n--- Level 4 · completion, and what expired unfinished ---")
    tm = TaskManager()
    for name in ("a", "b", "c"):
        tm.add_task(1, name, 1)
    tm.add_user(1, "u1", 5)
    tm.add_user(1, "u2", 5)
    tm.assign_task(10, "task_id_1", "u1", 100)
    tm.assign_task(10, "task_id_2", "u1", 200)
    tm.assign_task(10, "task_id_3", "u2", 150)

    check("completing an active assignment is 'true'",
          tm.complete_task(50, "task_id_2", "u1"), "true")
    check("completing it twice is 'false'", tm.complete_task(60, "task_id_2", "u1"), "false")
    check("completing for the wrong user is 'false'",
          tm.complete_task(60, "task_id_1", "u2"), "false")
    check("a completed task leaves the active list",
          tm.list_user_tasks(60, "u1"), ["task_id_1"])
    check("completing frees the quota slot too",
          len(tm._active_for_user("u1", 60)), 1)

    check("nothing has expired yet", tm.expired_unfinished(50), [])
    check("at EXACTLY the finish it counts as expired",
          tm.expired_unfinished(100), ["task_id_1(u1)"])
    check("the completed one never appears",
          tm.expired_unfinished(500), ["task_id_1(u1)", "task_id_3(u2)"])
    check("expired results are ordered by finish time",
          tm.expired_unfinished(500)[0], "task_id_1(u1)")

    check("completing an already-expired assignment is 'false'",
          tm.complete_task(500, "task_id_1", "u1"), "false")


def shape_guarantees():
    print("\n--- Structural guarantees ---")
    import inspect

    ops = ["add_task", "get_task", "update_task", "delete_task", "search_tasks",
           "list_tasks", "add_user", "assign_task", "list_user_tasks",
           "complete_task", "expired_unfinished"]
    missing = [
        op for op in ops
        if list(inspect.signature(getattr(TaskManager, op)).parameters)[1] != "now"
    ]
    check("every operation takes `now` as its first real argument", missing, [])

    src = inspect.getsource(TaskManager)
    check("the active-window test is defined once", src.count("def _is_active"), 1)
    check("the ranking key is defined once", src.count("def _ranked"), 1)
    # quota is COMPUTED, never stored as a running counter
    check("no stored 'used quota' counter exists", "used_quota" in src, False)
    check("get_task pins the no-space separators",
          'separators=(",", ":")' in src, True)


def main():
    level1()
    level2()
    level3()
    level4()
    shape_guarantees()
    print(f"\n{_checks} checks, {_failures} failed.")
    if _failures:
        raise SystemExit(1)
    print("Reference implementation intact.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
