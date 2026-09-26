#!/usr/bin/env python3
"""Anthropic CodeSignal ICA — question bank with worked, self-testing answers.

Two complete four-level projects in the shape the Industry Coding Assessment
actually uses: one problem, four progressive levels, later levels forcing a
refactor of earlier code.

  Problem A — file hosting service   (the public practice scenario)
  Problem B — banking system         (a reported scenario pool)

Run it. It must exit 0 with every check PASS:

    python3 anthropic-ica-question-bank.py

The solutions below are the source of truth for the worked answers printed on
anthropic-codesignal-assessment.html — that page's code blocks are generated
from the regions in this file, so a fix here cannot drift from the page.

Level titles are CodeSignal's own framework names, not invented labels:
  L1 Initial Design & Basic Functions     L3 Refactoring & Encapsulation
  L2 Data Structures & Data Processing    L4 Extending Design & Functionality
"""
from __future__ import annotations

import sys

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got == want:
        print(f"PASS  {label}")
    else:
        print(f"FAIL  {label}\n        got:  {got!r}\n        want: {want!r}")
        FAILURES.append(label)


def check_raises(label: str, fn, exc=RuntimeError) -> None:
    try:
        fn()
    except exc:
        print(f"PASS  {label}")
        return
    except Exception as other:  # wrong exception type is still a failure
        print(f"FAIL  {label}\n        raised {type(other).__name__}, wanted {exc.__name__}")
        FAILURES.append(label)
        return
    print(f"FAIL  {label}\n        nothing raised, wanted {exc.__name__}")
    FAILURES.append(label)


# =============================================================================
# PROBLEM A — file hosting service
# =============================================================================
# region: a-l1
class FileHosting:
    """Level 1 — Initial Design & Basic Functions.

    The whole score of the later levels is decided here, by ONE choice: a file
    is a RECORD, not a bare integer. Level 3 adds a timestamp and a ttl to every
    file and Level 4 has to rewind history; if `self.files[name]` is an int you
    rewrite every method to find out. Cost of the record now: nothing.
    """

    def __init__(self) -> None:
        # name -> {"size": int, "created": int|None, "ttl": int|None}
        self.files: dict[str, dict] = {}

    def file_upload(self, file_name: str, size: int) -> None:
        """Existing name is a runtime exception — NOT an overwrite."""
        if file_name in self.files:
            raise RuntimeError(f"file already exists: {file_name}")
        self.files[file_name] = {"size": size, "created": None, "ttl": None}

    def file_get(self, file_name: str) -> int | None:
        """Missing file returns nothing. Returning 0 is the classic wrong answer:
        0 is a legitimate size, so it collides with 'absent'."""
        record = self.files.get(file_name)
        return None if record is None else record["size"]

    def file_copy(self, source: str, dest: str) -> None:
        """Missing SOURCE raises; existing DEST is overwritten. The asymmetry is
        deliberate and is the single most-missed corner case at Level 1."""
        if source not in self.files:
            raise RuntimeError(f"no such source: {source}")
        self.files[dest] = dict(self.files[source])  # copy, never alias
# endregion: a-l1

# region: a-l2
    def file_search(self, prefix: str) -> list[str]:
        """Level 2 — Data Structures & Data Processing.

        Top 10 by size DESCENDING, ties broken by file name ASCENDING. That is a
        mixed-direction sort, so one `reverse=True` cannot express it: negate the
        numeric key instead and leave the string key ascending.
        """
        matches = [name for name in self.files if name.startswith(prefix)]
        matches.sort(key=lambda name: (-self.files[name]["size"], name))
        return matches[:10]
# endregion: a-l2

