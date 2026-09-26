#!/usr/bin/env python3
"""
Anthropic Technical Advisor — CodeSignal ICA
The in-memory key-value database: all four levels, BOTH Level 4 variants.

WHY THIS FILE EXISTS
--------------------
Per the Coachable brief for this role, the problem is drawn from a bank of seven
systems, and this one is "most often reported, by a wide margin". It is the single
highest-value system to be able to write from a blank file.

The shape matters more than the content. Notice:
  * ONE class owns all the state. No logic in a dispatcher.
  * EVERY internal method takes `now` from Level 1 onward, even though Level 1
    ignores it. That is why Level 3 adds no structural change at all.
  * ONE liveness helper, called at the top of every read.
  * History and backups are written ON THE WAY IN, so the Level 4 queries are
    lookups rather than reconstructions.

Run it:  python3 anthropic-ica-kv-database.py
Every check must print PASS. Exit code 0 means the reference is intact.
"""

from bisect import bisect_right


class InMemoryDB:
    def __init__(self):
        # key -> field -> (value, expires_at or None)
        self.records = {}
        # key -> field -> ([timestamps], [(value, expires_at)])  for look-back
        self.history = {}
        self.backup_times = []
        self.backups = []

    # --- the one check every read goes through ---------------------------

    def _alive(self, key, field, now):
        rec = self.records.get(key)
        if rec is None or field not in rec:
            return False
        _, expires_at = rec[field]
        # dead at EXACTLY expires_at — this boundary is tested
        return expires_at is None or now < expires_at

    def _history(self, now, key, field, value, expires_at):
        times, entries = self.history.setdefault(key, {}).setdefault(field, ([], []))
        times.append(now)
        entries.append((value, expires_at))

    def _write(self, now, key, field, value, expires_at):
        self.records.setdefault(key, {})[field] = (value, expires_at)
        self._history(now, key, field, value, expires_at)

    # --- Level 1: initial design & basic functions -----------------------

    def set(self, now, key, field, value):
        self._write(now, key, field, value, None)
        return ""

    def get(self, now, key, field):
        if not self._alive(key, field, now):
            return ""
        return self.records[key][field][0]

    def delete(self, now, key, field):
        if not self._alive(key, field, now):
            return "false"
        del self.records[key][field]
        self._history(now, key, field, None, None)  # tombstone keeps look-back honest
        return "true"

    # Some versions add these two. They are pure Level 1 rule-checking.
    def compare_and_set(self, now, key, field, expected, new_value):
        if not self._alive(key, field, now):
            return "false"
        if self.records[key][field][0] != expected:
            return "false"
        _, expires_at = self.records[key][field]
        self._write(now, key, field, new_value, expires_at)  # CAS preserves the TTL
        return "true"

    def compare_and_delete(self, now, key, field, expected):
        if not self._alive(key, field, now):
            return "false"
        if self.records[key][field][0] != expected:
            return "false"
        return self.delete(now, key, field)

    # --- Level 2: data structures & data processing ----------------------

    def scan(self, now, key):
        return self.scan_by_prefix(now, key, "")

    def scan_by_prefix(self, now, key, prefix=""):
        rec = self.records.get(key, {})
        live = sorted(
            f for f in rec if f.startswith(prefix) and self._alive(key, f, now)
        )
        # exact output format: "field(value), field(value)" — comma-SPACE separator
        return ", ".join(f"{f}({rec[f][0]})" for f in live)

    # --- Level 3: refactoring & encapsulation (time enters the model) ----

    def set_with_ttl(self, now, key, field, value, ttl):
        self._write(now, key, field, value, now + ttl)
        return ""

    # --- Level 4, variant A: backup and restore --------------------------

    def backup(self, now):
        snapshot = {}
        for key, rec in self.records.items():
            fields = {
                # store REMAINING ttl, not the absolute expiry — restore resumes it
                f: (v, None if exp is None else exp - now)
                for f, (v, exp) in rec.items()
                if exp is None or now < exp
            }
            if fields:
                snapshot[key] = fields
        self.backup_times.append(now)
        self.backups.append(snapshot)
        return str(len(snapshot))

    def restore(self, now, at):
        i = bisect_right(self.backup_times, at) - 1  # latest backup AT OR BEFORE `at`
        if i < 0:
            return ""
        self.records = {
            key: {
                f: (v, None if rem is None else now + rem)  # ttl resumes from NOW
                for f, (v, rem) in fields.items()
            }
            for key, fields in self.backups[i].items()
        }
        return ""

    # --- Level 4, variant B: look back -----------------------------------

    def get_when(self, now, key, field, at):
        if at == 0:
            return self.get(now, key, field)
        times, entries = self.history.get(key, {}).get(field, ([], []))
        i = bisect_right(times, at) - 1  # binary search — a linear scan fails the bound
        if i < 0:
            return ""
        value, expires_at = entries[i]
        alive_then = value is not None and (expires_at is None or at < expires_at)
        return value if alive_then else ""


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
    db = InMemoryDB()
    check("set returns empty string", db.set(1, "A", "x", "1"), "")
    check("get returns the value", db.get(2, "A", "x"), "1")
    check("get on a missing field returns empty", db.get(2, "A", "nope"), "")
    check("get on a missing key returns empty", db.get(2, "ZZ", "x"), "")
    check("delete an existing field is 'true'", db.delete(3, "A", "x"), "true")
    check("the field is gone after delete", db.get(4, "A", "x"), "")
    check("delete a missing field is 'false'", db.delete(4, "A", "x"), "false")

    db.set(5, "A", "y", "7")
    check("CAS with the wrong expected is 'false'", db.compare_and_set(6, "A", "y", "9", "8"), "false")
    check("CAS left the value alone", db.get(6, "A", "y"), "7")
    check("CAS with the right expected is 'true'", db.compare_and_set(7, "A", "y", "7", "8"), "true")
    check("CAS wrote the new value", db.get(7, "A", "y"), "8")
    check("CAD on a missing field is 'false'", db.compare_and_delete(8, "A", "gone", "1"), "false")
    check("CAD with the right expected is 'true'", db.compare_and_delete(8, "A", "y", "8"), "true")


