#!/usr/bin/env python3
"""
Generate the Citi · Karat Python interview prep artifacts from ONE tested source:

  citi-karat-solutions.py        (hand-written, self-testing — must exit 0 first)
        ├─► citi-karat-practice.py            blanked Problem 1-2 skeletons, the buggy Problem 3 code, the same checks
        └─► citi-karat-python-interview.html  the prep page

Every "predict the output" snippet on the page is EXECUTED here, and its captured output must equal the
expectation written beside its explanation — so an explanation can never disagree with what Python prints.

Re-run after any edit:  python3 build-citi-karat-page.py && ./build-standalone.sh
The page's <style> is copied from the Hyundai page (as the Kaseya generator does) so the set stays one system.
"""
import html
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "citi-karat-solutions.py"
PRACTICE = HERE / "citi-karat-practice.py"
PAGE = HERE / "citi-karat-python-interview.html"
STYLE_DONOR = HERE / "hyundai-autoever-applied-ai-hm-call.html"
PREPARED = "16 Sep 2026"

# 1. The solutions must pass before anything is generated from them. ------------------------------
run = subprocess.run([sys.executable, str(SRC)], capture_output=True, text=True)
if run.returncode != 0:
    sys.stderr.write(run.stdout + run.stderr)
    sys.exit("solutions file is red — refusing to generate from it")

src = SRC.read_text(encoding="utf-8")
parts = re.split(r"^# ==== (\w+) ====\n", src, flags=re.M)
preamble, rest = parts[0], parts[1:]
sections = {rest[i]: rest[i + 1].rstrip("\n") + "\n" for i in range(0, len(rest), 2)}
ORDER = ["imports", "bank", "tracker", "orderbook_given", "orderbook", "tests"]
assert list(sections) == ORDER, list(sections)


def strip_markers(code):
    return "\n".join(l for l in code.splitlines() if l.strip() not in ("# >>> implement", "# <<< implement")) + "\n"


def skeletonize(code):
    out, skipping = [], False
    for line in code.splitlines():
        s = line.strip()
        if s == "# >>> implement":
            indent = line[: len(line) - len(line.lstrip())]
            out += [indent + "# implement this", indent + "pass"]
            skipping = True
        elif s == "# <<< implement":
            skipping = False
        elif not skipping:
            out.append(line)
    return "\n".join(out) + "\n"


given_ns = {}
exec(sections["orderbook_given"], given_ns)
GIVEN_CODE = given_ns["ORDERBOOK_GIVEN"].strip("\n") + "\n"

# 2. Practice file. ------------------------------------------------------------------------------
practice = '''"""
Citi · Karat Python interview — PRACTICE FILE (generated from citi-karat-solutions.py; your edits are yours).

Run:  python3 citi-karat-practice.py      every check prints PASS or FAIL with the failing line

Problems 1 and 2: fill every `# implement this` / `pass` region. The docstrings are the spec.
    Target: 35 minutes per problem, all four parts, talking out loud as if someone were listening.
Problem 3: Order and OrderBook below are the "given codebase", and their checks fail.
    Fix the bugs without changing any method signature, then add busiest_hour(). Target: 30 minutes.

Write it from blank regions every time. Citi's email says pasted or source-matching code is flagged,
so the goal is fluency with the patterns, not a memorised answer.
"""
'''
practice += "# ==== imports ====\n" + sections["imports"] + "\n"
practice += "# ==== bank ====\n" + skeletonize(sections["bank"]) + "\n"
practice += "# ==== tracker ====\n" + skeletonize(sections["tracker"]) + "\n"
practice += "# ==== orderbook (the given code: fix it) ====\n" + GIVEN_CODE + "\n\n"
practice += "# ==== tests ====\n" + sections["tests"]
PRACTICE.write_text(practice, encoding="utf-8")

blank = subprocess.run([sys.executable, str(PRACTICE)], capture_output=True, text=True)
if blank.returncode == 0 or re.search(r"^PASS", blank.stdout, flags=re.M) or "Traceback" in blank.stderr:
    sys.stderr.write(blank.stdout + blank.stderr)
    sys.exit("practice file must run cleanly and fail every check before any work is done")


# 3. Knowledge snippets: run each one and insist the output matches what the explanation assumes. ---
# A second, older interpreter (Karat's editor version is unknown) re-runs everything; differences are shown on the card.
ALT_PYTHON = shutil.which("python3.12")
if ALT_PYTHON and subprocess.run([ALT_PYTHON, str(SRC)], capture_output=True).returncode != 0:
    sys.exit(f"solutions file is red on {ALT_PYTHON}")


def python_version(executable):
    return subprocess.run([executable, "-c", "import platform; print(platform.python_version())"],
                          capture_output=True, text=True).stdout.strip()


def run_snippet(code, executable=sys.executable):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    with tempfile.TemporaryDirectory() as folder:
        Path(folder, "snippet.py").write_text(code, encoding="utf-8")
        proc = subprocess.run([executable, "snippet.py"], cwd=folder, capture_output=True, text=True, env=env, timeout=30)
    lines = []
    for line in proc.stderr.splitlines():
        warning = re.match(r"^\S*snippet\.py:\d+: (\w*Warning: .*)$", line)
        if warning:
            lines.append(warning.group(1))
    lines += proc.stdout.rstrip("\n").splitlines()
    if proc.returncode != 0:
        final = [l for l in proc.stderr.splitlines() if l and not l.startswith((" ", "Traceback"))]
        lines += ["Traceback (most recent call last): …", final[-1]]
    return "\n".join(lines)


def S(sid, title, code, out, why, fix=None, fix_out=None):
    return dict(sid=sid, title=title, code=code.strip("\n") + "\n", out=out.strip("\n"), why=why,
                fix=fix.strip("\n") + "\n" if fix else None, fix_out=fix_out.strip("\n") if fix_out else None)


DEFAULTS = [
    S("d1", "A list as a default", '''
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags

print(add_tag("urgent"))
print(add_tag("billing"))
print(add_tag("vip", []))
print(add_tag("late"))
''', '''
['urgent']
['urgent', 'billing']
['vip']
['urgent', 'billing', 'late']
''', "A default is evaluated once, when the <code>def</code> statement runs, and stored on the function in <code>add_tag.__defaults__</code>. Every call that omits <code>tags</code> gets that same list object, so the appends pile up. Passing a list explicitly bypasses the shared one, which is why the <code>\"vip\"</code> call looks correct and hides the bug.",
      '''
def add_tag(tag, tags=None):
    if tags is None:
        tags = []
    tags.append(tag)
    return tags

print(add_tag("urgent"))
print(add_tag("billing"))
''', '''
['urgent']
['billing']
'''),
    S("d2", "A generated id as a default", '''
import itertools

ids = itertools.count(1)

def new_ticket(title, ticket_id=next(ids)):
    return ticket_id, title

print(new_ticket("login fails"))
print(new_ticket("card declined"))
''', '''
(1, 'login fails')
(1, 'card declined')
''', "<code>next(ids)</code> ran exactly once, when the function was defined. The same trap freezes <code>datetime.now()</code>, <code>time.time()</code> and <code>uuid4()</code> in a default: every record gets the moment the module was imported. Anything that must be fresh per call belongs in the body.",
      '''
import itertools

ids = itertools.count(1)

def new_ticket(title, ticket_id=None):
    if ticket_id is None:
        ticket_id = next(ids)
    return ticket_id, title

print(new_ticket("login fails"))
print(new_ticket("card declined"))
''', '''
(1, 'login fails')
(2, 'card declined')
'''),
    S("d3", "A default that reads a global", '''
rate = 0.05

def interest(amount, r=rate):
    return amount * r

rate = 0.10
print(interest(100))
''', "5.0", "The default captured the <em>value</em> <code>rate</code> had when <code>def</code> ran, not the variable. Rebinding the global later cannot reach it. If the current value is what you want, read it inside the body or pass it explicitly."),
    S("d4", "The same bug inside __init__", '''
class Account:
    def __init__(self, owner, history=[]):
        self.owner = owner
        self.history = history

ann = Account("ann")
bob = Account("bob")
ann.history.append("deposit 100")
print(bob.history)
print(ann.history is bob.history)
print(Account.__init__.__defaults__)
''', '''
['deposit 100']
True
(['deposit 100'],)
''', "This is the shape it takes in an interview class. Both accounts hold the one list created with <code>__init__</code>, which is visible in <code>__defaults__</code>. The fix also copies a caller's list, so a caller who keeps mutating their own list cannot change the account afterwards.",
      '''
class Account:
    def __init__(self, owner, history=None):
        self.owner = owner
        self.history = [] if history is None else list(history)

ann = Account("ann")
bob = Account("bob")
ann.history.append("deposit 100")
print(bob.history)
''', "[]"),
    S("d5", "Late binding, and the default-argument trick", '''
handlers = [lambda: n for n in range(3)]
print([h() for h in handlers])

handlers = [lambda n=n: n for n in range(3)]
print([h() for h in handlers])
''', '''
[2, 2, 2]
[0, 1, 2]
''', "The opposite timing. A closure looks <code>n</code> up when it is <em>called</em>, after the loop has finished, so all three see 2. A default is evaluated when each lambda is <em>created</em>, so <code>n=n</code> freezes each value. <code>functools.partial</code> says the same thing more readably."),
    S("d6", "What dataclasses do about it", '''
from dataclasses import dataclass

@dataclass
class Team:
    name: str
    members: list = []
''', "Traceback (most recent call last): …\nValueError: mutable default <class 'list'> for field members is not allowed: use default_factory",
      "dataclasses refuse the trap when the class is defined, because a list default would be shared by every instance. Since Python 3.11 the check rejects any unhashable default, not only list, dict and set. <code>field(default_factory=list)</code> calls <code>list()</code> once per instance.",
      '''
from dataclasses import dataclass, field

@dataclass
class Team:
    name: str
    members: list = field(default_factory=list)

print(Team("risk").members is Team("payments").members)
''', "False"),
]