# region: a-l3
    # Level 3 — Refactoring & Encapsulation.
    #
    # Every operation gains a timestamp, and a file may carry a ttl. Do NOT fork
    # a parallel set of *_at methods: express the untimed Level 1/2 calls in
    # terms of the timed ones, or the two implementations drift and Level 1's
    # tests start failing while you are working on Level 3.
    def _alive(self, name: str, timestamp: int) -> bool:
        record = self.files.get(name)
        if record is None:
            return False
        if record["ttl"] is None:
            return True
        return timestamp < record["created"] + record["ttl"]

    def file_upload_at(self, timestamp: int, file_name: str, file_size: int,
                       ttl: int | None = None) -> None:
        if self._alive(file_name, timestamp):
            raise RuntimeError(f"file already exists: {file_name}")
        self.files[file_name] = {"size": file_size, "created": timestamp, "ttl": ttl}

    def file_get_at(self, timestamp: int, file_name: str) -> int | None:
        return self.files[file_name]["size"] if self._alive(file_name, timestamp) else None

    def file_copy_at(self, timestamp: int, file_from: str, file_to: str) -> None:
        if not self._alive(file_from, timestamp):
            raise RuntimeError(f"no such source: {file_from}")
        source = self.files[file_from]
        # The COPY inherits the source's REMAINING life, not a fresh full ttl.
        remaining = None if source["ttl"] is None else source["created"] + source["ttl"] - timestamp
        self.files[file_to] = {"size": source["size"], "created": timestamp, "ttl": remaining}

    def file_search_at(self, timestamp: int, prefix: str) -> list[str]:
        matches = [n for n in self.files if n.startswith(prefix) and self._alive(n, timestamp)]
        matches.sort(key=lambda name: (-self.files[name]["size"], name))
        return matches[:10]
# endregion: a-l3

# region: a-l4
    # Level 4 — Extending Design & Functionality.
    #
    # ROLLBACK(timestamp) restores the state as of that timestamp and says "all
    # ttls should be recalculated accordingly". Read that clause twice: a file
    # uploaded at 10 with ttl 100 must, after a rollback to 50, still expire at
    # 110 — you rewind the WORLD CLOCK, you do not re-start the file's life.
    #
    # So keep the ORIGINAL created/ttl and simply drop anything not yet born or
    # already dead at the rollback instant. Files whose created > timestamp never
    # existed; files already expired stay expired.
    def rollback(self, timestamp: int) -> None:
        for name in list(self.files):
            record = self.files[name]
            created = record["created"]
            if created is not None and created > timestamp:
                del self.files[name]          # not yet uploaded at that instant
            elif not self._alive(name, timestamp):
                del self.files[name]          # already expired at that instant
# endregion: a-l4


def test_problem_a() -> None:
    print("\n--- Problem A · file hosting service ---")
    # Level 1
    fs = FileHosting()
    fs.file_upload("file-1.zip", 4321)
    check("A-L1 get returns the size", fs.file_get("file-1.zip"), 4321)
    check("A-L1 missing file returns nothing", fs.file_get("nope.txt"), None)
    check_raises("A-L1 duplicate upload raises", lambda: fs.file_upload("file-1.zip", 1))
    check_raises("A-L1 copy of a missing source raises", lambda: fs.file_copy("gone", "x"))
    fs.file_upload("dir-b/file-4.mdx", 3378)
    fs.file_copy("file-1.zip", "dir-b/file-4.mdx")
    check("A-L1 copy OVERWRITES an existing dest", fs.file_get("dir-b/file-4.mdx"), 4321)
    fs.file_upload("zero.bin", 0)
    check("A-L1 a 0-byte file is not 'absent'", fs.file_get("zero.bin"), 0)

    # Level 2
    fs = FileHosting()
    for name, size in [("dir/f-a", 100), ("dir/f-b", 300), ("dir/f-c", 300),
                       ("other/f-d", 900)]:
        fs.file_upload(name, size)
    check("A-L2 size desc, then name asc on a tie",
          fs.file_search("dir/"), ["dir/f-b", "dir/f-c", "dir/f-a"])
    check("A-L2 prefix is respected", fs.file_search("other/"), ["other/f-d"])
    check("A-L2 no match returns empty", fs.file_search("zzz"), [])
    fs = FileHosting()
    for i in range(15):
        fs.file_upload(f"p/f{i:02d}", i)
    check("A-L2 caps at ten results", len(fs.file_search("p/")), 10)
    check("A-L2 keeps the ten LARGEST", fs.file_search("p/")[0], "p/f14")

    # Level 3
    fs = FileHosting()
    fs.file_upload_at(10, "a.txt", 100, 20)          # alive 10 -> 29
    check("A-L3 alive inside its ttl", fs.file_get_at(25, "a.txt"), 100)
    check("A-L3 dead at created+ttl exactly", fs.file_get_at(30, "a.txt"), None)
    fs.file_upload_at(5, "forever.txt", 7)            # no ttl
    check("A-L3 no ttl means infinite", fs.file_get_at(10_000, "forever.txt"), 7)
    check("A-L3 search hides dead files", fs.file_search_at(30, "a"), [])
    fs.file_upload_at(40, "a.txt", 55, 10)            # re-upload after expiry is legal
    check("A-L3 re-upload after expiry is allowed", fs.file_get_at(41, "a.txt"), 55)
    check_raises("A-L3 upload over a LIVE file still raises",
                 lambda: fs.file_upload_at(42, "a.txt", 1))
    fs2 = FileHosting()
    fs2.file_upload_at(0, "src", 10, 100)             # dies at 100
    fs2.file_copy_at(90, "src", "dst")
    check("A-L3 copy inherits REMAINING life, not a fresh ttl",
          fs2.file_get_at(99, "dst"), 10)
    check("A-L3 the copy dies with its source", fs2.file_get_at(100, "dst"), None)

    # Level 4
    fs = FileHosting()
    fs.file_upload_at(10, "keep.txt", 1, 100)         # born 10, dies 110
    fs.file_upload_at(60, "later.txt", 2)             # born after the rollback point
    fs.rollback(50)
    check("A-L4 rollback drops files not yet uploaded", fs.file_get_at(50, "later.txt"), None)
    check("A-L4 rollback keeps files alive at that instant", fs.file_get_at(50, "keep.txt"), 1)
    check("A-L4 ttl is recalculated, NOT restarted — still dies at 110",
          fs.file_get_at(110, "keep.txt"), None)
    check("A-L4 and is still alive just before 110", fs.file_get_at(109, "keep.txt"), 1)
    fs = FileHosting()
    fs.file_upload_at(0, "gone.txt", 1, 5)            # died at 5
    fs.rollback(50)
    check("A-L4 already-expired files stay expired", fs.file_get_at(50, "gone.txt"), None)