def level2():
    print("\n--- Level 2 · data structures & data processing ---")
    db = InMemoryDB()
    db.set(1, "A", "banana", "2")
    db.set(1, "A", "apple", "1")
    db.set(1, "A", "cherry", "3")
    check("scan is sorted alphabetically, comma-space",
          db.scan(2, "A"), "apple(1), banana(2), cherry(3)")
    check("prefix scan filters and keeps the format",
          db.scan_by_prefix(2, "A", "b"), "banana(2)")
    check("a prefix matching nothing returns empty", db.scan_by_prefix(2, "A", "z"), "")
    check("scan of a missing key returns empty", db.scan(2, "NOPE"), "")

    db.set(3, "B", "ab", "1")
    db.set(3, "B", "abc", "2")
    db.set(3, "B", "b", "3")
    check("prefix is a prefix, not a substring",
          db.scan_by_prefix(4, "B", "ab"), "ab(1), abc(2)")


def level3():
    print("\n--- Level 3 · refactoring & encapsulation (TTL) ---")
    db = InMemoryDB()
    db.set_with_ttl(1, "A", "x", "1", 10)
    check("alive before expiry", db.get(10, "A", "x"), "1")
    check("DEAD AT EXACTLY timestamp + ttl", db.get(11, "A", "x"), "")
    check("still dead after expiry", db.get(50, "A", "x"), "")

    # an update resets the TTL
    db2 = InMemoryDB()
    db2.set_with_ttl(1, "A", "x", "1", 10)
    db2.set_with_ttl(5, "A", "x", "2", 10)
    check("an update resets the TTL (old expiry passed)", db2.get(12, "A", "x"), "2")
    check("the reset TTL expires at its own boundary", db2.get(15, "A", "x"), "")

    # a plain set clears the TTL
    db3 = InMemoryDB()
    db3.set_with_ttl(1, "A", "x", "1", 5)
    db3.set(2, "A", "x", "2")
    check("a plain set clears the expiry", db3.get(100, "A", "x"), "2")

    # LEVEL 2 MUST HONOUR EXPIRY — the most-missed requirement on this level
    db4 = InMemoryDB()
    db4.set(1, "A", "keep", "1")
    db4.set_with_ttl(1, "A", "fade", "2", 5)
    check("scan includes a live TTL field", db4.scan(3, "A"), "fade(2), keep(1)")
    check("SCAN DROPS AN EXPIRED FIELD", db4.scan(6, "A"), "keep(1)")
    check("prefix scan also drops it", db4.scan_by_prefix(6, "A", "f"), "")
    check("get on an expired field is empty", db4.get(6, "A", "fade"), "")
    check("delete on an expired field is 'false'", db4.delete(6, "A", "fade"), "false")
    check("CAS on an expired field is 'false'",
          db4.compare_and_set(6, "A", "fade", "2", "3"), "false")