IDENTITY = [
    S("i1", "Equal, identical, aliased", '''
a = [1, 2, 3]
b = [1, 2, 3]
c = a
print(a == b, a is b, a is c)
c.append(4)
print(a, b)
''', '''
True False True
[1, 2, 3, 4] [1, 2, 3]
''', "<code>==</code> asks whether the values are equal. <code>is</code> asks whether both names refer to the same object. <code>c = a</code> copies the reference, not the list, so appending through <code>c</code> changes <code>a</code>. <code>b</code> is a separate list that happens to hold equal values."),
    S("i2", "Integers that are sometimes identical", '''
x, y = int("256"), int("256")
print(x == y, x is y)
x, y = int("257"), int("257")
print(x == y, x is y)
''', '''
True True
True False
''', "CPython pre-creates the integers from −5 to 256 and hands out the same objects, so <code>is</code> happens to be True up to 256 and False one step later. That is an implementation detail. Literals in one file can even be merged into a single constant, which is why this example builds the numbers at run time. The rule is simple: never use <code>is</code> to compare numbers or strings."),
    S("i3", "is against a string literal", '''
region = "".join(["NA", "M"])
print(region == "NAM")
print(region is "NAM")
''', '''
SyntaxWarning: "is" with 'str' literal. Did you mean "=="?
True
False
''', "Python flags this itself: <code>is</code> against a literal raises a SyntaxWarning when the file is compiled, and the wording varies by version. A string assembled at run time, from a join, a file or a request body, is a different object from the literal even when the text is equal. This is the bug in Problem 3's <code>orders_for</code>."),
    S("i4", "A class with no __eq__", '''
class Trade:
    def __init__(self, symbol, qty):
        self.symbol, self.qty = symbol, qty

print(Trade("C", 100) == Trade("C", 100))
print(Trade("C", 100) in [Trade("C", 100)])
''', '''
False
False
''', "Without <code>__eq__</code> a class inherits <code>object.__eq__</code>, which is identity. List membership uses <code>==</code> per element, so it fails too, and so do <code>list.remove</code>, <code>list.index</code> and <code>list.count</code>. A frozen dataclass generates <code>__eq__</code> and a matching <code>__hash__</code> from the fields.",
      '''
from dataclasses import dataclass

@dataclass(frozen=True)
class Trade:
    symbol: str
    qty: int

print(Trade("C", 100) == Trade("C", 100))
print(len({Trade("C", 100), Trade("C", 100)}))
''', '''
True
1
'''),
    S("i5", "__eq__ without __hash__", '''
class Customer:
    def __init__(self, cid):
        self.cid = cid

    def __eq__(self, other):
        return isinstance(other, Customer) and self.cid == other.cid

print(Customer(7) == Customer(7))
print(Customer.__hash__)
print(len({Customer(7), Customer(7)}))
''', "True\nNone\nTraceback (most recent call last): …\nTypeError: cannot use 'Customer' as a set element (unhashable type: 'Customer')",
      "Defining <code>__eq__</code> without <code>__hash__</code> sets <code>__hash__</code> to None, so instances can no longer go in a set or be dict keys. The contract: objects that compare equal must hash equal, and a hash must not change while the object sits in a set. So hash exactly the immutable fields that <code>__eq__</code> compares. Older Pythons word the error as <code>unhashable type: 'Customer'</code>.",
      '''
class Customer:
    def __init__(self, cid):
        self.cid = cid

    def __eq__(self, other):
        return isinstance(other, Customer) and self.cid == other.cid

    def __hash__(self):
        return hash(self.cid)

print(len({Customer(7), Customer(7)}))
''', "1"),
    S("i6", "NaN inside a list", '''
nan = float("nan")
print(nan == nan)
print(nan in [nan])
print([nan] == [nan])
''', '''
False
True
True
''', "NaN is not equal to itself, yet <code>nan in [nan]</code> is True. Containers check identity first and only then call <code>==</code>, so the very same object always matches. It is a compact proof that membership means <code>x is y or x == y</code>."),
    S("i7", "A grid built with *", '''
grid = [[0] * 3] * 3
grid[0][0] = 1
print(grid)
''', "[[1, 0, 0], [1, 0, 0], [1, 0, 0]]",
      "Multiplying a list copies references. The outer list holds three references to one inner list, so a single assignment shows up in every row. The inner <code>[0] * 3</code> is fine because integers are immutable. Build a new inner list per row.",
      '''
grid = [[0] * 3 for _ in range(3)]
grid[0][0] = 1
print(grid)
''', "[[1, 0, 0], [0, 0, 0], [0, 0, 0]]"),
    S("i8", "Shallow and deep copies", '''
import copy

original = {"branch": "Tampa", "ids": [1, 2]}
shallow = copy.copy(original)
deep = copy.deepcopy(original)
original["ids"].append(3)
original["branch"] = "Irving"
print(shallow)
print(deep)
''', '''
{'branch': 'Tampa', 'ids': [1, 2, 3]}
{'branch': 'Tampa', 'ids': [1, 2]}
''', "<code>copy.copy</code> makes a new outer dict whose values are the same objects, so the shared <code>ids</code> list shows the append. Assigning <code>original[\"branch\"]</code> rebinds a key in the original only, so neither copy sees Irving. <code>deepcopy</code> copies the nested list as well."),
    S("i9", "== None versus is None", '''
class AlwaysEqual:
    def __eq__(self, other):
        return True

value = AlwaysEqual()
print(value == None)
print(value is None)
''', '''
True
False
''', "<code>==</code> calls a method the class controls, so it can claim anything. <code>is None</code> cannot be overridden, is faster, and is what PEP 8 asks for with singletons. Use <code>is</code> for None, sentinel objects and enum members, and <code>==</code> for everything else."),
]

FILES = [
    S("f1", "Summing a generator twice", '''
squares = (n * n for n in range(4))
print(sum(squares))
print(sum(squares))
''', '''
14
0
''', "A generator is a one-shot iterator. The first <code>sum</code> consumes it, and the second finds it exhausted and adds nothing, silently. If you need two passes, build a list, or compute both results in a single pass."),
    S("f2", "Looping over a file twice", '''
from pathlib import Path

Path("trades.txt").write_text("C,100\\nJPM,50\\nGS,75\\n", encoding="utf-8")

with open("trades.txt", encoding="utf-8") as f:
    first = sum(1 for _ in f)
    second = sum(1 for _ in f)
print(first, second)
''', "3 0", "A file object is an iterator with a position. After the first loop it sits at end-of-file, so the second loop reads nothing. <code>f.seek(0)</code> rewinds it, but the better answer is to compute everything you need in one pass over the file."),
    S("f3", "A lazy generator outliving its with block", '''
from pathlib import Path

Path("trades.txt").write_text("C,100\\nJPM,50\\n", encoding="utf-8")

with open("trades.txt", encoding="utf-8") as f:
    rows = (line.rstrip("\\n").split(",") for line in f)
print(list(rows))
''', "Traceback (most recent call last): …\nValueError: I/O operation on closed file.",
      "The generator expression is lazy: no line is read until <code>list()</code> pulls from it, and by then the <code>with</code> block has closed the file. Either consume the data inside the block, or move the <code>with</code> into a generator function so the file stays open exactly as long as someone is iterating.",
      '''
from pathlib import Path

Path("trades.txt").write_text("C,100\\nJPM,50\\n", encoding="utf-8")

def read_rows(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\\n").split(",")

print(list(read_rows("trades.txt")))
''', "[['C', '100'], ['JPM', '50']]"),
    S("f4", "Removing while iterating", '''
amounts = [120, -40, -15, 60, -5]
for amount in amounts:
    if amount < 0:
        amounts.remove(amount)
print(amounts)
''', "[120, -15, 60]", "Removing an item shifts everything after it one place left, while the loop's hidden index keeps moving forward. So the element right after each removal is never examined, and −15 survives. Build a new list instead.",
      '''
amounts = [120, -40, -15, 60, -5]
amounts = [amount for amount in amounts if amount >= 0]
print(amounts)
''', "[120, 60]"),
    S("f5", "Ranking CSV values", '''
import csv
import io

feed = io.StringIO("account,amount\\nA1,95\\nA2,120\\nA3,80\\n")
rows = list(csv.DictReader(feed))
print(max(rows, key=lambda r: r["amount"])["account"])
print(max(rows, key=lambda r: float(r["amount"]))["account"])
''', '''
A1
A2
''', "The <code>csv</code> module gives you strings, and strings compare character by character, so <code>\"95\" &gt; \"80\" &gt; \"120\"</code>. Convert at the boundary, once, when you read each row, so nothing downstream ever compares the text. Clock times such as <code>\"9:30\"</code> and <code>\"12:00\"</code> fail the same way."),
    S("f6", "groupby on unsorted data", '''
from itertools import groupby

branches = ["Tampa", "Irving", "Tampa", "Tampa"]
print([(name, len(list(group))) for name, group in groupby(branches)])
''', "[('Tampa', 1), ('Irving', 1), ('Tampa', 2)]",
      "<code>groupby</code> only groups <em>consecutive</em> equal items. It is a streaming tool that expects input already sorted by the key, which costs O(n log n). To count or group unsorted data, use a <code>Counter</code> or a <code>defaultdict(list)</code> in one O(n) pass.",
      '''
from collections import Counter

branches = ["Tampa", "Irving", "Tampa", "Tampa"]
print(Counter(branches))
''', "Counter({'Tampa': 3, 'Irving': 1})"),
    S("f7", "most_common with a tie", '''
from collections import Counter

visits = Counter(["Tampa", "Irving", "Irving", "Tampa", "Dallas"])
print(visits.most_common(1))
print(min(visits, key=lambda branch: (-visits[branch], branch)))
''', '''
[('Tampa', 2)]
Irving
''', "<code>most_common</code> orders equal counts by first insertion, not alphabetically, so it answers Tampa. When the problem says ties go to the name that sorts first, put the rule in the key and minimise <code>(-count, name)</code>. That one line handles every “most frequent, ties by X” part in the problems below."),
    S("f8", "Correct, and still a code-review comment", '''
from pathlib import Path

Path("app.log").write_text("INFO start\\nERROR db timeout\\nINFO retry\\nERROR db timeout\\n", encoding="utf-8")

def count_errors(path):
    f = open(path)
    lines = f.readlines()
    count = 0
    for i in range(len(lines)):
        if "ERROR" in lines[i]:
            count = count + 1
    return count

print(count_errors("app.log"))
''', "2", "It prints the right answer, and it would still get pushback on a 40 GB log. <code>readlines()</code> loads the whole file into memory. The file is not closed deterministically, and never if an exception interrupts. The encoding depends on the machine. <code>range(len(...))</code> indexing is noise. Iterating the file object streams one line at a time, so memory stays flat however large the log is.",
      '''
from pathlib import Path

Path("app.log").write_text("INFO start\\nERROR db timeout\\nINFO retry\\nERROR db timeout\\n", encoding="utf-8")

def count_errors(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if "ERROR" in line)

print(count_errors("app.log"))
''', "2"),
    S("f9", "zip with inputs of different lengths", '''
names = ["Ana", "Ben", "Cy"]
balances = [380, 440]
print(list(zip(names, balances)))
print(list(zip(names, balances, strict=True)))
''', "[('Ana', 380), ('Ben', 440)]\nTraceback (most recent call last): …\nValueError: zip() argument 2 is shorter than argument 1",
      "<code>zip</code> stops at the shortest input without a word, so Cy silently disappears. <code>strict=True</code>, added in Python 3.10, raises instead. Use it whenever the inputs are supposed to line up."),
]

