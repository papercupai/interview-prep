"""
2. Bank: simplest timed-test answer

- _settle(now) is the first line of EVERY method. It pays any cashback due at or before now, so a payment landing at exactly its due time is already credited when the operation runs.
- Three dicts instead of one dict of dicts: balance[id] (an id is an account iff it is in here), sent = defaultdict(int), hist = defaultdict(list). You write self.balance[a] instead of self.acc[a]["balance"], and sent and hist never need "create it if missing".
- Payments are dicts in creation order. The delay is fixed, so creation order is also due order, and _settle is a plain loop with no heap.
- Merge: pop the removed account's balance and sent into the kept one, then point its payments at the kept account. Pending cashback follows the money with no alias chains to chase.
- Look-back: append (time, balance) on every change, then walk the list backwards to the first entry at or before `at`. A merged-away id logs None, so it reads as "did not exist" from that time on.
"""

from collections import defaultdict

DAY = 86_400_000


class Bank:
    def __init__(self):
        self.balance = {}              # id -> balance   (an id is an account iff it is here)
        self.sent = defaultdict(int)   # id -> money sent out (transfers + payments)
        self.hist = defaultdict(list)  # id -> [(time, balance or None)]   None = merged away
        self.payments = {}             # payment_id -> {"acc", "due", "cashback", "paid"}

    def _log(self, t, a):
        self.hist[a].append((t, self.balance.get(a)))  # .get: None once the id is gone

    def _settle(self, now):  # FIRST line of every method
        for p in self.payments.values():
            if not p["paid"] and p["due"] <= now:
                p["paid"] = True
                self.balance[p["acc"]] += p["cashback"]
                self._log(p["due"], p["acc"])  # history stamped at the DUE time

    # Level 1
    def create_account(self, now, a):
        self._settle(now)
        if a in self.balance:
            return "false"
        self.balance[a] = 0
        self._log(now, a)
        return "true"

    def deposit(self, now, a, amount):
        self._settle(now)
        if a not in self.balance:
            return ""
        self.balance[a] += amount
        self._log(now, a)
        return str(self.balance[a])

    def transfer(self, now, src, dst, amount):
        self._settle(now)
        if src == dst or src not in self.balance or dst not in self.balance or self.balance[src] < amount:
            return ""
        self.balance[src] -= amount
        self.balance[dst] += amount
        self.sent[src] += amount
        self._log(now, src)
        self._log(now, dst)
        return str(self.balance[src])

    # Level 2
    def top_spenders(self, now, n):
        self._settle(now)
        ranked = sorted(self.balance, key=lambda a: (-self.sent[a], a))
        result = []
        for a in ranked[:n]:
            result.append(f"{a}({self.sent[a]})")
        return result

    # Level 3
    def pay(self, now, a, amount):
        self._settle(now)
        if a not in self.balance or self.balance[a] < amount:
            return ""
        self.balance[a] -= amount
        self.sent[a] += amount  # a payment is money sent out
        self._log(now, a)
        pid = f"payment{len(self.payments) + 1}"
        self.payments[pid] = {"acc": a, "due": now + DAY, "cashback": amount * 2 // 100, "paid": False}
        return pid

    def get_payment_status(self, now, a, pid):
        self._settle(now)
        p = self.payments.get(pid)
        if p is None or p["acc"] != a:
            return ""
        if p["paid"]:
            return "CASHBACK_RECEIVED"
        return "IN_PROGRESS"

    # Level 4
    def merge_accounts(self, now, keep, gone):
        self._settle(now)
        if keep == gone or keep not in self.balance or gone not in self.balance:
            return "false"
        self.balance[keep] += self.balance.pop(gone)
        self.sent[keep] += self.sent.pop(gone, 0)  # pop: a re-created id starts from zero
        for p in self.payments.values():
            if p["acc"] == gone:
                p["acc"] = keep  # pending cashback follows the money
        self._log(now, keep)
        self._log(now, gone)  # logs None: "did not exist" from here on
        return "true"

    def get_balance(self, now, a, at):
        self._settle(now)
        for t, bal in reversed(self.hist[a]):
            if t <= at:
                return "" if bal is None else str(bal)
        return ""  # did not exist yet


# ---- tests: python3 bank.py ----
if __name__ == "__main__":
    b = Bank()
    # Level 1 + 2: the page's "check yourself"
    assert b.create_account(1, "a") == "true" and b.create_account(1, "b") == "true"
    assert b.create_account(2, "a") == "false"
    assert b.deposit(3, "a", 200) == "200" and b.deposit(3, "zz", 5) == ""
    assert b.transfer(4, "a", "b", 50) == "150"
    assert b.top_spenders(5, 2) == ["a(50)", "b(0)"]
    assert b.transfer(5, "a", "a", 1) == ""        # self-transfer
    assert b.transfer(5, "b", "a", 999) == ""      # insufficient funds
    assert b.transfer(5, "a", "zz", 1) == ""       # missing id
    assert b.top_spenders(6, 2) == ["a(50)", "b(0)"]   # failed transfers don't count
    # Level 3: cashback lands at exactly +1 day, BEFORE the operation at that instant
    assert b.pay(10, "a", 100) == "payment1"       # 2% of 100 = 2
    assert b.pay(10, "a", 1000) == ""
    assert b.get_payment_status(11, "a", "payment1") == "IN_PROGRESS"
    assert b.get_payment_status(11, "b", "payment1") == ""
    assert b.deposit(10 + DAY, "a", 0) == "52"     # 150 - 100 + 2
    assert b.get_payment_status(10 + DAY, "a", "payment1") == "CASHBACK_RECEIVED"
    assert b.pay(20 + DAY, "b", 49) == "payment2"  # 49 * 2 // 100 = 0 (floored)
    assert b.top_spenders(21 + DAY, 1) == ["a(150)"]
    # Level 4: merge moves balance, sent total and PENDING cashback
    m = Bank()
    m.create_account(1, "p"); m.create_account(1, "q")
    m.deposit(2, "p", 100); m.deposit(2, "q", 500)
    assert m.pay(3, "q", 100) == "payment1"        # cashback 2 due at 3 + DAY
    assert m.merge_accounts(4, "p", "p") == "false" and m.merge_accounts(4, "p", "zz") == "false"
    assert m.merge_accounts(5, "p", "q") == "true"
    assert m.deposit(6, "p", 0) == "500"           # 100 + 400
    assert m.top_spenders(6, 1) == ["p(100)"]
    assert m.get_payment_status(6, "p", "payment1") == "IN_PROGRESS"
    assert m.get_payment_status(6, "q", "payment1") == ""
    assert m.deposit(7, "q", 1) == ""              # q is gone
    assert m.deposit(3 + DAY, "p", 0) == "502"     # cashback followed the money
    assert m.get_balance(8 + DAY, "q", 2) == "500" and m.get_balance(8 + DAY, "q", 4) == "400"
    assert m.get_balance(8 + DAY, "q", 5) == ""    # merged away at 5
    assert m.get_balance(8 + DAY, "p", 4) == "100" and m.get_balance(8 + DAY, "p", 5) == "500"
    assert m.get_balance(8 + DAY, "p", 3 + DAY) == "502"
    assert m.get_balance(8 + DAY, "p", 0) == ""    # did not exist yet
    assert m.create_account(9 + DAY, "q") == "true"
    assert m.deposit(9 + DAY, "q", 0) == "0"       # a re-created id starts at zero
    assert m.top_spenders(9 + DAY, 2) == ["p(100)", "q(0)"]   # ...and so does its sent total
    assert m.get_balance(9 + DAY, "q", 6) == ""    # it did not exist between merge and re-create
    print("bank: all checks passed")