def level4_backup_restore():
    print("\n--- Level 4 variant A · backup and restore ---")
    db = InMemoryDB()
    db.set(1, "A", "permanent", "p")
    db.set_with_ttl(1, "A", "temp", "t", 100)     # expires at 101
    check("backup reports the record count", db.backup(10), "1")

    db.set(20, "A", "added-after", "z")
    check("the live record has the later write", db.get(21, "A", "added-after"), "z")

    db.restore(50, 10)
    check("restore removed a write made after the backup",
          db.get(51, "A", "added-after"), "")
    check("restore brought back the permanent field", db.get(51, "A", "permanent"), "p")

    # The whole point: the TTL RESUMES from the restore time, it does not keep
    # its original absolute expiry. Backed up at t=10 with 91 remaining, restored
    # at t=50, so it must now die at 141 — not at the original 101.
    check("TTL survives past its ORIGINAL expiry after a late restore",
          db.get(120, "A", "temp"), "t")
    check("...and dies at restore_time + remaining", db.get(141, "A", "temp"), "")

    # "latest backup at or before T"
    db2 = InMemoryDB()
    db2.set(1, "A", "v", "one")
    db2.backup(10)
    db2.set(20, "A", "v", "two")
    db2.backup(30)
    db2.set(40, "A", "v", "three")
    db2.restore(100, 25)
    check("restore picks the latest backup AT OR BEFORE the time",
          db2.get(101, "A", "v"), "one")
    db2.restore(200, 30)
    check("an exact backup time is included (at-or-before)",
          db2.get(201, "A", "v"), "two")
    db3 = InMemoryDB()
    db3.set(1, "A", "v", "one")
    check("restoring with no backup at all is a no-op", db3.restore(5, 5), "")

    # an expired field is not carried into the backup at all
    db4 = InMemoryDB()
    db4.set_with_ttl(1, "A", "gone", "g", 5)
    db4.set(1, "A", "kept", "k")
    check("backup skips already-expired fields", db4.backup(10), "1")
    db4.restore(20, 10)
    check("the expired field did not come back", db4.get(21, "A", "gone"), "")
    check("the live one did", db4.get(21, "A", "kept"), "k")


def level4_look_back():
    print("\n--- Level 4 variant B · look-back get ---")
    db = InMemoryDB()
    db.set(10, "A", "x", "first")
    db.set(20, "A", "x", "second")
    db.set(30, "A", "x", "third")
    check("look-back before any write is empty", db.get_when(100, "A", "x", 5), "")
    check("look-back at the exact write time sees it", db.get_when(100, "A", "x", 10), "first")
    check("look-back between writes sees the earlier", db.get_when(100, "A", "x", 19), "first")
    check("look-back at the second write", db.get_when(100, "A", "x", 20), "second")
    check("look-back after the last write", db.get_when(100, "A", "x", 99), "third")
    check("at == 0 falls through to a normal get", db.get_when(100, "A", "x", 0), "third")
    check("look-back on an unknown field is empty", db.get_when(100, "A", "nope", 50), "")

    # a delete must be visible to look-back as a tombstone
    db2 = InMemoryDB()
    db2.set(10, "A", "x", "v")
    db2.delete(20, "A", "x")
    check("before the delete the value is visible", db2.get_when(100, "A", "x", 15), "v")
    check("AT the delete the tombstone wins", db2.get_when(100, "A", "x", 20), "")
    check("after the delete it stays gone", db2.get_when(100, "A", "x", 50), "")

    # look-back must respect the TTL that was in force at that time
    db3 = InMemoryDB()
    db3.set_with_ttl(10, "A", "x", "v", 10)  # alive [10, 20)
    check("look-back inside the lifetime", db3.get_when(100, "A", "x", 15), "v")
    check("look-back AT the historical expiry is empty", db3.get_when(100, "A", "x", 20), "")
    check("look-back after the historical expiry is empty", db3.get_when(100, "A", "x", 30), "")


def shape_guarantees():
    """The brief's structural advice, asserted so it cannot rot."""
    print("\n--- Structural guarantees ---")
    import inspect

    # every public operation takes `now` first — this is what makes L3 free
    ops = ["set", "get", "delete", "scan", "scan_by_prefix", "set_with_ttl",
           "backup", "restore", "get_when", "compare_and_set", "compare_and_delete"]
    missing = [
        op for op in ops
        if list(inspect.signature(getattr(InMemoryDB, op)).parameters)[1] != "now"
    ]
    check("every operation takes `now` as its first real argument", missing, [])

    # the liveness check is in exactly one place
    src = inspect.getsource(InMemoryDB)
    check("liveness is defined once", src.count("def _alive"), 1)
    check("history is written through one helper", src.count("def _history"), 1)


def main():
    level1()
    level2()
    level3()
    level4_backup_restore()
    level4_look_back()
    shape_guarantees()
    print(f"\n{_checks} checks, {_failures} failed.")
    if _failures:
        raise SystemExit(1)
    print("Reference implementation intact.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