mismatches = []
for snippet in DEFAULTS + IDENTITY + FILES:
    for code_key, out_key in (("code", "out"), ("fix", "fix_out")):
        if snippet[code_key] is None:
            continue
        actual = run_snippet(snippet[code_key])
        if actual != snippet[out_key]:
            mismatches.append(f"--- {snippet['sid']} {code_key}\nexpected:\n{snippet[out_key]}\nactual:\n{actual}")
        if ALT_PYTHON:
            alt = run_snippet(snippet[code_key], ALT_PYTHON)
            snippet[out_key + "_alt"] = alt if alt != actual else None
if mismatches:
    sys.exit("snippet outputs disagree with their explanations:\n" + "\n".join(mismatches))


# 4. Page pieces. --------------------------------------------------------------------------------
def esc(s):
    return html.escape(s, quote=False)


def code_block(code, label=None, extra=""):
    lab = f'<p class="eyebrow">{esc(label)}</p>' if label else ""
    return f'{lab}<pre class="code{extra}"><code>{esc(code.rstrip())}</code></pre>'


ALT_VERSION = python_version(ALT_PYTHON) if ALT_PYTHON else None
PRIMARY_VERSION = platform.python_version()


def version_note(s, key):
    if not s.get(key + "_alt"):
        return ""
    return code_block(s[key + "_alt"], f"Python {ALT_VERSION} prints this instead", " out")


def predict_cards(snippets, topic):
    out = ['<div class="predict-grid">']
    for s in snippets:
        fix = ""
        if s["fix"]:
            fix = code_block(s["fix"], "The fix") + code_block(s["fix_out"], "Which prints", " out") + version_note(s, "fix_out")
        out.append(
            f'<article class="predict" id="{s["sid"]}">'
            f'<p class="eyebrow">{esc(topic)} · predict the output</p><h4>{esc(s["title"])}</h4>'
            f'{code_block(s["code"])}'
            f'<details class="solution"><summary>Output and why — say yours first</summary><div class="reveal">'
            f'{code_block(s["out"], f"Python {PRIMARY_VERSION} prints", " out")}{version_note(s, "out")}'
            f'<p>{s["why"]}</p>{fix}</div></details>'
            "</article>"
        )
    out.append("</div>")
    return "\n".join(out)


CARDS = [
    ("Defaults", "Why does Python evaluate a default only once, and when is that useful?",
     "<ul><li><code>def</code> is an executable statement that builds a function object. Default expressions are evaluated at that moment and stored in <code>__defaults__</code> and <code>__kwdefaults__</code>.</li><li>It is cheap, since nothing is re-evaluated per call, and it is predictable: the default is whatever existed at definition time.</li><li>Deliberate uses: a memo dict such as <code>def fib(n, _memo={})</code>, or freezing a loop variable with <code>lambda n=n: n</code>. <code>functools.lru_cache</code> and <code>functools.partial</code> express both more clearly, so say that too.</li></ul>"),
    ("Defaults", "The standard fix uses None. What if None is a valid argument?",
     "<ul><li>Use a private sentinel: <code>_MISSING = object()</code>, then <code>def f(x=_MISSING)</code> and <code>if x is _MISSING:</code>.</li><li>A fresh <code>object()</code> is identical only to itself, so no caller value can collide with it. This is one of the legitimate uses of <code>is</code>.</li><li>Making the parameter keyword-only with <code>*</code> also keeps call sites explicit.</li></ul>"),
    ("Identity", "When is is the right comparison?",
     "<ul><li>Singletons: <code>None</code>, and <code>True</code>/<code>False</code> when you must distinguish them from 1 and 0.</li><li>Sentinel objects, and enum members, where <code>is</code> and <code>==</code> agree.</li><li>Asking whether two names alias the same mutable object, for example to avoid copying onto itself or to detect a cycle.</li><li>Never for numbers, strings or tuples: their identity is an interpreter detail that changes with how the value was produced.</li></ul>"),
    ("Identity", "What is the contract between __eq__ and __hash__, and how do dataclasses handle it?",
     "<ul><li>If <code>a == b</code> then <code>hash(a) == hash(b)</code>. The hash must also stay stable while the object is in a set or used as a dict key.</li><li>Defining <code>__eq__</code> sets <code>__hash__</code> to None, so the class becomes unhashable until you add one. Hash exactly the immutable fields <code>__eq__</code> compares.</li><li><code>@dataclass</code> has <code>eq=True</code> by default, which leaves instances unhashable. <code>frozen=True</code> generates a field-based hash. <code>unsafe_hash=True</code> forces one on a mutable class, and mutating a hashed field then makes the object unfindable in its set.</li></ul>"),
    ("Identity", "A function changed the list its caller passed in. Explain what happened.",
     "<ul><li>Python passes references to objects, sometimes called call by sharing. Rebinding the parameter name inside the function does not affect the caller. Mutating the object does, because both names refer to it.</li><li>Defend at the boundary: copy on the way in with <code>list(x)</code> or <code>dict(x)</code>, <code>copy.deepcopy</code> for nesting, or return new objects instead of mutating.</li><li>Tuples and frozen dataclasses make data that should not change impossible to change.</li></ul>"),
    ("Files", "How would you total amounts per account from a 50 GB CSV on a laptop?",
     "<ul><li>Stream it: <code>with open(path, newline=\"\", encoding=\"utf-8\") as f</code>, then <code>for row in csv.DictReader(f)</code>, accumulating into a dict keyed by account.</li><li>Memory is then proportional to the number of distinct accounts, not the size of the file. Parse types once per row, and collect malformed rows with their line numbers instead of crashing on row 400 million.</li><li>If even the distinct keys do not fit: partition rows into files by a hash of the key and aggregate each file, or sort externally. Parallelise over byte ranges if the parsing is CPU-bound.</li><li>Then mention the tools you would really reach for at scale, such as chunked pandas or a SQL engine, after showing you can write the streaming version.</li></ul>"),
    ("Files", "What does with guarantee, and how do you write your own context manager?",
     "<ul><li><code>with</code> calls <code>__enter__</code>, and always calls <code>__exit__</code> on the way out: normal exit, exception, <code>return</code> or <code>break</code>. Files close and locks release deterministically.</li><li>If <code>__exit__</code> returns True, the exception is suppressed, which is rarely what you want.</li><li>Write one as a class with those two methods, or with <code>@contextlib.contextmanager</code> and a <code>try</code>/<code>finally</code> around a single <code>yield</code>. For a variable number of resources, use <code>contextlib.ExitStack</code>.</li></ul>"),
    ("Files", "Why pass encoding=, and why newline=\"\" for CSV files?",
     "<ul><li>Without <code>encoding</code>, text mode uses the platform's locale encoding, such as cp1252 on many Windows machines. Code that works on a laptop then fails on a server. PEP 686 makes UTF-8 mode the default in Python 3.15, but explicit is still correct.</li><li>The <code>csv</code> documentation requires <code>newline=\"\"</code>, so that the csv module, not the file layer, handles <code>\\r\\n</code> endings and newlines inside quoted fields.</li><li>Use binary mode (<code>\"rb\"</code>) for data that is not text, and no encoding at all there.</li></ul>"),
    ("Files", "How do you write a file so that a crash cannot leave it half-written?",
     "<ul><li>Write to a temporary file in the same directory, <code>flush()</code> and <code>os.fsync()</code> it, then <code>os.replace(tmp, final)</code>.</li><li>The rename is atomic on POSIX and Windows, so readers see the old file or the new one, never a partial one.</li><li>Same directory matters: a rename across filesystems is a copy, which is not atomic.</li></ul>"),
    ("Iteration", "List, iterator, generator: what is the difference, and when do you pick each?",
     "<ul><li>A list holds every item: reusable, indexable, has a length, costs O(n) memory.</li><li>An iterator yields items one at a time through <code>__next__</code> and remembers its position; it is single-pass.</li><li>A generator, from a function with <code>yield</code> or a generator expression, is a lazy iterator: O(1) memory, ideal for pipelines over large input and for early exit with <code>any</code>, <code>next</code> or <code>itertools.islice</code>.</li><li>Pick a list when you need several passes, random access or <code>len</code>; pick a generator when you stream.</li></ul>"),
    ("Complexity", "Quote the costs of the operations you will lean on in the coding round.",
     "<ul><li>List: append O(1) amortised; <code>x in list</code> O(n); <code>pop(0)</code> and <code>insert(0, x)</code> O(n), so use <code>collections.deque</code> for queues.</li><li>Dict and set: get, set and <code>in</code> are O(1) on average.</li><li><code>sorted</code> is O(n log n) and stable. <code>heapq.nsmallest(k, xs)</code> is about O(n log k). <code>min</code>, <code>max</code>, <code>sum</code> and <code>Counter(xs)</code> are O(n).</li><li>String <code>+=</code> in a loop can go quadratic, so collect parts and <code>\"\".join</code> them. Slicing copies, O(k).</li></ul>"),
    ("Ranking", "Sort by count descending, then name ascending. And what if both keys are strings?",
     "<ul><li>With a numeric primary key, negate it: <code>sorted(rows, key=lambda r: (-r.count, r.name))</code>.</li><li>A string cannot be negated. Use stability instead: sort by the secondary key first, then by the primary key with <code>reverse=True</code>. Equal primary keys keep their secondary order.</li><li>For the single best item, <code>min</code> with the same key is O(n) instead of O(n log n).</li></ul>"),
    ("Money", "Why not float for money, and what would you use at a bank?",
     "<ul><li>Binary floats cannot represent most decimal fractions: <code>0.1 + 0.2 != 0.3</code>, and the errors accumulate in totals.</li><li>Use <code>decimal.Decimal</code> built from strings, <code>Decimal(\"0.10\")</code>, never <code>Decimal(0.1)</code>, with explicit rounding through <code>quantize</code>. Or store integer minor units such as cents.</li><li>If an exercise hands you floats, follow the spec, and say this out loud: it is a cheap signal that you think like someone who would handle ledgers.</li></ul>"),
    ("The role, beyond the email", "What happens if you call a blocking function inside async def?",
     "<ul><li>It blocks the event loop. Every other coroutine on that loop, including every other request a FastAPI worker is serving, stalls until the call returns.</li><li>Use the async equivalent, such as <code>await asyncio.sleep</code> or an async HTTP client. For unavoidable blocking or CPU-bound work, use <code>await asyncio.to_thread(fn, ...)</code> or a process pool.</li><li>In FastAPI, a plain <code>def</code> endpoint runs in a threadpool, so blocking code there does not freeze the loop. <code>async def</code> is only faster when everything awaited is truly non-blocking.</li></ul>"),
    ("The role, beyond the email", "Call three LLM tools concurrently with a deadline, and tolerate one failing.",
     "<ul><li><code>asyncio.gather(*calls, return_exceptions=True)</code> returns every result or exception, so one failure does not discard the others. Wrap it in <code>asyncio.timeout(...)</code> (Python 3.11+) or <code>asyncio.wait_for</code>.</li><li><code>asyncio.TaskGroup</code> (3.11+) cancels the siblings when one task fails. Choose it when a partial answer is worthless.</li><li>Bound fan-out with an <code>asyncio.Semaphore</code>, and retry 429 and 5xx responses with exponential backoff plus jitter, under an overall budget.</li></ul>"),
]


