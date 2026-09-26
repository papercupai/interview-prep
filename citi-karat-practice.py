"""
Citi · Karat Python interview — PRACTICE FILE (generated from citi-karat-solutions.py; your edits are yours).

Run:  python3 citi-karat-practice.py      every check prints PASS or FAIL with the failing line

Problems 1 and 2: fill every `# implement this` / `pass` region. The docstrings are the spec.
    Target: 35 minutes per problem, all four parts, talking out loud as if someone were listening.
Problem 3: Order and OrderBook below are the "given codebase", and their checks fail.
    Fix the bugs without changing any method signature, then add busiest_hour(). Target: 30 minutes.

Write it from blank regions every time. Citi's email says pasted or source-matching code is flagged,
so the goal is fluency with the patterns, not a memorised answer.
"""
# ==== imports ====
import csv
import heapq
import os
import sys
import tempfile
import traceback
from collections import Counter, defaultdict

# ==== bank ====
class Bank:
    """Problem 1 — customers own accounts; accounts carry transactions.

    Timestamps are "YYYY-MM-DD HH:MM" strings. Amounts are whole dollars:
    positive is a credit, negative is a debit. Unknown ids raise ValueError.
    """

    def __init__(self):
        # implement this
        pass

    # ---- Part 1 ------------------------------------------------------------
    def add_customer(self, customer_id, name, branch):
        """Register a customer. A repeated customer_id raises ValueError."""
        # implement this
        pass

    def open_account(self, account_id, customer_id):
        """Open an account for an existing customer. Unknown customer or repeated account_id raises ValueError."""
        # implement this
        pass

    def record(self, account_id, amount, timestamp, category):
        """Apply one transaction. An unknown account, or a debit that would take the balance
        below zero, raises ValueError and records nothing. Exactly zero is allowed."""
        # implement this
        pass

    def balance(self, account_id):
        """Current balance of one account."""
        # implement this
        pass

    # ---- Part 2 ------------------------------------------------------------
    def customer_balance(self, customer_id):
        """Sum of balances across every account the customer owns; 0 if they own none."""
        # implement this
        pass

    def branch_summary(self):
        """{branch: {"customers": int, "accounts": int, "total_balance": int}} for every branch with a customer."""
        # implement this
        pass

    # ---- Part 3 ------------------------------------------------------------
    def average_amount_by_category(self):
        """{category: mean of abs(amount), rounded to 2 decimals} over recorded transactions."""
        # implement this
        pass

    def busiest_hour(self):
        """Hour of day (0-23) with the most transactions. Ties go to the earliest hour. None if there are none."""
        # implement this
        pass

    # ---- Part 4 ------------------------------------------------------------
    def top_customers(self, k):
        """Names of the k customers who moved the most money (sum of abs(amount)), highest first.
        Ties go to the name that sorts first. Customers with no transactions still rank, at 0."""
        # implement this
        pass

    def most_common_category(self, customer_id):
        """The category this customer uses most often across all their accounts.
        Ties go to the category that sorts first. None if they have no transactions."""
        # implement this
        pass

# ==== tracker ====
class ProjectTracker:
    """Problem 2 — employees log hours against projects. Dates are "YYYY-MM-DD".

    Unknown ids raise ValueError.
    """

    def __init__(self):
        # implement this
        pass

    # ---- Part 1 ------------------------------------------------------------
    def add_employee(self, emp_id, name, department):
        """Register an employee. A repeated emp_id raises ValueError."""
        # implement this
        pass

    def add_project(self, project_id, name):
        """Register a project. A repeated project_id raises ValueError."""
        # implement this
        pass

    def log(self, emp_id, project_id, date, hours):
        """Log hours. Unknown ids, hours <= 0, or pushing that employee's total for that date
        above 24 raises ValueError and logs nothing. Exactly 24 is allowed."""
        # implement this
        pass

    def total_hours(self, emp_id):
        """Total hours this employee has logged; 0 if none."""
        # implement this
        pass

    # ---- Part 2 ------------------------------------------------------------
    def department_hours(self):
        """{department: total hours} for every department that has an employee (0 included)."""
        # implement this
        pass

    def project_average(self, project_id):
        """Average hours per contributing employee (total / distinct employees), rounded to 2 decimals.
        0.0 if nobody has logged on it."""
        # implement this
        pass

    # ---- Part 3 ------------------------------------------------------------
    def busiest_date(self):
        """Date with the most hours logged across everyone. Ties go to the earliest date. None if empty."""
        # implement this
        pass

    def top_contributor(self, project_id):
        """Name of the employee with the most hours on this project. Ties by name A-Z. None if nobody."""
        # implement this
        pass

    # ---- Part 4 ------------------------------------------------------------
    def collaborators(self, emp_id):
        """Names of the other employees who share at least one project with emp_id, ordered by
        number of shared projects (most first), then name A-Z."""
        # implement this
        pass