# =============================================================================
# PROBLEM B — banking system
# =============================================================================
# region: b-l1
class BankingSystem:
    """Level 1 — Initial Design & Basic Functions.

    Same discipline as Problem A: an account is a RECORD. Level 2 needs a
    running outgoing total, Level 3 needs scheduled payments, Level 4 needs to
    fold two accounts together. Every one of those is a field, not a rewrite.

    Note the return contract: a balance, or None for "could not do it". Do not
    raise here and do not return False — the tests distinguish 0 from None.
    """

    def __init__(self) -> None:
        self.accounts: dict[str, dict] = {}
        # (due_timestamp, scheduling_sequence, account_id, amount)
        self.scheduled: list[tuple[int, int, str, int]] = []
        self.next_payment = 1

    def create_account(self, timestamp: int, account_id: str) -> bool:
        if account_id in self.accounts:
            return False
        self.accounts[account_id] = {"balance": 0, "outgoing": 0}
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self._run_due(timestamp)
        if account_id not in self.accounts:
            return None
        self.accounts[account_id]["balance"] += amount
        return self.accounts[account_id]["balance"]

    def transfer(self, timestamp: int, source: str, target: str, amount: int) -> int | None:
        self._run_due(timestamp)
        if source not in self.accounts or target not in self.accounts:
            return None
        if source == target:                 # a self-transfer is not a no-op, it is invalid
            return None
        if self.accounts[source]["balance"] < amount:
            return None                      # insufficient funds: NOTHING moves
        self.accounts[source]["balance"] -= amount
        self.accounts[source]["outgoing"] += amount
        self.accounts[target]["balance"] += amount
        return self.accounts[source]["balance"]
# endregion: b-l1

# region: b-l2
    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        """Level 2 — Data Structures & Data Processing.

        Top n by total OUTGOING descending, ties by account_id ascending. The
        trap is scoring this from transaction history at query time; keep the
        running total on the account (Level 1 already has the field) so this is
        a sort, not a scan. Accounts that never spent still rank, at 0.
        """
        self._run_due(timestamp)
        ranked = sorted(self.accounts, key=lambda a: (-self.accounts[a]["outgoing"], a))
        return ranked[:max(0, n)]
# endregion: b-l2