def flash_cards():
    out = ['<div class="flash-grid">']
    for topic, q, a in CARDS:
        out.append(f'<details class="flash"><summary data-topic="{esc(topic)}">{esc(q)}</summary><div class="answer">{a}</div></details>')
    out.append("</div>")
    return "\n".join(out)


def fixture(name):
    match = re.search(rf"^def {name}\(\):\n(?:    .*\n|\n)+?    return \w+\n", sections["tests"], flags=re.M)
    assert match, name
    return match.group(0)


def solution_pair(section, minutes):
    return (
        f'<details class="solution"><summary>Skeleton — what the practice file gives you · target {minutes}</summary>'
        f'{code_block(skeletonize(sections[section]))}</details>'
        '<details class="solution"><summary>Reference solution — open only after your timed attempt</summary>'
        f'{code_block(strip_markers(sections[section]))}</details>'
    )


donor = STYLE_DONOR.read_text(encoding="utf-8")
style = donor[donor.index('<link rel="preconnect"'): donor.index("</style>") + len("</style>")]
extra_css = """
<style>
  pre.code {
    margin: 0;
    padding: 0.85rem 1rem;
    background: var(--surface-alt);
    border: 1px solid var(--rule);
    border-radius: 3px;
    overflow-x: auto;
    font-family: var(--f-mono);
    font-size: 0.78rem;
    line-height: 1.5;
    tab-size: 4;
  }
  pre.code code { background: transparent; padding: 0; font-size: inherit; }
  pre.code.out { background: var(--ground); border-style: dashed; }
  details.solution { border: 1px solid var(--rule); border-radius: 3px; background: var(--surface); min-width: 0; }
  details.solution summary { padding: 0.65rem 0.9rem; cursor: pointer; font-family: var(--f-display); font-weight: 650; font-size: 0.88rem; background: var(--caution-soft); color: var(--caution); }
  details.solution[open] summary { border-bottom: 1px solid var(--rule); }
  details.solution > pre.code { border: 0; border-radius: 0 0 3px 3px; }
  details.solution .reveal { padding: 0.8rem 0.9rem 0.9rem; display: flex; flex-direction: column; gap: 0.55rem; font-size: 0.94rem; }
  .predict-grid, .flash-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8rem; }
  .predict { min-width: 0; padding: 0.9rem 1rem; background: var(--surface); border: 1px solid var(--rule); border-radius: 3px; display: flex; flex-direction: column; gap: 0.55rem; }
  .predict h4, .topic-head h3 { margin: 0; }
  .topic-head { display: flex; flex-direction: column; gap: 0.3rem; margin-top: 0.6rem; }
  .topic-head .rule { color: var(--ink-muted); font-size: 0.98rem; }
  details.flash { background: var(--surface); border: 1px solid var(--rule); border-radius: 3px; overflow: hidden; }
  details.flash summary { padding: 0.75rem 0.95rem; cursor: pointer; font-family: var(--f-display); font-weight: 650; font-size: 0.93rem; line-height: 1.35; }
  details.flash summary::before { content: attr(data-topic); display: block; margin-bottom: 0.2rem; color: var(--accent); font: 600 0.62rem var(--f-mono); letter-spacing: 0.1em; text-transform: uppercase; }
  details.flash[open] summary { border-bottom: 1px solid var(--rule); background: var(--surface-alt); }
  details.flash .answer { padding: 0.8rem 0.95rem 0.95rem; font-size: 0.93rem; }
  details.flash .answer ul { margin: 0; padding-left: 1.1rem; }
  details.flash .answer li { margin: 0.3rem 0; }
  .drill-body.single { grid-template-columns: 1fr; }
  .spec { margin: 0; padding-left: 1.15rem; }
  .spec li { margin: 0.4rem 0; }
  table.matrix.compact { min-width: 36rem; }
  table.matrix.compact td:nth-child(3) { width: auto; }
  table.matrix code { font-size: 0.82em; overflow-wrap: anywhere; }
  .stack-lg { display: flex; flex-direction: column; gap: 0.9rem; }
  /* grid and flex children default to min-width:auto, which lets a long code line widen the page on a phone */
  section > *, .two-col > *, .card, .stack, .drill-body > *, details.solution .reveal > * { min-width: 0; }
  pre.code { max-width: 100%; }
  /* the donor's facts-strip rule `.fact` also matches `.badge.fact`, stretching those badges to 5.4rem */
  .badge.fact { min-height: 0; padding: 0.13rem 0.42rem; border: 0; display: inline-block; }
  /* the shared sticky menu wraps to three rows at desktop widths; land jump targets below it */
  html { scroll-padding-top: 8rem; }
  section, .topic-head { scroll-margin-top: 1rem; }
  @media (max-width: 48rem) { .predict-grid, .flash-grid { grid-template-columns: 1fr; } }
  @media print { details.solution > *, details.flash > * { display: block; } }
</style>
"""

BANK_PARTS = """
<details class="drill" open>
  <summary>Part 1 · Accounts and balances</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>add_customer(customer_id, name, branch)</code>. A repeated customer id raises <code>ValueError</code>.</li>
      <li><code>open_account(account_id, customer_id)</code>. The customer must exist and account ids are unique, otherwise <code>ValueError</code>.</li>
      <li><code>record(account_id, amount, timestamp, category)</code>. Positive is a credit, negative a debit. An unknown account, or a debit that would take the balance below zero, raises <code>ValueError</code> and records nothing. Exactly zero is allowed.</li>
      <li><code>balance(account_id)</code> returns the current balance. An unknown account raises <code>ValueError</code>.</li>
    </ul>
    <p class="probe">Ask before coding: are amounts whole numbers? Is an overdraft rejected or allowed? Do unknown ids raise or return a default? Is the timestamp format guaranteed?</p>
  </div></div>
</details>
<details class="drill">
  <summary>Part 2 · Customer and branch totals — open once Part 1 passes</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>customer_balance(customer_id)</code> sums the balances of every account the customer owns. A customer with no accounts has 0. An unknown customer raises <code>ValueError</code>.</li>
      <li><code>branch_summary()</code> returns <code>{branch: {"customers", "accounts", "total_balance"}}</code> for every branch that has a customer, counting customers who have no accounts.</li>
    </ul>
  </div></div>
</details>
<details class="drill">
  <summary>Part 3 · Averages and the busiest hour</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>average_amount_by_category()</code> returns the mean of <code>abs(amount)</code> per category, rounded to 2 decimals, over recorded transactions only.</li>
      <li><code>busiest_hour()</code> returns the hour, 0 to 23, with the most transactions. Ties go to the earliest hour. With no transactions it returns None.</li>
    </ul>
  </div></div>
</details>
<details class="drill">
  <summary>Part 4 · Ranking customers and their habits</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>top_customers(k)</code> returns the names of the k customers who moved the most money, the sum of <code>abs(amount)</code>, highest first. Ties go to the name that sorts first. Customers with no transactions still rank, at zero.</li>
      <li><code>most_common_category(customer_id)</code> returns the category the customer uses most across all their accounts. Ties go to the category that sorts first. With no transactions it returns None. An unknown customer raises <code>ValueError</code>.</li>
    </ul>
  </div></div>
</details>
"""

