"""
3. Task manager: simplest timed-test answer

- json.dumps(..., separators=(",", ":")) is the whole "no spaces" trap. {"task_id": tid, **task} builds the dict in the order you need, because dicts keep insertion order.
- Dicts keep insertion order and sort() is stable, so sorting tasks by -priority alone leaves ties in creation order. No sequence counter is needed.
- Assignments are a plain list of dicts. "Active" is computed from now (not done and now < finish), never stored, so the quota frees itself when an assignment expires.
- Calls arrive in time order, so every assignment's start is <= now and it never has to be checked or even stored.
- No defaultdict here: assignments are one flat list because delete_task and expired_unfinished both scan every user's assignments anyway.
"""

import json


class TaskManager:
    def __init__(self):
        self.tasks = {}   # task_id -> {"name", "priority"}   (dict order = creation order)
        self.count = 0
        self.quota = {}   # user_id -> quota
        self.jobs = []    # [{"task", "user", "finish", "done"}]

    # Level 1
    def add_task(self, now, name, priority):
        self.count += 1
        tid = f"task_id_{self.count}"
        self.tasks[tid] = {"name": name, "priority": priority}
        return tid

    def get_task(self, now, tid):
        if tid not in self.tasks:
            return ""
        return json.dumps({"task_id": tid, **self.tasks[tid]}, separators=(",", ":"))

    def update_task(self, now, tid, name=None, priority=None):
        if tid not in self.tasks:
            return "false"
        if name is not None:
            self.tasks[tid]["name"] = name
        if priority is not None:
            self.tasks[tid]["priority"] = priority
        return "true"

    def delete_task(self, now, tid):
        if tid not in self.tasks:
            return "false"
        del self.tasks[tid]
        kept = []
        for j in self.jobs:
            if j["task"] != tid:
                kept.append(j)
        self.jobs = kept
        return "true"

    # Level 2
    def _ranked(self, ids):
        ids = list(ids)
        ids.sort(key=lambda t: -self.tasks[t]["priority"])  # stable: ties stay in creation order
        return ids

    def search_tasks(self, now, text):
        hits = []
        for tid in self.tasks:
            if text in self.tasks[tid]["name"]:
                hits.append(tid)
        return self._ranked(hits)

    def list_tasks(self, now, limit):
        if limit <= 0:
            return []
        return self._ranked(self.tasks)[:limit]

    # Level 3
    def add_user(self, now, uid, quota):
        if uid in self.quota:
            return "false"
        self.quota[uid] = quota
        return "true"

    def _active(self, now, uid):
        active = []
        for j in self.jobs:
            if j["user"] == uid and not j["done"] and now < j["finish"]:
                active.append(j)
        return active

    def assign_task(self, now, tid, uid, finish):
        if tid not in self.tasks or uid not in self.quota or finish <= now:
            return "false"
        if len(self._active(now, uid)) >= self.quota[uid]:
            return "false"
        self.jobs.append({"task": tid, "user": uid, "finish": finish, "done": False})
        return "true"

    def list_user_tasks(self, now, uid):
        jobs = self._active(now, uid)
        jobs.sort(key=lambda j: (j["finish"], j["task"]))
        result = []
        for j in jobs:
            result.append(j["task"])
        return result

    # Level 4
    def complete_task(self, now, tid, uid):
        for j in self._active(now, uid):
            if j["task"] == tid:
                j["done"] = True
                return "true"
        return "false"

    def expired_unfinished(self, now):
        late = []
        for j in self.jobs:
            if not j["done"] and j["finish"] <= now:
                late.append(j)
        late.sort(key=lambda j: (j["finish"], j["task"]))
        result = []
        for j in late:
            result.append(f"{j['task']}({j['user']})")
        return result


# ---- tests: python3 task_manager.py ----
if __name__ == "__main__":
    tm = TaskManager()
    # Level 1: the page's "check yourself"
    assert tm.add_task(1, "read", 3) == "task_id_1"
    assert tm.get_task(2, "task_id_1") == '{"task_id":"task_id_1","name":"read","priority":3}'
    assert tm.get_task(2, "task_id_9") == ""
    assert tm.add_task(3, "write", 5) == "task_id_2"
    assert tm.update_task(4, "task_id_2", priority=1) == "true" and tm.update_task(4, "nope", name="x") == "false"
    assert tm.get_task(4, "task_id_2") == '{"task_id":"task_id_2","name":"write","priority":1}'
    assert tm.delete_task(5, "task_id_2") == "true" and tm.delete_task(5, "task_id_2") == "false"
    assert tm.add_task(6, "reread", 3) == "task_id_3"            # ids are never reused
    # Level 2
    tm.add_task(7, "spread", 9)                                   # task_id_4
    assert tm.search_tasks(8, "read") == ["task_id_4", "task_id_1", "task_id_3"]   # ties: creation order
    assert tm.list_tasks(8, 2) == ["task_id_4", "task_id_1"]
    assert tm.list_tasks(8, 0) == [] and tm.list_tasks(8, -1) == []
    assert tm.search_tasks(8, "zzz") == []
    # Level 3: quota-one assignment ending at 15 blocks another at 14, frees at 15
    assert tm.add_user(10, "u", 1) == "true" and tm.add_user(10, "u", 5) == "false"
    assert tm.assign_task(10, "task_id_1", "u", 15) == "true"
    assert tm.assign_task(14, "task_id_3", "u", 30) == "false"
    assert tm.list_user_tasks(14, "u") == ["task_id_1"]
    assert tm.assign_task(15, "task_id_3", "u", 30) == "true"
    assert tm.list_user_tasks(15, "u") == ["task_id_3"]
    assert tm.assign_task(15, "task_id_9", "u", 30) == "false" and tm.assign_task(15, "task_id_1", "x", 30) == "false"
    assert tm.list_user_tasks(15, "nobody") == []
    # Level 4
    assert tm.complete_task(16, "task_id_1", "u") == "false"     # already expired
    assert tm.complete_task(16, "task_id_3", "u") == "true"
    assert tm.complete_task(16, "task_id_3", "u") == "false"     # already complete
    assert tm.add_user(17, "v", 2) == "true"
    assert tm.assign_task(17, "task_id_4", "v", 20) == "true"    # completing frees quota too
    assert tm.expired_unfinished(19) == ["task_id_1(u)"]
    assert tm.expired_unfinished(20) == ["task_id_1(u)", "task_id_4(v)"]
    print("task_manager: all checks passed")