# region: b-l3
    # Level 3 — Refactoring & Encapsulation.
    #
    # Payments become deferred. The requirement that decides the score is
    # ORDERING: when several payments come due at the same instant they execute
    # in the order they were SCHEDULED, and they must run BEFORE whatever
    # operation carried this timestamp. That is why every public method above
    # opens with self._run_due(timestamp) — one seam, not eight copies.
    #
    # A due payment with insufficient funds is SKIPPED, not retried and not
    # partially applied.
    def schedule_payment(self, timestamp: int, account_id: str, amount: int,
                         delay: int) -> str | None:
        self._run_due(timestamp)
        if account_id not in self.accounts:
            return None
        sequence = self.next_payment
        self.next_payment += 1
        payment_id = f"payment{sequence}"
        # Keep the queue ordered by (due, scheduling sequence) so that payments
        # falling due at the SAME instant execute in the order they were made.
        self.scheduled.append((timestamp + delay, sequence, account_id, amount))
        self.scheduled.sort(key=lambda row: (row[0], row[1]))
        return payment_id

    def cancel_payment(self, timestamp: int, account_id: str, payment_id: str) -> bool:
        self._run_due(timestamp)
        for row in self.scheduled:
            _due, sequence, owner, _amount = row
            if f"payment{sequence}" == payment_id and owner == account_id:
                self.scheduled.remove(row)
                return True
        return False                         # already executed, or not this account's

    def _run_due(self, timestamp: int) -> None:
        while self.scheduled and self.scheduled[0][0] <= timestamp:
            _due, _sequence, account_id, amount = self.scheduled.pop(0)
            account = self.accounts.get(account_id)
            if account is None or account["balance"] < amount:
                continue                     # skip, do not retry, do not go negative
            account["balance"] -= amount
            account["outgoing"] += amount
# endregion: b-l3

# region: b-l4
    # Level 4 — Extending Design & Functionality.
    #
    # MERGE_ACCOUNTS folds account 2 into account 1. Enumerate what "merge"
    # actually owns before writing a line — every field you forget is a silent
    # partial-credit loss:
    #   balance    summed
    #   outgoing   summed, so Level 2's ranking stays correct afterwards
    #   scheduled  re-pointed at the surviving id, keeping their due order
    #   identity   the absorbed id must stop resolving entirely
    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool:
        self._run_due(timestamp)
        if account_id_1 == account_id_2:
            return False
        if account_id_1 not in self.accounts or account_id_2 not in self.accounts:
            return False
        absorbed = self.accounts.pop(account_id_2)
        survivor = self.accounts[account_id_1]
        survivor["balance"] += absorbed["balance"]
        survivor["outgoing"] += absorbed["outgoing"]
        self.scheduled = [
            (due, sequence, account_id_1 if owner == account_id_2 else owner, amount)
            for due, sequence, owner, amount in self.scheduled
        ]
        return True
# endregion: b-l4


