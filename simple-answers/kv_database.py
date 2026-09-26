"""
1. In-memory key-value database: simplest timed-test answer

- Store every field as (value, expires_at), and use INF for "never expires". That removes every None branch, and backup/restore arithmetic still works because INF - now and now + INF are both INF.
- defaultdict(dict) and defaultdict(list) mean writes never need "create it if missing". An empty entry means "nothing there", so it's harmless when a read creates one.
- One read helper, _live(now, key), returns {field: value} for the fields still alive. Every read goes through it, so TTL is respected everywhere with no extra code.
- One write helper, _put. A delete is just "expires right now", so the look-back history records deletions for free.
- compare_*: _live(...).get(field) returns None for a missing field, and None never equals a string, so one comparison covers "missing" and "wrong value".
- backup counts keys for free: the snapshot is a defaultdict, and a key only appears once one of its fields is alive.
- Level 4: write ONLY the variant your test gives you (backup/restore OR get_when). Levels 1-3 never need self.hist; add it only for look-back.
"""

from collections import defaultdict

INF = float("inf")  # "never expires"


class InMemoryDB:
    def __init__(self):
        self.db = defaultdict(dict)    # key -> {field: (value, expires_at)}
        self.hist = defaultdict(list)  # (key, field) -> [(time, value, expires_at)]   Level 4 look-back only
        self.backups = []              # [(time, snapshot)]                           Level 4 backup only

    def _put(self, now, key, field, value, exp):  # the only write
        self.db[key][field] = (value, exp)
        self.hist[key, field].append((now, value, exp))

    def _live(self, now, key):  # the only read: {field: value} for fields still alive
        live = {}
        for field, (value, exp) in self.db[key].items():
            if now < exp:
                live[field] = value
        return live

    # Level 1
    def set(self, now, key, field, value):
        return self.set_with_ttl(now, key, field, value, INF)

    def get(self, now, key, field):
        return self._live(now, key).get(field, "")

    def delete(self, now, key, field):
        if field not in self._live(now, key):
            return "false"
        self._put(now, key, field, None, now)  # delete = "expires right now"
        return "true"

    def compare_and_set(self, now, key, field, expected, new_value):
        if self._live(now, key).get(field) != expected:
            return "false"
        self._put(now, key, field, new_value, self.db[key][field][1])  # keep the TTL
        return "true"

    def compare_and_delete(self, now, key, field, expected):
        if self._live(now, key).get(field) != expected:
            return "false"
        return self.delete(now, key, field)

    # Level 2
    def scan(self, now, key):
        return self.scan_by_prefix(now, key, "")

    def scan_by_prefix(self, now, key, prefix):
        live = self._live(now, key)
        parts = []
        for field in sorted(live):
            if field.startswith(prefix):
                parts.append(f"{field}({live[field]})")
        return ", ".join(parts)

    # Level 3
    def set_with_ttl(self, now, key, field, value, ttl):
        self._put(now, key, field, value, now + ttl)
        return ""

    # Level 4, variant A: backup / restore
    def backup(self, now):
        snap = defaultdict(dict)
        for key, fields in self.db.items():
            for field, (value, exp) in fields.items():
                if now < exp:
                    snap[key][field] = (value, exp - now)  # store the REMAINING ttl
        self.backups.append((now, snap))
        return str(len(snap))  # only keys with a live field were created

    def restore(self, now, at):
        snap = None
        for t, s in self.backups:  # keep the latest backup at or before `at`
            if t <= at:
                snap = s
        if snap is not None:
            self.db = defaultdict(dict)
            for key, fields in snap.items():
                for field, (value, remaining) in fields.items():
                    self.db[key][field] = (value, now + remaining)  # the ttl resumes from NOW
        return ""

    # Level 4, variant B: look back
    def get_when(self, now, key, field, at):
        if at == 0:
            return self.get(now, key, field)
        for t, value, exp in reversed(self.hist[key, field]):
            if t <= at:
                return value if at < exp else ""
        return ""


# ---- tests: python3 kv_database.py ----
if __name__ == "__main__":
    db = InMemoryDB()
    # Level 1
    assert db.set(1, "u", "name", "ann") == ""
    assert db.get(2, "u", "name") == "ann"
    assert db.get(2, "u", "missing") == "" and db.get(2, "nokey", "name") == ""
    assert db.delete(3, "u", "missing") == "false" and db.delete(3, "nokey", "x") == "false"
    assert db.compare_and_set(4, "u", "name", "bob", "cal") == "false"   # wrong value
    assert db.compare_and_set(4, "u", "nope", "ann", "cal") == "false"   # missing field
    assert db.compare_and_set(4, "u", "name", "ann", "cal") == "true"
    assert db.compare_and_delete(5, "u", "name", "ann") == "false"
    assert db.compare_and_delete(5, "u", "name", "cal") == "true"
    assert db.get(6, "u", "name") == "" and db.delete(6, "u", "name") == "false"
    # Level 2
    db.set(7, "s", "b", "2"); db.set(7, "s", "a", "1"); db.set(7, "s", "ab", "3")
    assert db.scan(8, "s") == "a(1), ab(3), b(2)"
    assert db.scan_by_prefix(8, "s", "a") == "a(1), ab(3)"
    assert db.scan_by_prefix(8, "s", "z") == "" and db.scan(8, "nokey") == ""
    # Level 3: the page's "check yourself"
    db.set_with_ttl(10, "r", "a", "red", 5)
    assert db.scan(14, "r") == "a(red)"
    assert db.get(15, "r", "a") == ""            # dead at EXACTLY now + ttl
    db.set(16, "r", "a", "blue")
    assert db.scan(16, "r") == "a(blue)"
    db.set_with_ttl(20, "c", "f", "v", 10)
    assert db.compare_and_set(25, "c", "f", "v", "w") == "true"   # keeps expiry 30
    assert db.get(29, "c", "f") == "w" and db.get(30, "c", "f") == ""
    assert db.compare_and_set(31, "c", "f", "w", "x") == "false"  # expired = missing
    # Level 4A: backup stores remaining TTL, restore resumes it from NOW
    b = InMemoryDB()
    b.set_with_ttl(1, "k", "f", "v", 10)         # expires 11 -> 6 left at time 5
    b.set(2, "k2", "g", "w")
    b.get(3, "empty", "x")                       # a read creates an empty entry; backup must not count it
    assert b.backup(5) == "2"
    b.delete(6, "k2", "g")
    assert b.restore(7, 4) == ""                 # no backup at or before 4: unchanged
    assert b.get(8, "k2", "g") == ""
    b.restore(20, 5)
    assert b.get(20, "k2", "g") == "w"
    assert b.get(25, "k", "f") == "v" and b.get(26, "k", "f") == ""
    assert b.backup(30) == "1"                   # k has no live fields left
    # Level 4B: look back, including deletions and TTL
    h = InMemoryDB()
    h.set(1, "a", "f", "x"); h.set(5, "a", "f", "y"); h.delete(8, "a", "f")
    assert h.get_when(9, "a", "f", 1) == "x" and h.get_when(9, "a", "f", 4) == "x"
    assert h.get_when(9, "a", "f", 5) == "y" and h.get_when(9, "a", "f", 7) == "y"
    assert h.get_when(9, "a", "f", 8) == ""      # deleted at 8
    assert h.get_when(9, "a", "f", 0) == ""      # at == 0 means "now"
    h.set_with_ttl(10, "a", "t", "z", 3)
    assert h.get_when(20, "a", "t", 12) == "z" and h.get_when(20, "a", "t", 13) == ""
    assert h.get_when(20, "a", "never", 5) == ""
    print("kv_database: all checks passed")