# ==== orderbook (the given code: fix it) ====
class Order:
    def __init__(self, order_id, customer, amount, placed_at):
        self.order_id = order_id
        self.customer = customer
        self.amount = amount
        self.placed_at = placed_at  # "H:MM" or "HH:MM", 24-hour clock

    def __eq__(self, other):
        return isinstance(other, Order) and self.order_id == other.order_id


class OrderBook:
    """In-memory book of customer orders. A feed can resend an order, so order_id is identity."""

    def __init__(self, orders=[]):
        self.orders = orders

    def add(self, order):
        self.orders.append(order)

    def unique_orders(self):
        """A list of the orders with repeated order_ids removed: first occurrence kept, original order preserved."""
        return set(self.orders)

    def orders_for(self, customer):
        """Every order placed by this customer name."""
        return [o for o in self.orders if o.customer is customer]

    def orders_between(self, start, end):
        """Orders placed at or after start and before end, e.g. orders_between("9:00", "12:00")."""
        return [o for o in self.orders if start <= o.placed_at < end]

    def average_amount(self):
        """Mean order amount; 0.0 for an empty book."""
        return sum(o.amount for o in self.orders) / len(self.orders)

    def top_customer(self):
        """Customer name with the highest total spend; ties go to the name that sorts first; None if empty."""
        best = None
        for customer in [o.customer for o in self.orders]:
            total = sum(o.amount for o in self.orders if o.customer == customer)
            if best is None or total > best[0] or (total == best[0] and customer < best[1]):
                best = (total, customer)
        return best[1]

    @classmethod
    def load(cls, path):
        """Build a book from a CSV file whose header is order_id,amount,placed_at,customer."""
        book = cls()
        f = open(path)
        for line in f.readlines():
            order_id, amount, placed_at, customer = line.split(",")
            book.add(Order(order_id, customer, float(amount), placed_at))
        return book


# ==== tests ====
def _raises(exc_type, fn, *args):
    try:
        fn(*args)
    except exc_type:
        return True
    return False


def _run(label, fn, *args):
    """Run one check; report PASS or FAIL with the failing line, never stop the file."""
    try:
        fn(*args)
    except Exception as exc:  # a practice file full of `pass` raises all sorts; report and keep going
        frame = traceback.extract_tb(exc.__traceback__)[-1]
        detail = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
        print(f"FAIL  {label} — {detail} (line {frame.lineno}: {frame.line})")
        return False
    print(f"PASS  {label}")
    return True


# ---- Problem 1 ---------------------------------------------------------------
def _bank():
    b = Bank()
    b.add_customer("c1", "Ana", "Tampa")
    b.add_customer("c2", "Ben", "Tampa")
    b.add_customer("c3", "Cy", "Irving")
    b.add_customer("c4", "Dee", "Irving")  # never opens an account
    b.open_account("a1", "c1")
    b.open_account("a2", "c1")
    b.open_account("a3", "c2")
    b.open_account("a4", "c3")
    for row in [
        ("a1", 500, "2026-09-14 09:05", "payroll"),
        ("a1", -120, "2026-09-14 09:40", "groceries"),
        ("a2", 300, "2026-09-14 12:10", "transfer"),
        ("a3", 900, "2026-09-14 09:55", "payroll"),
        ("a3", -200, "2026-09-14 12:30", "rent"),
        ("a3", -60, "2026-09-15 12:45", "groceries"),
        ("a4", 50, "2026-09-15 17:00", "transfer"),
        ("a4", -20, "2026-09-15 17:20", "groceries"),
        ("a3", -200, "2026-09-16 08:15", "rent"),
    ]:
        b.record(*row)
    return b