def test_problem_b() -> None:
    print("\n--- Problem B · banking system ---")
    # Level 1
    bank = BankingSystem()
    check("B-L1 create returns True", bank.create_account(1, "acc1"), True)
    check("B-L1 duplicate create returns False", bank.create_account(2, "acc1"), False)
    check("B-L1 deposit into a missing account returns None",
          bank.deposit(3, "ghost", 100), None)
    check("B-L1 deposit returns the new balance", bank.deposit(4, "acc1", 2000), 2000)
    bank.create_account(5, "acc2")
    check("B-L1 transfer returns the SOURCE balance", bank.transfer(6, "acc1", "acc2", 500), 1500)
    check("B-L1 target was credited", bank.deposit(7, "acc2", 0), 500)
    check("B-L1 insufficient funds moves nothing", bank.transfer(8, "acc2", "acc1", 9999), None)
    check("B-L1 ... and the balance is untouched", bank.deposit(9, "acc2", 0), 500)
    check("B-L1 self-transfer is invalid", bank.transfer(10, "acc1", "acc1", 1), None)
    check("B-L1 transfer to a missing account is invalid",
          bank.transfer(11, "acc1", "ghost", 1), None)

    # Level 2
    bank = BankingSystem()
    for name in ["acc1", "acc2", "acc3", "acc4"]:
        bank.create_account(1, name)
        bank.deposit(1, name, 1000)
    bank.transfer(2, "acc3", "acc1", 300)
    bank.transfer(3, "acc2", "acc1", 300)     # tie with acc3 at 300
    bank.transfer(4, "acc1", "acc4", 900)
    check("B-L2 outgoing desc, then id asc on a tie",
          bank.top_spenders(5, 4), ["acc1", "acc2", "acc3", "acc4"])
    check("B-L2 n larger than the population is fine", len(bank.top_spenders(5, 99)), 4)
    check("B-L2 n <= 0 returns empty", bank.top_spenders(5, 0), [])
    check("B-L2 non-spenders still rank, at zero", bank.top_spenders(5, 4)[-1], "acc4")

    # Level 3
    bank = BankingSystem()
    bank.create_account(1, "acc1")
    bank.deposit(1, "acc1", 1000)
    pid = bank.schedule_payment(2, "acc1", 400, 10)   # due at 12
    check("B-L3 schedule returns a payment id", pid, "payment1")
    check("B-L3 not yet executed before it is due", bank.deposit(11, "acc1", 0), 1000)
    check("B-L3 executes when the clock reaches it", bank.deposit(12, "acc1", 0), 600)
    check("B-L3 cancelling an executed payment returns False",
          bank.cancel_payment(13, "acc1", pid), False)
    bank2 = BankingSystem()
    bank2.create_account(1, "acc1")
    bank2.deposit(1, "acc1", 1000)
    p2 = bank2.schedule_payment(2, "acc1", 100, 10)
    check("B-L3 cancel before it is due returns True",
          bank2.cancel_payment(5, "acc1", p2), True)
    check("B-L3 a cancelled payment never executes", bank2.deposit(50, "acc1", 0), 1000)
    bank3 = BankingSystem()
    bank3.create_account(1, "acc1")
    bank3.deposit(1, "acc1", 250)
    bank3.schedule_payment(2, "acc1", 200, 5)         # due 7, affordable first
    bank3.schedule_payment(2, "acc1", 200, 5)         # due 7, then unaffordable
    check("B-L3 same-instant payments run in scheduling order; the second is skipped",
          bank3.deposit(7, "acc1", 0), 50)
    check("B-L3 skipped payment did not drive the balance negative",
          bank3.deposit(7, "acc1", 0) >= 0, True)
    bank4 = BankingSystem()
    bank4.create_account(1, "acc1")
    bank4.deposit(1, "acc1", 1000)
    bank4.schedule_payment(2, "acc1", 400, 10)
    check("B-L3 a due payment counts toward top_spenders",
          bank4.top_spenders(12, 1), ["acc1"])

    # Level 4
    bank = BankingSystem()
    bank.create_account(1, "acc1")
    bank.create_account(1, "acc2")
    bank.deposit(1, "acc1", 1000)
    bank.deposit(1, "acc2", 500)
    bank.transfer(2, "acc2", "acc1", 200)             # acc2 outgoing = 200
    check("B-L4 merge returns True", bank.merge_accounts(3, "acc1", "acc2"), True)
    check("B-L4 balances are summed", bank.deposit(4, "acc1", 0), 1500)
    check("B-L4 the absorbed id stops resolving", bank.deposit(4, "acc2", 0), None)
    check("B-L4 outgoing is summed, so the ranking stays correct",
          bank.top_spenders(5, 1), ["acc1"])
    check("B-L4 merging an account with itself returns False",
          bank.merge_accounts(6, "acc1", "acc1"), False)
    check("B-L4 merging a missing account returns False",
          bank.merge_accounts(6, "acc1", "ghost"), False)
    bank2 = BankingSystem()
    bank2.create_account(1, "acc1")
    bank2.create_account(1, "acc2")
    bank2.deposit(1, "acc2", 1000)
    bank2.schedule_payment(2, "acc2", 300, 20)        # due 22, owned by acc2
    bank2.merge_accounts(3, "acc1", "acc2")
    check("B-L4 a scheduled payment survives the merge and debits the survivor",
          bank2.deposit(22, "acc1", 0), 700)


if __name__ == "__main__":
    test_problem_a()
    test_problem_b()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILING CHECK(S):")
        for label in FAILURES:
            print(f"  - {label}")
        sys.exit(1)
    print("all checks green")
    sys.exit(0)
