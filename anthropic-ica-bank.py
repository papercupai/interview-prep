#!/usr/bin/env python3
"""
Anthropic Technical Advisor — CodeSignal ICA
The banking system: all four levels, to the structure the Coachable brief describes.

WHY THIS FILE EXISTS
--------------------
Per the brief, the bank is the SECOND most-reported system in the seven-system bank
(after the in-memory key-value database, which is anthropic-ica-kv-database.py).
Between them they account for most reported sittings, and the brief names these two
as the pair to rehearse end to end.

This is NOT the generic banking exercise already on the prep page. It follows the
brief's specific level structure:
  L1  create / deposit / transfer, with the exact failure returns
  L2  top spenders by money sent OUT, ties alphabetical, "id(total)"
  L3  2% cashback landing 24 hours later, plus a payment-status query
  L4  merge two accounts, then balance at a past timestamp

THE SHAPE, which is the transferable part:
  * ONE class owns the state; `now` is the first argument of every operation.
  * `_settle(now)` runs at the TOP of every operation, so a due effect is already
    applied when an operation lands at exactly its due time.
  * The outgoing total is aggregated ON WRITE, never recomputed at query time.
  * Balance history is appended ON WRITE, so the L4 look-back is a binary search.

Run it:  python3 anthropic-ica-bank.py
Every check must print PASS. Exit code 0 means the reference is intact.
"""

import heapq
from bisect import bisect_right

MILLISECONDS_IN_1_DAY = 86_400_000
CASHBACK_PERCENT = 2