def bank_part1():
    b = _bank()
    assert b.balance("a1") == 380
    assert b.balance("a3") == 440
    assert _raises(ValueError, b.add_customer, "c1", "Ana again", "Tampa")
    assert _raises(ValueError, b.open_account, "a9", "c404")
    assert _raises(ValueError, b.open_account, "a1", "c2")
    assert _raises(ValueError, b.record, "a404", 10, "2026-09-16 10:00", "fees")
    assert _raises(ValueError, b.balance, "a404")
    assert _raises(ValueError, b.record, "a4", -31, "2026-09-16 10:00", "fees")
    assert b.balance("a4") == 30, "a rejected debit must not change the balance"
    b.record("a4", -30, "2026-09-16 10:05", "fees")
    assert b.balance("a4") == 0, "a debit down to exactly zero is allowed"


def bank_part2():
    b = _bank()
    assert b.customer_balance("c1") == 680
    assert b.customer_balance("c2") == 440
    assert b.customer_balance("c4") == 0
    assert _raises(ValueError, b.customer_balance, "c404")
    assert b.branch_summary() == {
        "Tampa": {"customers": 2, "accounts": 3, "total_balance": 1120},
        "Irving": {"customers": 2, "accounts": 1, "total_balance": 30},
    }
    assert Bank().branch_summary() == {}


def bank_part3():
    b = _bank()
    assert b.average_amount_by_category() == {
        "payroll": 700.0, "groceries": 66.67, "transfer": 175.0, "rent": 200.0,
    }
    assert b.busiest_hour() == 9, "hours 9 and 12 both have three; the earlier hour wins"
    empty = Bank()
    assert empty.average_amount_by_category() == {}
    assert empty.busiest_hour() is None
    assert _raises(ValueError, b.record, "a4", -500, "2026-09-16 23:00", "wire")
    assert "wire" not in b.average_amount_by_category(), "a rejected transaction is not recorded"


def bank_part4():
    b = _bank()
    assert b.top_customers(2) == ["Ben", "Ana"]
    assert b.top_customers(10) == ["Ben", "Ana", "Cy", "Dee"]
    assert b.top_customers(0) == []
    assert b.most_common_category("c2") == "rent"
    assert b.most_common_category("c1") == "groceries", "three-way tie at 1: alphabetical"
    assert b.most_common_category("c4") is None
    assert _raises(ValueError, b.most_common_category, "c404")
    tie = Bank()
    for customer_id, name in [("z", "Zed"), ("a", "Amy")]:
        tie.add_customer(customer_id, name, "Tampa")
        tie.open_account(customer_id + "1", customer_id)
        tie.record(customer_id + "1", 100, "2026-09-16 10:00", "payroll")
    assert tie.top_customers(2) == ["Amy", "Zed"], "equal volume: name A-Z"


# ---- Problem 2 ---------------------------------------------------------------
def _tracker():
    t = ProjectTracker()
    t.add_employee("e1", "Ana", "Risk")
    t.add_employee("e2", "Ben", "Risk")
    t.add_employee("e3", "Cy", "Payments")
    t.add_employee("e4", "Dee", "Payments")  # never logs
    t.add_employee("e5", "Eve", "Data")
    t.add_project("p1", "Ledger API")
    t.add_project("p2", "Fraud Model")
    t.add_project("p3", "Statements")
    t.add_project("p4", "Archive")  # nobody logs
    for entry in [
        ("e1", "p1", "2026-09-14", 6.0),
        ("e1", "p2", "2026-09-14", 2.0),
        ("e2", "p1", "2026-09-14", 4.5),
        ("e2", "p2", "2026-09-15", 3.0),
        ("e3", "p1", "2026-09-15", 5.0),
        ("e3", "p3", "2026-09-15", 2.5),
        ("e5", "p2", "2026-09-16", 7.0),
        ("e1", "p3", "2026-09-16", 1.5),
    ]:
        t.log(*entry)
    return t