TRACKER_PARTS = """
<details class="drill" open>
  <summary>Part 1 · Logging hours, with validation</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>add_employee(emp_id, name, department)</code> and <code>add_project(project_id, name)</code>. Repeated ids raise <code>ValueError</code>.</li>
      <li><code>log(emp_id, project_id, date, hours)</code>. Unknown ids, hours of zero or less, or pushing that employee's total for that date above 24 raise <code>ValueError</code> and log nothing. Exactly 24 is allowed, and the cap spans projects.</li>
      <li><code>total_hours(emp_id)</code> returns the employee's total, or 0. An unknown employee raises <code>ValueError</code>.</li>
    </ul>
    <p class="probe">Ask before coding: can the same person log the same project twice in a day? Is the 24-hour cap per project or per person? Are dates always ISO <code>YYYY-MM-DD</code>?</p>
  </div></div>
</details>
<details class="drill">
  <summary>Part 2 · Department and project statistics — open once Part 1 passes</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>department_hours()</code> returns <code>{department: total hours}</code> for every department that has an employee, including departments whose people logged nothing.</li>
      <li><code>project_average(project_id)</code> returns total hours divided by the number of <em>distinct</em> contributing employees, rounded to 2 decimals, or 0.0 if nobody has logged. Someone who logs twice counts once.</li>
    </ul>
  </div></div>
</details>
<details class="drill">
  <summary>Part 3 · The busiest date and the top contributor</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>busiest_date()</code> returns the date with the most hours logged across everyone. Ties go to the earliest date. When empty it returns None.</li>
      <li><code>top_contributor(project_id)</code> returns the name of the employee with the most hours on the project. Ties go to the name that sorts first. With nobody it returns None.</li>
    </ul>
  </div></div>
</details>
<details class="drill">
  <summary>Part 4 · A relationship query</summary>
  <div class="drill-body single"><div class="stack">
    <ul class="spec">
      <li><code>collaborators(emp_id)</code> returns the names of the other employees who share at least one project with <code>emp_id</code>, ordered by the number of shared projects, most first, then by name.</li>
    </ul>
  </div></div>
</details>
"""