class Bank:
    def __init__(self):
        # account_id -> {"balance": int, "outgoing": int}
        self.accounts = {}
        # account_id -> ([timestamps], [balances])   for the L4 look-back
        self.history = {}
        # heap of (due_at, seq, payment_id)
        self.pending = []
        self._seq = 0
        # payment_id -> {"account", "amount", "cashback", "due_at", "paid"}
        self.payments = {}
        self._payment_counter = 0
        # account_id -> the id it was merged INTO (so look-back still resolves)
        self.merged_into = {}
        # account_id -> timestamp it stopped existing
        self.merged_at = {}

    # --- internals -------------------------------------------------------

    def _record(self, now, account_id):
        """Append the current balance to this account's history."""
        times, balances = self.history.setdefault(account_id, ([], []))
        bal = self.accounts[account_id]["balance"]
        if times and times[-1] == now:
            balances[-1] = bal          # same instant: overwrite, do not append
        else:
            times.append(now)
            balances.append(bal)

    def _settle(self, now):
        """Apply every cashback due at or before `now`, BEFORE anything else runs."""
        while self.pending and self.pending[0][0] <= now:
            due_at, _, payment_id = heapq.heappop(self.pending)
            p = self.payments[payment_id]
            account_id = p["account"]
            # follow a merge so cashback lands in the surviving account
            while account_id in self.merged_into:
                account_id = self.merged_into[account_id]
            if account_id in self.accounts:
                self.accounts[account_id]["balance"] += p["cashback"]
                self._record(due_at, account_id)   # history stamped at the DUE time
            p["paid"] = True

    def _exists(self, account_id):
        return account_id in self.accounts

    # --- Level 1: initial design & basic functions -----------------------

    def create_account(self, now, account_id):
        self._settle(now)
        if account_id in self.accounts:
            return "false"
        # a merged-away id created again is a BRAND NEW account starting at zero
        self.accounts[account_id] = {"balance": 0, "outgoing": 0}
        self.history[account_id] = ([], [])
        self.merged_at.pop(account_id, None)
        self._record(now, account_id)
        return "true"

    def deposit(self, now, account_id, amount):
        self._settle(now)
        if not self._exists(account_id):
            return ""
        self.accounts[account_id]["balance"] += amount
        self._record(now, account_id)
        return str(self.accounts[account_id]["balance"])

    def transfer(self, now, source_id, target_id, amount):
        self._settle(now)
        if not self._exists(source_id) or not self._exists(target_id):
            return ""
        if source_id == target_id:
            return ""
        if self.accounts[source_id]["balance"] < amount:
            return ""
        self.accounts[source_id]["balance"] -= amount
        self.accounts[source_id]["outgoing"] += amount   # aggregate ON WRITE
        self.accounts[target_id]["balance"] += amount
        self._record(now, source_id)
        self._record(now, target_id)
        return str(self.accounts[source_id]["balance"])

    # --- Level 2: data structures & data processing ----------------------

    def top_spenders(self, now, n):
        self._settle(now)
        ranked = sorted(
            self.accounts.items(),
            key=lambda kv: (-kv[1]["outgoing"], kv[0]),   # desc total, then asc id
        )[:n]
        return [f"{acc_id}({data['outgoing']})" for acc_id, data in ranked]

    # --- Level 3: refactoring & encapsulation (time enters) --------------

    def pay(self, now, account_id, amount):
        self._settle(now)
        if not self._exists(account_id):
            return ""
        if self.accounts[account_id]["balance"] < amount:
            return ""
        self.accounts[account_id]["balance"] -= amount
        self.accounts[account_id]["outgoing"] += amount   # a payment IS money sent out
        self._record(now, account_id)

        self._payment_counter += 1
        payment_id = f"payment{self._payment_counter}"
        self._seq += 1
        due_at = now + MILLISECONDS_IN_1_DAY
        self.payments[payment_id] = {
            "account": account_id,
            "amount": amount,
            "cashback": amount * CASHBACK_PERCENT // 100,   # floor
            "due_at": due_at,
            "paid": False,
        }
        heapq.heappush(self.pending, (due_at, self._seq, payment_id))
        return payment_id

    def get_payment_status(self, now, account_id, payment_id):
        self._settle(now)
        if not self._exists(account_id):
            return ""
        if payment_id not in self.payments:
            return ""
        owner = self.payments[payment_id]["account"]
        while owner in self.merged_into:
            owner = self.merged_into[owner]
        if owner != account_id:
            return ""
        return "CASHBACK_RECEIVED" if self.payments[payment_id]["paid"] else "IN_PROGRESS"

    # --- Level 4: extending design & functionality -----------------------

    def merge_accounts(self, now, account_id_1, account_id_2):
        """Merge account 2 INTO account 1. Account 2 ceases to exist."""
        self._settle(now)
        if account_id_1 == account_id_2:
            return "false"
        if not self._exists(account_id_1) or not self._exists(account_id_2):
            return "false"

        # everything moves: balance, the outgoing total, and pending cashback
        self.accounts[account_id_1]["balance"] += self.accounts[account_id_2]["balance"]
        self.accounts[account_id_1]["outgoing"] += self.accounts[account_id_2]["outgoing"]
        # payment ids are remapped by following merged_into at settle/query time
        self.merged_into[account_id_2] = account_id_1
        self.merged_at[account_id_2] = now

        del self.accounts[account_id_2]
        self._record(now, account_id_1)
        return "true"

    def get_balance(self, now, account_id, time_at):
        """The balance of `account_id` at `time_at`, or "" if it did not exist then."""
        self._settle(now)
        times, balances = self.history.get(account_id, ([], []))
        if not times:
            return ""
        # an account that was merged away stops existing at the merge instant
        if account_id in self.merged_at and time_at >= self.merged_at[account_id]:
            return ""
        i = bisect_right(times, time_at) - 1    # binary search, not a scan
        if i < 0:
            return ""                            # did not exist yet at time_at
        return str(balances[i])


# ---------------------------------------------------------------------------
# Self-test. Every check must print PASS.
# ---------------------------------------------------------------------------

_checks = 0
_failures = 0
DAY = MILLISECONDS_IN_1_DAY


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
    b = Bank()
    check("create is 'true'", b.create_account(1, "a1"), "true")
    check("creating a duplicate is 'false'", b.create_account(2, "a1"), "false")
    check("deposit returns the NEW balance", b.deposit(3, "a1", 100), "100")
    check("deposit accumulates", b.deposit(4, "a1", 50), "150")
    check("deposit to a missing account is empty", b.deposit(5, "nope", 10), "")

    b.create_account(6, "a2")
    check("transfer returns the SOURCE's new balance", b.transfer(7, "a1", "a2", 50), "100")
    check("the target received it", b.deposit(8, "a2", 0), "50")
    check("transfer TO ITSELF is empty", b.transfer(9, "a1", "a1", 10), "")
    check("transfer with insufficient funds is empty", b.transfer(10, "a1", "a2", 10_000), "")
    check("a failed transfer changed nothing", b.deposit(11, "a1", 0), "100")
    check("transfer from a missing account is empty", b.transfer(12, "nope", "a1", 1), "")
    check("transfer to a missing account is empty", b.transfer(13, "a1", "nope", 1), "")