def tracker_part1():
    t = _tracker()
    assert t.total_hours("e1") == 9.5
    assert t.total_hours("e4") == 0
    assert _raises(ValueError, t.total_hours, "e404")
    assert _raises(ValueError, t.add_employee, "e1", "Ana again", "Risk")
    assert _raises(ValueError, t.add_project, "p1", "Ledger API again")
    assert _raises(ValueError, t.log, "e404", "p1", "2026-09-14", 1.0)
    assert _raises(ValueError, t.log, "e1", "p404", "2026-09-14", 1.0)
    assert _raises(ValueError, t.log, "e1", "p1", "2026-09-14", 0)
    t.log("e1", "p1", "2026-09-14", 16.0)  # 6 + 2 + 16 = exactly 24 on that date
    assert t.total_hours("e1") == 25.5
    assert _raises(ValueError, t.log, "e1", "p2", "2026-09-14", 0.25), "the 24-hour cap spans projects"
    assert t.total_hours("e1") == 25.5, "a rejected entry logs nothing"
    t.log("e1", "p2", "2026-09-15", 0.25)  # the cap is per date
    assert t.total_hours("e1") == 25.75


def tracker_part2():
    t = _tracker()
    assert t.department_hours() == {"Risk": 17.0, "Payments": 7.5, "Data": 7.0}
    assert t.project_average("p1") == 5.17
    assert t.project_average("p2") == 4.0
    assert t.project_average("p3") == 2.0
    assert t.project_average("p4") == 0.0
    assert _raises(ValueError, t.project_average, "p404")
    t.log("e2", "p1", "2026-09-16", 1.5)  # same employee again: still one contributor
    assert t.project_average("p1") == 5.67


def tracker_part3():
    t = _tracker()
    assert t.busiest_date() == "2026-09-14"
    assert t.top_contributor("p1") == "Ana"
    assert t.top_contributor("p2") == "Eve"
    assert t.top_contributor("p4") is None
    assert _raises(ValueError, t.top_contributor, "p404")
    assert ProjectTracker().busiest_date() is None
    tie = ProjectTracker()
    tie.add_employee("z", "Zed", "Risk")
    tie.add_employee("a", "Amy", "Risk")
    tie.add_project("p", "Ledger API")
    tie.log("z", "p", "2026-09-15", 4.0)
    tie.log("a", "p", "2026-09-14", 4.0)
    assert tie.busiest_date() == "2026-09-14", "equal hours: the earlier date wins"
    assert tie.top_contributor("p") == "Amy", "equal hours: name A-Z"


def tracker_part4():
    t = _tracker()
    assert t.collaborators("e1") == ["Ben", "Cy", "Eve"], "Ben and Cy share two projects each, Eve one"
    assert t.collaborators("e5") == ["Ana", "Ben"]
    assert t.collaborators("e4") == []
    assert _raises(ValueError, t.collaborators, "e404")


# ---- Problem 3 ---------------------------------------------------------------
def ob_fresh_books(Order, OrderBook):
    first = OrderBook()
    try:
        first.add(Order("o1", "ann", 10.0, "9:00"))
        assert OrderBook().orders == [], "a brand-new book must start empty"
    finally:
        first.orders.clear()  # keep a shared default list from leaking into later checks


def ob_unique_orders(Order, OrderBook):
    book = OrderBook([])
    for order in [Order("o1", "ann", 10.0, "9:00"), Order("o2", "bo", 5.0, "9:10"), Order("o1", "ann", 10.0, "9:00")]:
        book.add(order)
    result = book.unique_orders()
    assert isinstance(result, list), "the docstring promises a list"
    assert [o.order_id for o in result] == ["o1", "o2"]


def ob_orders_for(Order, OrderBook):
    book = OrderBook([])
    name_from_a_feed = "".join(["an", "na"])  # equal to "anna", but a different object
    book.add(Order("o1", name_from_a_feed, 10.0, "9:00"))
    assert len(book.orders_for("anna")) == 1


def ob_orders_between(Order, OrderBook):
    book = OrderBook([])
    for order_id, placed_at in [("o1", "8:59"), ("o2", "9:30"), ("o3", "11:45"), ("o4", "12:00")]:
        book.add(Order(order_id, "ann", 1.0, placed_at))
    assert [o.order_id for o in book.orders_between("9:00", "12:00")] == ["o2", "o3"]