page = """<title>Citi · Karat Python Interview — Senior AI Engineer</title>
@@STYLE@@
@@EXTRA_CSS@@

<a class="skip-link" href="#main">Skip to preparation</a>

<div class="wrap" id="top">
  <nav class="sitenav" aria-label="Prep documents">
    <a href="papercusp-answer-bank.html">Answer&nbsp;Bank</a>
    <a href="interview-feedback-answers.html">Feedback&nbsp;Answers</a>
    <a href="servicenow-staff-ml-interview-prep.html">ServiceNow&nbsp;Staff&nbsp;ML</a>
    <a href="steampunk-senior-ai-developer.html">Steampunk&nbsp;AI&nbsp;Developer</a>
    <a href="twg-recruiter-screen.html">TWG&nbsp;Global</a>
    <a href="rtx-hirevue-prep.html">RTX&nbsp;Screen</a>
    <a href="hyundai-autoever-applied-ai-hm-call.html">Hyundai&nbsp;AutoEver</a>
    <a href="kaseya-codesignal-mle-core.html">Kaseya&nbsp;CodeSignal</a>
    <a href="experian-sova-assessment.html">Experian&nbsp;Sova</a>
    <a href="roblox-assessments.html">Roblox&nbsp;Games</a>
    <a href="arrivia-member-travel-concierge.html">arrivia&nbsp;System&nbsp;Design</a>
    <a href="arrivia-evp-shawn-sandy.html">arrivia&nbsp;EVP&nbsp;Call</a>
    <a href="emergent-ai-director-testgorilla.html">Emergent&nbsp;AI&nbsp;Director</a>
    <a href="creatoriq-agentic-experience-prep.html">CreatorIQ&nbsp;Agentic</a>
    <a href="rackspace-fde.html">Rackspace&nbsp;FDE</a>
    <a href="flosum-ai-gtm.html">Flosum&nbsp;AI&nbsp;GTM</a>
    <a href="m3-senior-agentic-engineer.html">M3&nbsp;Agentic</a>
    <a href="anthropic-technical-advisor.html">Anthropic&nbsp;Advisor</a>
    <a href="citi-karat-python-interview.html" aria-current="page">Citi&nbsp;Karat</a>
    <a href="thomson-reuters-cocounsel-lead.html">TR&nbsp;CoCounsel</a>
    <a href="verizon-ai-control-plane-screen.html">Verizon&nbsp;Control&nbsp;Plane</a>
    <a href="turing-ai-eval-coding-agents.html">Turing&nbsp;AI&nbsp;Eval</a>
    <a href="micro1-forward-deployed-engineer.html">micro1&nbsp;FDE</a>
    <a href="jpmc-payments-ai-developer-portal.html">JPMC&nbsp;Payments</a>
    <span class="sep"></span>
    <a href="mcp-cicd-study-faq.html">CI/CD&nbsp;+&nbsp;MCP&nbsp;FAQ</a>
  </nav>

  <header class="masthead">
    <div class="mastcopy">
      <p class="eyebrow">Senior AI Engineer · Vice President · Citi · Karat round 1 · prepared @@PREPARED@@</p>
      <h1>Sixty minutes, one Karat engineer, and your reasoning out loud.</h1>
      <p class="standfirst">Citi's first round is a recorded video call with a Karat Interview Engineer: a short conversation about your experience, Python knowledge questions, then a multi-part backend coding exercise. The recruiter's email names the exact topics, so this page drills exactly those. That means default arguments, identity versus equality, and file handling, then classes that group, rank, average and find the busiest. Every output and every solution below was executed before it was written here.</p>
    </div>
    <aside class="join-card" aria-label="Interview scheduling">
      <p class="eyebrow">Owner-supplied email · 16 Sep 2026</p>
      <p><strong>Wait for Karat's scheduling email.</strong><br><span class="muted">Citi's recruiter said it arrives shortly. You pick the slot, and Karat reports many interviews run on evenings and weekends.</span></p>
      <p><strong class="hot">Python, live, recorded.</strong><br><span class="muted">Karat sends Citi's recruiter the video and a summary. Start with <a href="#first">section 01</a>, then drill <a href="#knowledge">section 03</a>.</span></p>
      <a class="button" href="https://karat.com/candidate-experience/" target="_blank" rel="noreferrer">Karat: what the interview is ↗</a>
      <p class="small muted">Practise in <code>citi-karat-practice.py</code> in this folder. Close this page, and every other aid, before the interview starts.</p>
    </aside>
  </header>

  <dl class="facts" aria-label="Interview and role facts">
    <div class="fact"><dt>Role</dt><dd>Senior AI Engineer · VP</dd></div>
    <div class="fact"><dt>Location</dt><dd>Jersey City · hybrid</dd></div>
    <div class="fact"><dt>Round</dt><dd>1 · Karat, live</dd></div>
    <div class="fact"><dt>Length</dt><dd>60 minutes</dd></div>
    <div class="fact"><dt>Coding</dt><dd>Python · ~40 min</dd></div>
    <div class="fact"><dt>Date</dt><dd class="hot">Not yet scheduled</dd></div>
  </dl>

  <nav class="toc" aria-label="Contents">
    <p class="eyebrow">Use the page in this order</p>
    <ol>
      <li><span class="n">01</span><a href="#first">Read this first</a></li>
      <li><span class="n">02</span><a href="#experience">Experience discussion</a></li>
      <li><span class="n">03</span><a href="#knowledge">Python knowledge drills</a></li>
      <li><span class="n">04</span><a href="#method">Running the coding round</a></li>
      <li><span class="n">05</span><a href="#bank">Problem 1 · Bank</a></li>
      <li><span class="n">06</span><a href="#tracker">Problem 2 · Project tracker</a></li>
      <li><span class="n">07</span><a href="#update">Problem 3 · Update given code</a></li>
      <li><span class="n">08</span><a href="#plan">Practice plan</a></li>
      <li><span class="n">09</span><a href="#dayof">Day-of checklist</a></li>
      <li><span class="n">10</span><a href="#sources">Sources + confidence</a></li>
    </ol>
  </nav>

  <main id="main">
    <section id="first">
      <div class="sec-head">
        <p class="eyebrow">01 · Read this first</p>
        <h2>The email tells you the test. Prepare for exactly that.</h2>
      </div>
      <div class="priority-grid">
        <article class="priority">
          <span class="num">01 / KNOWLEDGE · ~10 MIN</span>
          <h3>Three named Python topics</h3>
          <p>Default parameter evaluation, identity versus equality, and file handling with efficient iteration. Expect to predict output, spot the bug and explain the fix. See <a href="#knowledge">section 03</a>.</p>
        </article>
        <article class="priority">
          <span class="num">02 / CODING · ~40 MIN</span>
          <h3>One class, several parts</h3>
          <p>Methods that manage entities and their relationships, then aggregate, group, rank, average, and find the most frequent or busiest. Later parts reward the state you chose early. See <a href="#bank">sections 05–07</a>.</p>
        </article>
        <article class="priority">
          <span class="num">03 / NARRATION</span>
          <h3>They grade the explanation</h3>
          <p>The email lists answering “without explaining your thought process” as prohibited conduct. Restate, plan, state complexity, test out loud. See <a href="#method">section 04</a>.</p>
        </article>
        <article class="priority">
          <span class="num">04 / EXPERIENCE · BRIEF</span>
          <h3>One story, ninety seconds</h3>
          <p>Karat's own outline gives this a brief introduction slot, not a behavioural round. Have one Python story and one agent-systems story ready. See <a href="#experience">section 02</a>.</p>
        </article>
      </div>
      <div class="two-col">
        <div class="note crit">
          <p class="eyebrow">Interview integrity · from Citi's email</p>
          <p>Citi states a zero-tolerance policy, and Karat flags behaviour inconsistent with independent live problem-solving: help from another person, copy-pasting pre-written solutions, answers without reasoning, and code that matches online sources. Use this page to build fluency <strong>before</strong> the interview, then close it. Rewrite each problem from blank regions rather than memorising the reference, because the engineer will ask why you chose each line.</p>
        </div>
        <div class="note info">
          <p class="eyebrow">How a multi-part problem unfolds <span class="badge inference">Inference</span></p>
          <p>Candidate guides describe Karat coding as starting easy and extending as you progress: Part 1 runs, you state its complexity, and the next part changes the requirements. How far you get matters, and so does how cleanly your early design absorbs the later parts. That is why each problem below is four parts on one class.</p>
        </div>
      </div>
      <div class="note warn">
        <p class="eyebrow">The JD values AI coding tools. This round forbids them.</p>
        <p>The posting asks for hands-on experience with Claude Code, Devin, Cursor and Copilot, and that is a strength to bring to later rounds. It does not apply to Karat. Treat the live round as an in-person whiteboard with a Python interpreter, exactly as the email says.</p>
      </div>
    </section>

    <section id="experience">
      <div class="sec-head">
        <p class="eyebrow">02 · Experience discussion</p>
        <h2>A short conversation with someone who is not the hiring team</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <p class="eyebrow">What the role emphasises <span class="badge fact">Citi posting</span></p>
          <h3>Senior AI Engineer, Vice President</h3>
          <ul>
            <li>Lead AI agent development and architecture, integrated with enterprise systems through secure APIs.</li>
            <li>Python backend services with FastAPI and asyncio, REST APIs and data pipelines.</li>
            <li>Resilient systems: advanced error handling, fault tolerance, intelligent routing.</li>
            <li>Performance, latency and cost through profiling, caching and distributed-systems work.</li>
            <li>CI/CD with automated testing <em>and agent evaluation</em>, code review, mentoring.</li>
            <li>RAG, LLMs, LangChain, LangGraph or Google ADK; Kubernetes; 6+ years with strong Python.</li>
          </ul>
        </article>
        <article class="card">
          <p class="eyebrow">Which story for which prompt</p>
          <h3>Point at material you have already checked</h3>
          <ul>
            <li><strong>“A Python system you built.”</strong> The Storewolf scoring service: <a href="servicenow-staff-ml-interview-prep.html#stack">ServiceNow page, section 07</a>.</li>
            <li><strong>“Tell me about a recent project.”</strong> Papercusp's two-minute overview: <a href="papercusp-answer-bank.html#n-overview">Answer Bank N1</a>.</li>
            <li><strong>Resilience and fault tolerance.</strong> Telling a dead worker from a slow one: <a href="papercusp-answer-bank.html#n-liveness">N3</a>.</li>
            <li><strong>Agent evaluation.</strong> Evidence-backed completion and independent grading: <a href="papercusp-answer-bank.html#q-ai-eval">Q8</a>.</li>
            <li><strong>Hardest bug.</strong> The liveness check that lied: <a href="papercusp-answer-bank.html#q-debugging">Q3</a>.</li>
          </ul>
        </article>
      </div>
      <div class="script short">
        <p class="eyebrow">Draft · the Python story, about 90 seconds · keep only what you can defend</p>
        <p class="say">One Python system I built is the scoring service behind a gradient-boosted pricing model. The main application was Node, so instead of an HTTP service the model ran as a long-lived Python process: the Node side writes one JSON command per line, train or predict, and reads one JSON line back. The process loads the trained XGBoost model once, so a ten-thousand-row prediction batch doesn't pay that cost. The hard part wasn't the model, it was the feature schema. pandas <code>get_dummies</code> builds one-hot columns from whatever batch it sees, so an inference batch can silently produce a different column set from training. Training persists the exact column list, inference re-adds any missing columns as zeros, and then reorders to the booster's own feature names — two independent guards against one failure. If I were hardening it now, I'd persist a fitted scikit-learn Pipeline as the artifact, and I'd fix the imputer being re-fitted at prediction time.</p>
        <p class="small muted">Every claim above is on the <a href="servicenow-staff-ml-interview-prep.html#stack">ServiceNow page's verified inventory</a>. Papercusp is TypeScript-heavy; if asked about Python there, say so plainly.</p>
      </div>
      <div class="note warn">
        <p class="eyebrow">Keep it short, keep it true</p>
        <p>Karat's published outline gives this a brief introduction ahead of the technical sections, and the engineer is scoring for Citi, not deciding. Offer one story in about ninety seconds, let them pick what to follow up, and move on. Use only numbers that already appear on the Answer Bank or the ServiceNow page.</p>
      </div>
    </section>

    <section id="knowledge">
      <div class="sec-head">
        <p class="eyebrow">03 · Python knowledge drills</p>
        <h2>Predict the output, say why, then open the card</h2>
      </div>
      <p class="muted">Every snippet was executed by <code>build-citi-karat-page.py</code> on Python @@PYVER@@, and the build fails if an output drifts from its explanation. It was also re-run on @@ALTVER@@; where that older version prints something different, the card shows both. Error wording varies between versions; the behaviour does not.</p>

      <div class="topic-head" id="k-defaults">
        <p class="eyebrow">Topic 1 of 3 · named in the email</p>
        <h3>Default parameter evaluation</h3>
        <p class="rule">The rule: a default is evaluated once, when <code>def</code> runs, and every call that omits the argument reuses that one object.</p>
      </div>
      @@DEFAULTS@@

      <div class="topic-head" id="k-identity">
        <p class="eyebrow">Topic 2 of 3 · named in the email</p>
        <h3>Object identity versus value equality</h3>
        <p class="rule">The rule: <code>==</code> asks whether values are equal and runs code the class controls; <code>is</code> asks whether two names are the same object and cannot be overridden.</p>
      </div>
      @@IDENTITY@@

      <div class="topic-head" id="k-files">
        <p class="eyebrow">Topic 3 of 3 · named in the email</p>
        <h3>File handling and efficient iteration</h3>
        <p class="rule">The rule: stream instead of loading, close deterministically, convert types once at the boundary, and remember that iterators are single-pass.</p>
      </div>
      @@FILES@@

      <div class="topic-head" id="k-spoken">
        <p class="eyebrow">Spoken questions</p>
        <h3>Answer these out loud before opening them</h3>
        <p class="rule">The last two go beyond the email's topics. They cover the asyncio and FastAPI work the Citi posting names, and are cheap insurance for later rounds.</p>
      </div>
      @@CARDS@@
    </section>

    <section id="method">
      <div class="sec-head">
        <p class="eyebrow">04 · Running the coding round</p>
        <h2>The email's six instructions, turned into what you actually do</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>The loop for every part</h3>
          <ol class="timeline">
            <li><div><h4>Understand · 2 minutes</h4><p>Restate the task in one sentence. Ask about ties, empty input, unknown ids, format guarantees and return types. Walk the given example by hand.</p></div></li>
            <li><div><h4>Plan · 2 minutes</h4><p>Name your data structures from the queries: “what will later parts look things up by?” State the complexity you are aiming for before you type.</p></div></li>
            <li><div><h4>Code · narrate intent</h4><p>Say what each block is for, not what each character is. The moment you parse something twice, write a helper.</p></div></li>
            <li><div><h4>Test · 3 minutes</h4><p>Run the given sample. Then add your own cases: empty, single item, a tie, an unknown id, and the boundary, such as exactly zero or exactly 24.</p></div></li>
            <li><div><h4>Complexity, then the next part</h4><p>State time and space. When the next part arrives, ask aloud whether it changes your state design before adding any code.</p></div></li>
          </ol>
        </article>
        <article class="card">
          <h3>The simplify checklist</h3>
          <p class="muted small">The email tells you to keep one. This is it; run through it at the start of every part.</p>
          <ul class="checklist" style="grid-template-columns: 1fr">
            <li>Can a dict lookup replace a search?</li>
            <li>Can I keep a running value on write instead of scanning on read?</li>
            <li>Is there a standard tool: <code>Counter</code>, <code>defaultdict</code>, <code>heapq</code>, <code>sorted</code> with a key, <code>dict.fromkeys</code>?</li>
            <li>Can one tuple key express the ranking and the tie-break together?</li>
            <li>Can a neutral default, 0 or an empty list or None, remove a special case?</li>
            <li>Can I parse numbers and times once at the boundary, so nothing downstream sees strings?</li>
            <li>Stuck? Say what you know, what you are unsure of, and the brute-force version you would write first.</li>
          </ul>
        </article>
      </div>
      <div class="matrix-wrap">
        <table class="matrix compact">
          <thead><tr><th>You need to</th><th>Idiom</th><th>Cost</th></tr></thead>
          <tbody>
            <tr><td>Find an entity by id</td><td><code>self.customers[customer_id]</code>, a dict keyed by id</td><td>O(1)</td></tr>
            <tr><td>Follow a one-to-many link</td><td><code>self.accounts_of = defaultdict(list)</code>, indexed in both directions if you query both ways</td><td>O(1) per link</td></tr>
            <tr><td>Count by key</td><td><code>Counter(key(x) for x in items)</code></td><td>O(n)</td></tr>
            <tr><td>Total and average by key</td><td><code>totals[k] += v; counts[k] += 1</code>, divide at the end, guard empty</td><td>O(n)</td></tr>
            <tr><td>Most frequent, ties by a rule</td><td><code>min(counts, key=lambda k: (-counts[k], k))</code></td><td>O(k)</td></tr>
            <tr><td>Rank everything</td><td><code>sorted(scores, key=lambda k: (-scores[k], name(k)))</code></td><td>O(k log k)</td></tr>
            <tr><td>Top k only</td><td><code>heapq.nsmallest(k, scores, key=...)</code> with the same key</td><td>O(n log k)</td></tr>
            <tr><td>Remove duplicates, keep order</td><td><code>list(dict.fromkeys(items))</code></td><td>O(n)</td></tr>
            <tr><td>Compare times or amounts</td><td>Parse once: <code>int(ts[11:13])</code>, minutes since midnight, <code>float(row["amount"])</code></td><td>O(1) per row</td></tr>
            <tr><td>Answer reads cheaply</td><td>Update a running aggregate inside the write method</td><td>O(1) write</td></tr>
          </tbody>
        </table>
      </div>
      <div class="two-col">
        <div class="script short">
          <p class="eyebrow">Lines that keep you talking</p>
          <p class="say">I'll write the straightforward pass first so we have something correct, then tighten it.</p>
          <p class="say">Before I start Part 3, let me check whether my Part 1 structures still fit.</p>
          <p class="say">I'm unsure between these two approaches. This one costs O(n) per call and that one moves the work to the write path; I'm picking the second because reads are more frequent here.</p>
        </div>
        <div class="note info">
          <p class="eyebrow">If you get stuck</p>
          <p>The email says to speak up, and Karat engineers give hints. Silence reads worse than a wrong first idea. Name the sub-problem you are stuck on, state what you would try, and ask a narrow question, such as whether ties need handling, rather than “how do I do this?”.</p>
        </div>
      </div>
    </section>

    <section id="bank">
      <div class="sec-head">
        <p class="eyebrow">05 · Problem 1 · Bank</p>
        <h2>Customers own accounts, accounts carry transactions</h2>
      </div>
      <div class="note warn">
        <p class="eyebrow">How to use this problem</p>
        <p>Open <code>citi-karat-practice.py</code>, start a 35-minute timer, and talk out loud as if someone were listening. Record yourself on your phone if nobody can play the interviewer. Read one part at a time below, and only open the next when the file prints PASS for the current one. Compare with the reference afterwards, then listen back for silent stretches.</p>
      </div>
      @@BANK_PARTS@@
      <div class="two-col">
        <article class="card">
          <p class="eyebrow">Sample data used by the checks</p>
          @@BANK_FIXTURE@@
        </article>
        <article class="card">
          <h3>What to say while designing</h3>
          <ul>
            <li>“Customers own many accounts and transactions belong to accounts, so I need id to customer, account to owner, and customer to accounts.”</li>
            <li>“Balance will be asked constantly, so I'll keep a running balance per account instead of re-summing.”</li>
            <li>“In <code>record</code> I validate before I mutate, so a rejected debit leaves no trace.”</li>
            <li>“Every ‘most’ here has a tie rule, so I'll use one pattern everywhere: minimise negative count, then the name.”</li>
            <li>“I'll test an empty bank, a debit to exactly zero, a tie at the top, and an unknown id.”</li>
          </ul>
        </article>
      </div>
      <div class="matrix-wrap">
        <table class="matrix compact">
          <thead><tr><th>Method</th><th>Why it costs that</th><th>Time</th></tr></thead>
          <tbody>
            <tr><td>add_customer, open_account, record, balance</td><td>Dict lookups, with the balance maintained on every write</td><td>O(1)</td></tr>
            <tr><td>customer_balance</td><td>Walks only that customer's accounts</td><td>O(a)</td></tr>
            <tr><td>branch_summary</td><td>One pass over customers and their accounts</td><td>O(c + a)</td></tr>
            <tr><td>average_amount_by_category</td><td>One pass accumulating sum and count per category</td><td>O(n)</td></tr>
            <tr><td>busiest_hour</td><td>A Counter over at most 24 keys</td><td>O(n)</td></tr>
            <tr><td>top_customers</td><td>A volume pass, then heap-based top k</td><td>O(n + c log k)</td></tr>
            <tr><td>most_common_category</td><td>A scan; drops to O(categories) with a per-customer Counter kept on write</td><td>O(n)</td></tr>
          </tbody>
        </table>
      </div>
      <details class="drill">
        <summary>Follow-up questions an engineer could ask, with answers</summary>
        <div class="drill-body single"><div class="stack">
          <p><strong>“record runs millions of times a day and top_customers every second. What changes?”</strong> Move work to the write path: update per-customer volume, per-category sum and count, and per-hour counts inside <code>record</code>, so reads cost O(groups) or O(c log k). The price is write cost and consistency: a reversal or correction now has to update every aggregate.</p>
          <p><strong>“Two threads call record on the same account.”</strong> The balance check and the update are a check-then-act race. Lock per account, or push it into the database as one conditional statement, such as an <code>UPDATE</code> that only applies when the new balance stays at or above zero, and check the affected-row count.</p>
          <p><strong>“Amounts become dollars and cents.”</strong> Use integer cents or <code>Decimal</code> built from strings, never float.</p>
          <p><strong>“Write branch_summary in SQL.”</strong></p>
          <pre class="code"><code>SELECT c.branch,
       COUNT(DISTINCT c.customer_id) AS customers,
       COUNT(a.account_id)           AS accounts,
       COALESCE(SUM(a.balance), 0)   AS total_balance
FROM customers c
LEFT JOIN accounts a ON a.customer_id = c.customer_id
GROUP BY c.branch;</code></pre>
          <p class="small muted">The <code>LEFT JOIN</code> keeps customers without accounts; <code>COUNT(a.account_id)</code> ignores the resulting nulls.</p>
        </div></div>
      </details>
      @@BANK_SOLUTION@@
    </section>

    <section id="tracker">
      <div class="sec-head">
        <p class="eyebrow">06 · Problem 2 · Project tracker</p>
        <h2>Employees log hours against projects — and Part 4 is a graph question</h2>
      </div>
      @@TRACKER_PARTS@@
      <div class="two-col">
        <article class="card">
          <p class="eyebrow">Sample data used by the checks</p>
          @@TRACKER_FIXTURE@@
        </article>
        <article class="card">
          <h3>What to say while designing</h3>
          <ul>
            <li>“Part 4 asks who shares projects, so I'll index both directions from the start: project to a map of employee hours, and employee to their set of projects.”</li>
            <li>“The 24-hour rule needs a total per employee per date, which nothing else needs, so it gets its own dict.”</li>
            <li>“Inside validation I read defaultdicts with <code>.get</code>, so a rejected call doesn't create empty entries.”</li>
            <li>“ISO dates sort chronologically as strings, so the date itself can be the tie-break. That is not true of times like 9:05, which is Problem 3's bug.”</li>
          </ul>
        </article>
      </div>
      <div class="matrix-wrap">
        <table class="matrix compact">
          <thead><tr><th>Method</th><th>Why it costs that</th><th>Time</th></tr></thead>
          <tbody>
            <tr><td>log, total_hours</td><td>Every aggregate updated on write</td><td>O(1)</td></tr>
            <tr><td>department_hours</td><td>One pass over employees</td><td>O(e)</td></tr>
            <tr><td>project_average, top_contributor</td><td>Only that project's team</td><td>O(t)</td></tr>
            <tr><td>busiest_date</td><td>One pass over distinct dates</td><td>O(d)</td></tr>
            <tr><td>collaborators</td><td>Walks the teams of my projects, then sorts the m people found</td><td>O(Σt + m log m)</td></tr>
          </tbody>
        </table>
      </div>
      <details class="drill">
        <summary>Follow-up questions an engineer could ask, with answers</summary>
        <div class="drill-body single"><div class="stack">
          <p><strong>“Entries can now be edited or deleted.”</strong> Give entries ids and keep them. Every aggregate must be decremented on delete, or you recompute lazily per project and invalidate a cache on change. Say which you would pick given how often edits happen.</p>
          <p><strong>“Compute collaborators for everyone at once.”</strong> For each project, every pair of its team members shares it, so the cost is the sum of team size squared. That is fine for small teams and quadratic for large ones, where a sparse co-occurrence approach is better.</p>
          <p><strong>“Hours are floats. Is that safe?”</strong> Not for arbitrary fractions: use integer minutes or <code>Decimal</code>. The checks here use quarter hours, which binary floating point represents exactly.</p>
        </div></div>
      </details>
      @@TRACKER_SOLUTION@@
    </section>

    <section id="update">
      <div class="sec-head">
        <p class="eyebrow">07 · Problem 3 · Update given code</p>
        <h2>The checks fail. Fix the code without changing its interface, then extend it.</h2>
      </div>
      <div class="two-col">
        <div class="note info">
          <p class="eyebrow">Why this shape</p>
          <p>The email's third section is “Develop and <em>Update</em> Backend Code”, and a third-party report of Citi's Karat round describes a given-codebase bug fix that came down to <code>equals</code> and <code>hashCode</code>, the Java form of topic 2. This drill is deliberately dense: seven bugs drawn from the three knowledge topics. The real task is likely smaller.</p>
        </div>
        <div class="note warn">
          <p class="eyebrow">Work it out loud, in this order</p>
          <p>Run the checks and read the failing names first. Treat each docstring as the spec. Fix one bug at a time and re-run after each. Say which problem no check covers, the quadratic <code>top_customer</code>, and name the test you would add. Then add <code>busiest_hour()</code>, which returns the hour 0 to 23 with the most orders, earliest on a tie, or None when empty. Target: 20 minutes for the bugs, 10 for the method.</p>
        </div>
      </div>
      <article class="card">
        <p class="eyebrow">The given code — also the Problem 3 section of the practice file</p>
        @@GIVEN_CODE@@
      </article>
      <details class="solution">
        <summary>The seven bugs — open only after your attempt</summary>
        <div class="reveal">
          <div class="matrix-wrap">
            <table class="matrix compact">
              <thead><tr><th>What a check shows</th><th>Root cause</th><th>Fix</th></tr></thead>
              <tbody>
                <tr><td>1 · A brand-new book already has orders</td><td><code>orders=[]</code> is built once and shared by every <code>OrderBook()</code></td><td><code>orders=None</code>; create, or copy, the list in the body</td></tr>
                <tr><td>2 · <code>unique_orders</code> raises TypeError</td><td><code>__eq__</code> without <code>__hash__</code> makes Order unhashable; a set also loses order and is not the promised list</td><td>Hash <code>order_id</code>; return <code>list(dict.fromkeys(self.orders))</code></td></tr>
                <tr><td>3 · An equal customer name finds nothing</td><td><code>is</code> compares identity</td><td><code>==</code></td></tr>
                <tr><td>4 · 9:30 falls outside 9:00 to 12:00</td><td>Clock strings compare character by character</td><td>Parse to minutes once; compare integers</td></tr>
                <tr><td>5 · An empty book crashes <code>average_amount</code></td><td>Division by zero</td><td>Return 0.0 when empty, as the docstring says</td></tr>
                <tr><td>6 · An empty book crashes <code>top_customer</code></td><td><code>best[1]</code> on None; also re-sums every order per order, O(n²)</td><td>One pass into a totals dict; <code>min</code> over <code>(-total, name)</code></td></tr>
                <tr><td>7 · <code>load</code> fails on the header, names keep a newline</td><td>Every line split by hand, header included; file never closed; platform encoding</td><td><code>with open(path, newline="", encoding="utf-8")</code> and <code>csv.DictReader</code></td></tr>
              </tbody>
            </table>
          </div>
          <p class="small muted">The solutions file proves each check fails against this given code, and a separate run confirmed that fixing one bug turns exactly its own check green.</p>
        </div>
      </details>
      <details class="solution">
        <summary>Fixed code, with busiest_hour — open only after your attempt</summary>
        @@FIXED_CODE@@
      </details>
    </section>

    <section id="plan">
      <div class="sec-head">
        <p class="eyebrow">08 · Practice plan</p>
        <h2>Five sessions before whatever slot you book, then the morning of</h2>
      </div>
      <ol class="timeline">
        <li><div><h3>Session 1 · Knowledge out loud · 60 min</h3><p>Predict all @@NSNIPPETS@@ snippets in section 03 before opening each one, then answer the @@NCARDS@@ spoken cards aloud. For every miss, write the rule in your own words.</p></div></li>
        <li><div><h3>Session 2 · Problem 1, timed · 50 min</h3><p>35 minutes in the practice file for all four parts, narrating and recording. 15 minutes comparing with the reference and listening back for silences longer than about twenty seconds.</p></div></li>
        <li><div><h3>Session 3 · Problem 2, then a redo · 60 min</h3><p>Problem 2 at 35 minutes. Then rewrite your weakest Problem 1 part from a blank region without looking.</p></div></li>
        <li><div><h3>Session 4 · Given code and your story · 45 min</h3><p>Problem 3 at 30 minutes. Then two timed run-throughs of the 90-second story in section 02.</p></div></li>
        <li><div><h3>Session 5 · Full mock · 60 min</h3><p>Ideally someone plays the interviewer beforehand, which is preparation, not interview help. Five minutes of introduction, ten of knowledge from five random cards, forty of coding on a variant below you have not seen, five of questions. Stop at sixty.</p></div></li>
        <li><div><h3>The morning of</h3><p>Run the practice file once from a fresh copy until it is green, reread section 04 and section 09, then close every prep window.</p></div></li>
      </ol>
      <article class="card">
        <h3>Variants for the mock — same shape, new domain</h3>
        <ul>
          <li><strong>Library.</strong> Members, books and loans: average loan length per genre, busiest checkout weekday, members ranked by overdue count.</li>
          <li><strong>Airline.</strong> Flights, airports and delays: busiest airport by departures plus arrivals, average delay per route, most frequent route.</li>
          <li><strong>Clinic.</strong> Doctors, patients and appointments: average wait per doctor, busiest hour, patients who share the most doctors.</li>
          <li><strong>Courses.</strong> Students, courses and grades: average grade per course, most popular course per term, students who share the most courses.</li>
        </ul>
      </article>
    </section>

    <section id="dayof">
      <div class="sec-head">
        <p class="eyebrow">09 · Day-of checklist</p>
        <h2>Setup, rules, and what happens after</h2>
      </div>
      <ul class="checklist">
        <li>Book the slot from Karat's email and note the time zone it shows.</li>
        <li>Use Chrome or Firefox. Karat says Safari is supported but can have audio or video issues.</li>
        <li>Headphones, microphone, webcam, a stable connection and a quiet room, per Karat's own recommendation.</li>
        <li>Test your microphone and camera in the browser beforehand, not five minutes before.</li>
        <li>Ask at the start what is allowed, such as running code or checking standard-library documentation, and abide by the answer.</li>
        <li>Close this page, the practice files, AI tools and notes before you join.</li>
        <li>Expect a recording: Karat sends the video and a summary to Citi's recruiter.</li>
        <li>Water within reach, notifications off, phone silenced.</li>
      </ul>
      <div class="note info">
        <p class="eyebrow">If it goes badly <span class="badge fact">Karat</span></p>
        <p>Karat lets candidates request a redo of a first-round interview within 24 hours, with a different set of questions. Both recommendations go to the employer, which decides whether to advance you, so a redo adds a data point rather than erasing one. Use it only if the first attempt clearly did not reflect you.</p>
      </div>
    </section>

    <section id="sources">
      <div class="sec-head">
        <p class="eyebrow">10 · Sources + confidence</p>
        <h2>What came from Citi, what came from Karat, and what is inferred</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>Confidence by claim</h3>
          <ul>
            <li><span class="badge owner">Owner</span> Section list, the three knowledge topics, the three coding topics, the six interview instructions (understand, optimize, test, simplify, explain, speak up), the integrity rules and the round order: Citi recruiter email, received 16 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Role title, Jersey City hybrid, responsibilities and qualifications, posting close date 17 Sep 2026: Citi's Workday posting, requisition 26988992, fetched 16 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Sixty minutes with a brief introduction, about 10 minutes of discussion questions and 40 of programming; recording and summary sent to the recruiter: Karat's candidate-experience page, fetched 16 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Redo within 24 hours, new questions, both recommendations to the employer: Karat's redo page, fetched 16 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Every snippet output was captured on Python @@PYVER@@ at build time and re-run on @@ALTVER@@; every reference solution passed <code>citi-karat-solutions.py</code> on both; each Problem 3 check fails on the given code.</li>
            <li><span class="badge inference">Inference</span> That Citi's Karat round includes short output-prediction or bug-finding questions and a given-codebase fix: third-party guides published by interview-assistant vendors, low reliability, Aug 2026.</li>
            <li><span class="badge inference">Inference</span> The three problems resemble the described format. They are original practice material, not leaked questions.</li>
            <li><span class="badge unknown">Unknown</span> Interview date, team, the Python version in Karat's editor, and whether documentation lookup is permitted.</li>
          </ul>
        </article>
        <article class="card">
          <h3>Sources</h3>
          <ul class="source-list">
            <li><a href="https://citi.wd5.myworkdayjobs.com/2/job/jersey-city-new-jersey-united-states/senior-ai-engineer---vice-president_26988992" target="_blank" rel="noreferrer">Citi — Senior AI Engineer, Vice President, Jersey City (Workday posting 26988992)</a></li>
            <li><a href="https://karat.com/candidate-experience/" target="_blank" rel="noreferrer">Karat — The Karat interview experience</a></li>
            <li><a href="https://connect.karat.com/redo-interviews" target="_blank" rel="noreferrer">Karat — Redo interviews</a></li>
            <li><a href="https://interviewfox.ai/interview-questions/citi-karat-oa-guide/" target="_blank" rel="noreferrer">Third-party guide — Citi Karat interview, Java/Spring track, Aug 2026 (vendor content, low reliability)</a></li>
            <li><a href="https://docs.python.org/3/library/csv.html" target="_blank" rel="noreferrer">Python docs — csv, including the newline="" requirement</a></li>
            <li><a href="https://peps.python.org/pep-0686/" target="_blank" rel="noreferrer">PEP 686 — Make UTF-8 mode default</a></li>
            <li><a href="citi-karat-solutions.py">citi-karat-solutions.py</a> — the tested source · <a href="citi-karat-practice.py">citi-karat-practice.py</a> — the practice file · <a href="build-citi-karat-page.py">build-citi-karat-page.py</a> — the generator</li>
          </ul>
        </article>
      </div>
    </section>
  </main>

  <footer>
    <p>Prepared @@PREPARED@@ for Citi's Karat round for Senior AI Engineer, Vice President. Generated by <code>build-citi-karat-page.py</code>, which refuses to write this page unless the solutions pass and every snippet output matches its explanation.</p>
    <p><a href="#top">Back to top ↑</a></p>
  </footer>
</div>
"""