def level2():
    print("\n--- Level 2 · data structures & data processing ---")
    b = Bank()
    for acc in ("a1", "a2", "a3", "b1"):
        b.create_account(1, acc)
        b.deposit(1, acc, 1000)
    b.transfer(2, "a2", "a1", 300)
    b.transfer(3, "a3", "a1", 300)   # tie with a2 on 300 -> alphabetical
    b.transfer(4, "a1", "b1", 100)

    check("ranked by money sent OUT, ties alphabetical",
          b.top_spenders(5, 4), ["a2(300)", "a3(300)", "a1(100)", "b1(0)"])
    check("top N slices the ranking", b.top_spenders(5, 2), ["a2(300)", "a3(300)"])
    check("n larger than the population is fine", len(b.top_spenders(5, 99)), 4)
    check("outgoing counts what was SENT, not received",
          b.top_spenders(5, 4)[3], "b1(0)")

    empty = Bank()
    check("no accounts gives an empty ranking", empty.top_spenders(1, 3), [])


def level3():
    print("\n--- Level 3 · cashback landing 24 hours later ---")
    b = Bank()
    b.create_account(1, "a1")
    b.deposit(1, "a1", 10_000)

    pid = b.pay(100, "a1", 1000)
    check("pay returns an ordinal payment id", pid, "payment1")
    check("the amount left immediately", b.deposit(101, "a1", 0), "9000")
    check("status before the due time", b.get_payment_status(102, "a1", pid), "IN_PROGRESS")

    just_before = 100 + DAY - 1
    check("cashback has NOT landed one tick early",
          b.deposit(just_before, "a1", 0), "9000")
    check("...and the status still says in progress",
          b.get_payment_status(just_before, "a1", pid), "IN_PROGRESS")

    # THE BOUNDARY: the effect is applied BEFORE the operation at exactly the due time
    due = 100 + DAY
    check("AT EXACTLY the due time the cashback is already there",
          b.deposit(due, "a1", 0), "9020")           # 2% of 1000 = 20
    check("status flips at the due time",
          b.get_payment_status(due, "a1", pid), "CASHBACK_RECEIVED")

    # cashback FLOORS — exercised through the real pay path, not by restating the arithmetic
    bf = Bank()
    bf.create_account(1, "f")
    bf.deposit(1, "f", 10_000)
    bf.pay(1, "f", 1049)                      # 2% of 1049 = 20.98 -> 20, not 21
    check("cashback floors rather than rounding",
          bf.deposit(1 + DAY, "f", 0), str(10_000 - 1049 + 20))
    bf2 = Bank()
    bf2.create_account(1, "g")
    bf2.deposit(1, "g", 10_000)
    bf2.pay(1, "g", 49)                       # 2% of 49 = 0.98 -> 0
    check("a cashback that floors to zero adds nothing",
          bf2.deposit(1 + DAY, "g", 0), str(10_000 - 49))

    check("a payment beyond the balance is empty", b.pay(due, "a1", 10 ** 9), "")
    check("a payment from a missing account is empty", b.pay(due, "nope", 1), "")
    check("status for an unknown payment is empty", b.get_payment_status(due, "a1", "payment99"), "")

    b.create_account(due, "a2")
    check("status for another account's payment is empty",
          b.get_payment_status(due, "a2", pid), "")

    # a payment also counts as money sent out
    b2 = Bank()
    b2.create_account(1, "x")
    b2.deposit(1, "x", 500)
    b2.pay(2, "x", 200)
    check("a payment counts toward the outgoing total",
          b2.top_spenders(3, 1), ["x(200)"])