def ob_average_amount(Order, OrderBook):
    assert OrderBook([]).average_amount() == 0.0
    book = OrderBook([])
    book.add(Order("o1", "ann", 10.0, "9:00"))
    book.add(Order("o2", "bo", 5.0, "9:10"))
    assert book.average_amount() == 7.5


def ob_top_customer(Order, OrderBook):
    assert OrderBook([]).top_customer() is None
    book = OrderBook([])
    for order_id, customer, amount in [("o1", "bo", 15.0), ("o2", "ann", 10.0), ("o3", "cy", 3.0), ("o4", "ann", 5.0)]:
        book.add(Order(order_id, customer, amount, "9:00"))
    assert book.top_customer() == "ann", "ann and bo both total 15.0; ann sorts first"


def ob_load(Order, OrderBook):
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "orders.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("order_id,amount,placed_at,customer\n")
            f.write("L1,12.50,9:05,lena\n")
            f.write("L2,7.25,13:40,omar\n")
            f.write("L3,3.00,9:55,lena\n")
        book = OrderBook.load(path)
        assert [o.order_id for o in book.orders] == ["L1", "L2", "L3"], "the header is not an order"
        assert [o.customer for o in book.orders] == ["lena", "omar", "lena"], "no trailing newline on the last column"
        assert book.orders[0].amount == 12.5


def ob_busiest_hour(Order, OrderBook):
    assert OrderBook([]).busiest_hour() is None
    book = OrderBook([])
    for order_id, placed_at in [("o1", "9:05"), ("o2", "13:40"), ("o3", "9:55"), ("o4", "13:10"), ("o5", "8:00")]:
        book.add(Order(order_id, "ann", 1.0, placed_at))
    assert book.busiest_hour() == 9, "9 and 13 both have two; the earlier hour wins"


ORDERBOOK_CHECKS = [
    ("Problem 3 · bug · fresh books do not share orders", ob_fresh_books),
    ("Problem 3 · bug · resent orders collapse, order kept", ob_unique_orders),
    ("Problem 3 · bug · customer lookup matches by value", ob_orders_for),
    ("Problem 3 · bug · time window compares clock times", ob_orders_between),
    ("Problem 3 · bug · average of an empty book", ob_average_amount),
    ("Problem 3 · bug · top customer: ties and empty book", ob_top_customer),
    ("Problem 3 · bug · load reads the CSV correctly", ob_load),
    ("Problem 3 · part 2 · new busiest_hour method", ob_busiest_hour),
]


def main():
    results = [
        _run("Problem 1 · part 1 · accounts and balances", bank_part1),
        _run("Problem 1 · part 2 · customer and branch totals", bank_part2),
        _run("Problem 1 · part 3 · averages and busiest hour", bank_part3),
        _run("Problem 1 · part 4 · ranking and most common", bank_part4),
        _run("Problem 2 · part 1 · logging with validation", tracker_part1),
        _run("Problem 2 · part 2 · department and project stats", tracker_part2),
        _run("Problem 2 · part 3 · busiest date and top contributor", tracker_part3),
        _run("Problem 2 · part 4 · collaborators", tracker_part4),
    ]
    results += [_run(label, check, Order, OrderBook) for label, check in ORDERBOOK_CHECKS]

    if "ORDERBOOK_GIVEN" in globals():
        # Solutions file only: prove every Problem 3 check really catches a bug in the given code.
        # Each check gets a freshly exec'd copy, so a shared-default bug cannot leak between them.
        missed = []
        for label, check in ORDERBOOK_CHECKS:
            given = {}
            exec(ORDERBOOK_GIVEN, given)
            try:
                check(given["Order"], given["OrderBook"])
            except Exception:
                continue
            missed.append(label)
        if missed:
            print("FAIL  the given Problem 3 code passes checks it should fail: " + "; ".join(missed))
            results.append(False)
        else:
            print(f"PASS  the given Problem 3 code fails all {len(ORDERBOOK_CHECKS)} checks, as intended")

    passed = sum(results)
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