replacements = {
    "@@STYLE@@": style,
    "@@EXTRA_CSS@@": extra_css,
    "@@PREPARED@@": PREPARED,
    "@@PYVER@@": PRIMARY_VERSION,
    "@@ALTVER@@": f"Python {ALT_VERSION}" if ALT_VERSION else "no second interpreter (python3.12 not found)",
    "@@NSNIPPETS@@": str(len(DEFAULTS) + len(IDENTITY) + len(FILES)),
    "@@NCARDS@@": str(len(CARDS)),
    "@@DEFAULTS@@": predict_cards(DEFAULTS, "Defaults"),
    "@@IDENTITY@@": predict_cards(IDENTITY, "Identity"),
    "@@FILES@@": predict_cards(FILES, "Files and iteration"),
    "@@CARDS@@": flash_cards(),
    "@@BANK_PARTS@@": BANK_PARTS,
    "@@BANK_FIXTURE@@": code_block(fixture("_bank")),
    "@@BANK_SOLUTION@@": solution_pair("bank", "35 min"),
    "@@TRACKER_PARTS@@": TRACKER_PARTS,
    "@@TRACKER_FIXTURE@@": code_block(fixture("_tracker")),
    "@@TRACKER_SOLUTION@@": solution_pair("tracker", "35 min"),
    "@@GIVEN_CODE@@": code_block(GIVEN_CODE),
    "@@FIXED_CODE@@": code_block(sections["orderbook"]),
}
for marker, value in replacements.items():
    assert marker in page, marker
    page = page.replace(marker, value)
leftover = re.findall(r"@@\w+@@", page)
assert not leftover, leftover

PAGE.write_text(page, encoding="utf-8")
print(f"solutions green; {len(DEFAULTS) + len(IDENTITY) + len(FILES)} snippets matched; {len(CARDS)} spoken cards")
print(f"wrote {PRACTICE} ({PRACTICE.stat().st_size} bytes)")
print(f"wrote {PAGE} ({PAGE.stat().st_size} bytes)")