def level4_merge():
    print("\n--- Level 4 · merge one account into another ---")
    b = Bank()
    b.create_account(1, "a1")
    b.create_account(1, "a2")
    b.deposit(1, "a1", 1000)
    b.deposit(1, "a2", 500)
    b.create_account(1, "sink")
    b.transfer(2, "a1", "sink", 100)   # a1 outgoing 100
    b.transfer(3, "a2", "sink", 300)   # a2 outgoing 300

    pid = b.pay(10, "a2", 100)          # a2 pays; cashback due at 10 + DAY
    check("the payment belongs to a2 before the merge",
          b.get_payment_status(11, "a2", pid), "IN_PROGRESS")

    check("merge is 'true'", b.merge_accounts(20, "a1", "a2"), "true")
    check("merging an account into itself is 'false'", b.merge_accounts(21, "a1", "a1"), "false")
    check("merging a now-missing account is 'false'", b.merge_accounts(21, "a1", "a2"), "false")

    # balance moved: a1 900 + a2 (500-300-100)=100  -> 1000
    check("the balance moved into the survivor", b.deposit(22, "a1", 0), "1000")
    check("the merged-away account is gone", b.deposit(22, "a2", 0), "")
    # outgoing moved: 100 + 300 + 100 (the payment) = 500
    check("the outgoing total moved too", b.top_spenders(23, 1), ["a1(500)"])

    # THE TRAP: the pending cashback follows the merge, and the payment id remaps
    check("the payment id now resolves against the SURVIVOR",
          b.get_payment_status(24, "a1", pid), "IN_PROGRESS")
    due = 10 + DAY
    check("the pending cashback lands in the survivor",
          b.deposit(due, "a1", 0), "1002")            # 2% of 100 = 2
    check("and its status flips under the survivor",
          b.get_payment_status(due, "a1", pid), "CASHBACK_RECEIVED")

    # THE OTHER TRAP: re-creating the merged id starts from nothing
    check("the merged id can be created again", b.create_account(due + 1, "a2"), "true")
    check("A RE-CREATED MERGED ID STARTS AT ZERO", b.deposit(due + 2, "a2", 0), "0")
    check("...and with no outgoing history either",
          [s for s in b.top_spenders(due + 3, 9) if s.startswith("a2")], ["a2(0)"])


def level4_look_back():
    print("\n--- Level 4 · balance at a past timestamp ---")
    b = Bank()
    b.create_account(10, "a1")
    b.deposit(20, "a1", 100)
    b.deposit(30, "a1", 100)
    b.deposit(40, "a1", 100)

    check("before the account existed is empty", b.get_balance(100, "a1", 5), "")
    check("at creation the balance is zero", b.get_balance(100, "a1", 10), "0")
    check("at an exact write time", b.get_balance(100, "a1", 20), "100")
    check("between writes sees the earlier", b.get_balance(100, "a1", 29), "100")
    check("after the last write", b.get_balance(100, "a1", 99), "300")
    check("an unknown account is empty", b.get_balance(100, "nope", 50), "")

    # cashback must appear in history at its DUE time, not at settle time
    b2 = Bank()
    b2.create_account(1, "x")
    b2.deposit(1, "x", 1000)
    b2.pay(10, "x", 500)                       # cashback 10, due at 10 + DAY
    due = 10 + DAY
    b2.deposit(due + 5000, "x", 0)             # force a settle well after the due time
    check("history shows the pre-cashback balance just before due",
          b2.get_balance(due + 9000, "x", due - 1), "500")
    check("HISTORY IS STAMPED AT THE DUE TIME, not the settle time",
          b2.get_balance(due + 9000, "x", due), "510")

    # a merged-away account stops existing at the merge instant
    b3 = Bank()
    b3.create_account(1, "p")
    b3.create_account(1, "q")
    b3.deposit(2, "q", 700)
    b3.merge_accounts(50, "p", "q")
    check("look-back BEFORE the merge still resolves", b3.get_balance(100, "q", 10), "700")
    check("AT the merge instant it is gone", b3.get_balance(100, "q", 50), "")
    check("after the merge it stays gone", b3.get_balance(100, "q", 80), "")
    check("the survivor carries the merged balance", b3.get_balance(100, "p", 50), "700")


def shape_guarantees():
    print("\n--- Structural guarantees ---")
    import inspect

    ops = ["create_account", "deposit", "transfer", "top_spenders", "pay",
           "get_payment_status", "merge_accounts", "get_balance"]
    missing = [
        op for op in ops
        if list(inspect.signature(getattr(Bank, op)).parameters)[1] != "now"
    ]
    check("every operation takes `now` as its first real argument", missing, [])

    src = inspect.getsource(Bank)
    check("settling is defined once", src.count("def _settle"), 1)
    check("every public op settles first", src.count("self._settle(now)"), len(ops))
    check("the outgoing total is aggregated on write, never recomputed",
          "sum(" in src, False)


def main():
    level1()
    level2()
    level3()
    level4_merge()
    level4_look_back()
    shape_guarantees()
    print(f"\n{_checks} checks, {_failures} failed.")
    if _failures:
        raise SystemExit(1)
    print("Reference implementation intact.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
