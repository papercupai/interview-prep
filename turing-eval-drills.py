"""
Turing · AI Evaluation / Coding Agents — REVIEW DRILLS (self-checking).

    python3 turing-eval-drills.py            runs every response against every test; exit 0 only if every
                                             result matches the expectation declared beside it

Each drill is a small, realistic agent task: an issue, the original code, and two agent responses (A and B)
with the agent's own final message. The hidden tests encode what the issue actually requires, including
cases the agent's visible test missed. build-turing-page.py imports this file, re-runs it, and refuses to
write the page if any declared result is wrong — so every "B fails on X" on the page was observed, not assumed.

The scenarios are original practice material modelled on common coding-agent failure modes; they are not
Turing's exercise.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

P, F, NA = "pass", "fail", "n/a"

DRILLS = [
    # ------------------------------------------------------------------------------------------------
    dict(
        id="durations",
        title="Compound durations",
        mode="Correct versus incomplete",
        language="python",
        module="durations.py",
        issue='`parse_duration` rejects compound values. Users type things like "1h30m" or "2m5s" into the '
              'timeout field and get a ValueError. It should accept any combination of hours, minutes and seconds.',
        original=r'''
import re

_UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text):
    """Parse a duration such as "90s", "15m" or "2h" into seconds."""
    match = re.fullmatch(r"(\d+)([hms])", text.strip())
    if not match:
        raise ValueError(f"invalid duration: {text!r}")
    value, unit = match.groups()
    return int(value) * _UNIT_SECONDS[unit]
''',
        responses={
            "A": dict(claim="parse_duration now accepts any sequence of number-and-unit parts. Added tests for 1h30m and 2m5s; the suite passes.", code=r'''
import re

_UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}
_PART = re.compile(r"(\d+)([hms])")


def parse_duration(text):
    """Parse a duration such as "90s", "15m", "2h" or "1h30m" into seconds."""
    text = text.strip()
    if not re.fullmatch(r"(?:\d+[hms])+", text):
        raise ValueError(f"invalid duration: {text!r}")
    return sum(int(value) * _UNIT_SECONDS[unit] for value, unit in _PART.findall(text))
'''),
            "B": dict(claim="Added support for compound durations like 1h30m. I added a test for 1h30m and the full suite passes.", code=r'''
import re

_UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text):
    """Parse a duration such as "90s", "15m", "2h" or "1h30m" into seconds."""
    match = re.fullmatch(r"(\d+)([hms])(?:(\d+)([hms]))?", text.strip())
    if not match:
        raise ValueError(f"invalid duration: {text!r}")
    first_value, first_unit, second_value, second_unit = match.groups()
    total = int(first_value) * _UNIT_SECONDS[first_unit]
    if second_value:
        total += int(second_value) * _UNIT_SECONDS[second_unit]
    return total
'''),
        },
        setup="from durations import parse_duration",
        tests=[
            dict(name='"1h30m" is 5400 seconds — the agent-visible test', visible=True,
                 code='assert parse_duration("1h30m") == 5400', expect={"original": F, "A": P, "B": P}),
            dict(name='Single units still work', code='assert parse_duration("90s") == 90 and parse_duration("2h") == 7200',
                 expect={"original": P, "A": P, "B": P}),
            dict(name='Three parts: "1h2m3s" is 3723', code='assert parse_duration("1h2m3s") == 3723',
                 expect={"original": F, "A": P, "B": F}),
            dict(name='Garbage is still rejected', code='''
for bad in ["", "h", "1x", "1h 30m", "-5m"]:
    try:
        parse_duration(bad)
    except ValueError:
        continue
    raise AssertionError(f"accepted {bad!r}")
''', expect={"original": P, "A": P, "B": P}),
            dict(name='Probe, spec silent: a repeated unit such as "1h1h" is rejected', probe=True,
                 code='''
try:
    parse_duration("1h1h")
except ValueError:
    pass
else:
    raise AssertionError("accepted 1h1h")
''', expect={"original": P, "A": F, "B": F}),
        ],
    ),
    # ------------------------------------------------------------------------------------------------
    dict(
        id="settings",
        title="Optional settings",
        mode="Fixing a crash by hiding every error",
        language="python",
        module="settings.py",
        issue="`load_settings` crashes with KeyError when settings.json leaves out `timeout` or `retries`. "
              "Those two are optional and should fall back to DEFAULTS. `endpoint` is required.",
        original=r'''
import json

DEFAULTS = {"timeout": 30, "retries": 3}


def load_settings(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {"endpoint": raw["endpoint"], "timeout": raw["timeout"], "retries": raw["retries"]}
''',
        responses={
            "A": dict(claim="Optional keys now fall back to DEFAULTS, and a missing endpoint raises a clear ValueError naming the file.", code=r'''
import json

DEFAULTS = {"timeout": 30, "retries": 3}


def load_settings(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if "endpoint" not in raw:
        raise ValueError(f"{path}: 'endpoint' is required")
    return {
        "endpoint": raw["endpoint"],
        "timeout": raw.get("timeout", DEFAULTS["timeout"]),
        "retries": raw.get("retries", DEFAULTS["retries"]),
    }
'''),
            "B": dict(claim="Made load_settings robust: missing keys fall back to defaults and it no longer crashes on bad input.", code=r'''
import json

DEFAULTS = {"timeout": 30, "retries": 3}


def load_settings(path):
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return {
            "endpoint": raw.get("endpoint"),
            "timeout": raw.get("timeout", 30),
            "retries": raw.get("retries", 3),
        }
    except Exception:
        return {"endpoint": None, **DEFAULTS}
'''),
        },
        setup='''
import os, tempfile
from settings import load_settings

def write(content):
    handle, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(handle, "w", encoding="utf-8") as f:
        f.write(content)
    return path
''',
        tests=[
            dict(name="Optional keys fall back to defaults — the agent-visible test", visible=True,
                 code='assert load_settings(write(\'{"endpoint": "https://api"}\')) == {"endpoint": "https://api", "timeout": 30, "retries": 3}',
                 expect={"original": F, "A": P, "B": P}),
            dict(name="Explicit values still win",
                 code='assert load_settings(write(\'{"endpoint": "https://api", "timeout": 5}\')) == {"endpoint": "https://api", "timeout": 5, "retries": 3}',
                 expect={"original": F, "A": P, "B": P}),
            dict(name="A missing endpoint is an error, not None", code='''
try:
    result = load_settings(write('{"timeout": 5}'))
except (ValueError, KeyError):
    pass
else:
    raise AssertionError(f"returned {result!r}")
''', expect={"original": P, "A": P, "B": F}),
            dict(name="Malformed JSON is an error, not silent defaults", code='''
try:
    result = load_settings(write('{"endpoint": "https://api",}'))
except ValueError:
    pass
else:
    raise AssertionError(f"returned {result!r}")
''', expect={"original": P, "A": P, "B": F}),
            dict(name="A missing file is an error, not silent defaults", code='''
try:
    result = load_settings("/nonexistent/settings.json")
except FileNotFoundError:
    pass
else:
    raise AssertionError(f"returned {result!r}")
''', expect={"original": P, "A": P, "B": F}),
        ],
    ),
    # ------------------------------------------------------------------------------------------------
    dict(
        id="quotes",
        title="Concurrent quotes",
        mode="Passes the test because the mock is instant",
        language="javascript",
        module="fetchPrices.js",
        issue="Loading a 50-symbol watchlist takes about five seconds because `fetchPrices` awaits each quote in turn. "
              "Fetch the quotes concurrently. The return value must not change.",
        original=r'''
async function fetchPrices(symbols, getQuote) {
  const prices = {};
  for (const symbol of symbols) {
    prices[symbol] = await getQuote(symbol);
  }
  return prices;
}

module.exports = { fetchPrices };
''',
        responses={
            "A": dict(claim="Quotes are now fetched concurrently with Promise.all; the result shape is unchanged.", code=r'''
async function fetchPrices(symbols, getQuote) {
  const quotes = await Promise.all(symbols.map((symbol) => getQuote(symbol)));
  return Object.fromEntries(symbols.map((symbol, i) => [symbol, quotes[i]]));
}

module.exports = { fetchPrices };
'''),
            "B": dict(claim="Parallelised fetchPrices. The existing test passes and the function now returns in under 1 ms.", code=r'''
async function fetchPrices(symbols, getQuote) {
  const prices = {};
  symbols.forEach(async (symbol) => {
    prices[symbol] = await getQuote(symbol);
  });
  return prices;
}

module.exports = { fetchPrices };
'''),
        },
        setup="",
        tests=[
            dict(name="A price per symbol, with an instant mock — the agent-visible test", visible=True, code='''
const getQuote = async (symbol) => ({ C: 71.2, JPM: 248.9 })[symbol];
assert.deepEqual(await mod.fetchPrices(["C", "JPM"], getQuote), { C: 71.2, JPM: 248.9 });
''', expect={"original": P, "A": P, "B": P}),
            dict(name="A price per symbol when each quote takes 20 ms", code='''
const getQuote = (symbol) => new Promise((resolve) => setTimeout(() => resolve(symbol.length), 20));
assert.deepEqual(await mod.fetchPrices(["C", "JPM", "GS"], getQuote), { C: 1, JPM: 3, GS: 2 });
''', expect={"original": P, "A": P, "B": F}),
            dict(name="Ten 50 ms quotes finish in under 250 ms", code='''
const getQuote = () => new Promise((resolve) => setTimeout(() => resolve(1), 50));
const symbols = Array.from({ length: 10 }, (_, i) => `S${i}`);
const started = Date.now();
await mod.fetchPrices(symbols, getQuote);
const elapsed = Date.now() - started;
note(`${elapsed} ms`);
assert.ok(elapsed < 250, `took ${elapsed} ms`);
''', expect={"original": F, "A": P, "B": P}),
            dict(name="A failed quote rejects the call", code='''
const getQuote = (symbol) => new Promise((resolve, reject) =>
  setTimeout(() => (symbol === "BAD" ? reject(new Error("no quote for BAD")) : resolve(1)), 10));
await assert.rejects(mod.fetchPrices(["C", "BAD"], getQuote), /no quote/);
await new Promise((resolve) => setTimeout(resolve, 30));
''', expect={"original": P, "A": P, "B": F}),
            dict(name="No unhandled promise rejections escape", unhandled=True, code="",
                 expect={"original": P, "A": P, "B": F}),
        ],
    ),
    # ------------------------------------------------------------------------------------------------
    dict(
        id="search",
        title="Customer search",
        mode="Works for the demo, open to injection",
        language="python",
        module="customers.py",
        issue="Support needs a search box. Add `find_customers(conn, name_prefix)` returning `(id, name)` rows whose "
              "name starts with the typed prefix, ordered by name.",
        original=r'''
def list_customers(conn):
    return conn.execute("SELECT id, name FROM customers ORDER BY name").fetchall()
''',
        responses={
            "A": dict(claim="Added find_customers using a parameterised LIKE query; % and _ typed by a user are escaped so they match literally.", code=r'''
def list_customers(conn):
    return conn.execute("SELECT id, name FROM customers ORDER BY name").fetchall()


def find_customers(conn, name_prefix):
    # Escape LIKE wildcards so a typed % or _ is matched literally.
    escaped = name_prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return conn.execute(
        "SELECT id, name FROM customers WHERE name LIKE ? ESCAPE '\\' ORDER BY name",
        (escaped + "%",),
    ).fetchall()
'''),
            "B": dict(claim="Added find_customers. Verified manually: searching 'An' returns Ana and Andre.", code=r'''
def list_customers(conn):
    return conn.execute("SELECT id, name FROM customers ORDER BY name").fetchall()


def find_customers(conn, name_prefix):
    query = f"SELECT id, name FROM customers WHERE name LIKE '{name_prefix}%' ORDER BY name"
    return conn.execute(query).fetchall()
'''),
        },
        setup='''
import sqlite3
from customers import find_customers
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)")
conn.executemany("INSERT INTO customers (name) VALUES (?)", [("Ana",), ("Andre",), ("Ben",), ("O'Brien",), ("50% Off Ltd",)])
''',
        tests=[
            dict(name='"An" finds Ana and Andre — the agent-visible check', visible=True,
                 code='assert [name for _, name in find_customers(conn, "An")] == ["Ana", "Andre"]',
                 expect={"original": NA, "A": P, "B": P}),
            dict(name="A name with an apostrophe", code='assert find_customers(conn, "O\'B") == [(4, "O\'Brien")]',
                 expect={"original": NA, "A": P, "B": F}),
            dict(name="Injection: typing ' OR 1=1 -- returns nothing", code='''
rows = find_customers(conn, "' OR 1=1 --")
note(f"{len(rows)} rows returned")
assert rows == [], f"returned {len(rows)} rows"
''', expect={"original": NA, "A": P, "B": F}),
            dict(name="A typed % is literal, not a wildcard", code='''
rows = find_customers(conn, "%")
assert rows == [], f"returned {len(rows)} rows"
''', expect={"original": NA, "A": P, "B": F}),
            dict(name='Probe, spec silent: the search is case-sensitive ("an" finds nothing)', probe=True,
                 code='assert find_customers(conn, "an") == []', expect={"original": NA, "A": F, "B": F}),
        ],
    ),
    # ------------------------------------------------------------------------------------------------
    dict(
        id="refunds",
        title="Refund formatting",
        mode="Right fix, wrong scope",
        language="python",
        module="report.py",
        issue="Refunds show as `$-12.50` in the finance report. They should read `-$12.50`.",
        original=r'''
def format_amount(cents):
    return f"${cents / 100:,.2f}"


def build_report(rows):
    """rows: (name, cents) pairs, already in the order the finance team wants."""
    return "\n".join(f"{name}: {format_amount(cents)}" for name, cents in rows)
''',
        responses={
            "A": dict(claim="Negative amounts now render as -$12.50. Added a test for a refund and for -1 cent.", code=r'''
def format_amount(cents):
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) / 100:,.2f}"


def build_report(rows):
    """rows: (name, cents) pairs, already in the order the finance team wants."""
    return "\n".join(f"{name}: {format_amount(cents)}" for name, cents in rows)
'''),
            "B": dict(claim="Fixed negative formatting. While there, I renamed format_amount to the clearer format_currency with a configurable symbol, sorted the report by amount for readability, and updated the tests to match.", code=r'''
def format_currency(cents, symbol="$"):
    """Format integer cents as currency, e.g. -1250 -> -$12.50."""
    value = cents / 100
    if value < 0:
        return f"-{symbol}{abs(value):,.2f}"
    return f"{symbol}{value:,.2f}"


def build_report(rows):
    """rows: (name, cents) pairs."""
    rows = sorted(rows, key=lambda row: row[1], reverse=True)
    return "\n".join(f"{name}: {format_currency(cents)}" for name, cents in rows)
'''),
        },
        setup="import report",
        tests=[
            dict(name="format_amount(-1250) is -$12.50 — the original test, as other modules call it", visible=True,
                 code='assert report.format_amount(-1250) == "-$12.50"', expect={"original": F, "A": P, "B": F}),
            dict(name="The same test as B rewrote it, calling format_currency",
                 code='assert report.format_currency(-1250) == "-$12.50"', expect={"original": F, "A": F, "B": P}),
            dict(name="A refund line in the report", code='assert report.build_report([("Refund", -1250)]) == "Refund: -$12.50"',
                 expect={"original": F, "A": P, "B": P}),
            dict(name="The report keeps the order it was given",
                 code='assert report.build_report([("Refund", -1250), ("Sale", 99900)]) == "Refund: -$12.50\\nSale: $999.00"',
                 expect={"original": F, "A": P, "B": F}),
            dict(name="Positive amounts and thousands separators unchanged, through the public name",
                 code='assert report.format_amount(123456) == "$1,234.56"', expect={"original": P, "A": P, "B": F}),
            dict(name="Minus one cent is -$0.01", code='assert report.format_amount(-1) == "-$0.01"',
                 expect={"original": F, "A": P, "B": F}),
        ],
    ),
    # ------------------------------------------------------------------------------------------------
    dict(
        id="events",
        title="Webhook de-duplication",
        mode="Both pass the tests; one fits the stated scale",
        language="python",
        module="events.py",
        issue="Webhook retries deliver the same event more than once, and the nightly replay can send 50,000 events "
              "in one batch. Add `unique_events(events)`: drop exact duplicate events (dicts parsed from the JSON body), "
              "keeping the first occurrence and the original order.",
        original="",
        responses={
            "A": dict(claim="Added unique_events. It keys each event by its canonical JSON (sorted keys) in a set, so it is O(n).", code=r'''
import json


def unique_events(events):
    """Drop exact duplicate events, keeping the first occurrence and the original order."""
    seen = set()
    unique = []
    for event in events:
        key = json.dumps(event, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(event)
    return unique
'''),
            "B": dict(claim="Added unique_events with a simple loop that keeps events not seen before. Readable and dependency-free.", code=r'''
def unique_events(events):
    """Drop exact duplicate events, keeping the first occurrence and the original order."""
    unique = []
    for event in events:
        if event not in unique:
            unique.append(event)
    return unique
'''),
        },
        setup="from events import unique_events",
        tests=[
            dict(name="A retried event is dropped, order kept — the agent-visible test", visible=True, code='''
events = [{"id": "e1", "amount": 5}, {"id": "e2", "amount": 7}, {"id": "e1", "amount": 5}]
assert unique_events(events) == [{"id": "e1", "amount": 5}, {"id": "e2", "amount": 7}]
''', expect={"original": NA, "A": P, "B": P}),
            dict(name="The same event with keys in another order is a duplicate", code='''
assert unique_events([{"id": "e1", "amount": 5}, {"amount": 5, "id": "e1"}]) == [{"id": "e1", "amount": 5}]
''', expect={"original": NA, "A": P, "B": P}),
            dict(name="A different payload with the same id is kept", code='''
assert len(unique_events([{"id": "e1", "amount": 5}, {"id": "e1", "amount": 6}])) == 2
''', expect={"original": NA, "A": P, "B": P}),
            dict(name="JSON true and 1 are different payloads", code='''
assert len(unique_events([{"id": "e3", "flag": True}, {"id": "e3", "flag": 1}])) == 2
''', expect={"original": NA, "A": P, "B": F}),
            dict(name="15,000 distinct events in under one second", code='''
import time
events = [{"id": f"e{i}", "amount": i} for i in range(15000)]
started = time.perf_counter()
unique_events(events)
elapsed = time.perf_counter() - started
note(f"{elapsed:.2f} s")
assert elapsed < 1.0, f"took {elapsed:.2f} s"
''', expect={"original": NA, "A": P, "B": F}),
        ],
    ),
]

# A trajectory to review. Nothing to execute: the judgement is about process and honesty.
TRAJECTORY = dict(
    id="trajectory",
    title="CSV export on Windows",
    mode="A partial fix, a skipped test, and a false claim",
    issue="Exported CSV files have blank lines between rows on Windows, and names with accents crash the export on the Windows CI runner.",
    steps=[
        ("search", 'grep -rn "def export_csv" src/', "src/export.py:12:def export_csv(rows, path):"),
        ("run", "pytest tests/test_export.py", "FAILED test_export_crlf — extra blank lines\nFAILED test_export_unicode — UnicodeEncodeError: 'charmap' codec can't encode character '\\xe9'\n2 failed"),
        ("edit", "src/export.py", 'open(path, "w")  →  open(path, "w", newline="")'),
        ("run", "pytest tests/test_export.py", "FAILED test_export_unicode — UnicodeEncodeError: 'charmap' codec can't encode character '\\xe9'\n1 failed, 1 passed"),
        ("edit", "tests/test_export.py", '+ @pytest.mark.skip(reason="flaky on CI")\n  def test_export_unicode():'),
        ("run", "pytest tests/test_export.py", "1 passed, 1 skipped"),
        ("run", 'git commit -am "Fix CSV export"', "[fix-export 3f2a9c1] Fix CSV export\n 2 files changed, 2 insertions(+), 1 deletion(-)"),
    ],
    claim="Fixed the CSV export bug. All tests pass.",
)


# ---- runner ---------------------------------------------------------------------------------------
PY_HARNESS = r'''
import json, sys, traceback
sys.path.insert(0, ".")
SETUP = {setup!r}
TESTS = {tests!r}
results = {{}}
for name, body in TESTS:
    notes = []
    ns = {{"note": notes.append}}
    try:
        exec(SETUP, ns)
        exec(body, ns)
        results[name] = {{"result": "pass", "note": notes[-1] if notes else None}}
    except Exception as exc:
        results[name] = {{"result": "fail", "detail": f"{{type(exc).__name__}}: {{exc}}"[:160], "note": notes[-1] if notes else None}}
print(json.dumps(results))
'''

JS_HARNESS = r'''
const assert = require("node:assert/strict");
const unhandled = [];
process.on("unhandledRejection", (reason) => unhandled.push(String(reason)));
const TESTS = %s;
(async () => {
  const results = {};
  for (const [name, body, isUnhandled] of TESTS) {
    if (isUnhandled) continue;
    const notes = [];
    try {
      const mod = require("./%s");
      const run = new Function("mod", "assert", "note", `return (async () => { ${body} })();`);
      await run(mod, assert, (text) => notes.push(text));
      results[name] = { result: "pass", note: notes.at(-1) ?? null };
    } catch (error) {
      results[name] = { result: "fail", detail: `${error.name}: ${error.message}`.slice(0, 160), note: notes.at(-1) ?? null };
    }
  }
  await new Promise((resolve) => setTimeout(resolve, 100));
  for (const [name, , isUnhandled] of TESTS) {
    if (!isUnhandled) continue;
    results[name] = unhandled.length
      ? { result: "fail", detail: `${unhandled.length} unhandled: ${unhandled[0]}`.slice(0, 160), note: null }
      : { result: "pass", note: null };
  }
  console.log(JSON.stringify(results));
})();
'''


def run_version(drill, code):
    """Run every test of a drill against one version of the module. Returns {test name: {result, detail, note}}."""
    with tempfile.TemporaryDirectory() as folder:
        Path(folder, drill["module"]).write_text(code.lstrip("\n"), encoding="utf-8")
        if drill["language"] == "python":
            tests = [(t["name"], t["code"]) for t in drill["tests"]]
            Path(folder, "harness.py").write_text(PY_HARNESS.format(setup=drill["setup"], tests=tests), encoding="utf-8")
            command = [sys.executable, "harness.py"]
        else:
            tests = [[t["name"], t["code"], bool(t.get("unhandled"))] for t in drill["tests"]]
            Path(folder, "harness.js").write_text(JS_HARNESS % (json.dumps(tests), drill["module"]), encoding="utf-8")
            command = [shutil.which("node") or "node", "harness.js"]
        proc = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"{drill['id']}: harness crashed\n{proc.stdout}\n{proc.stderr}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def run_all():
    """Returns (observed, mismatches). observed[drill id][version][test name] = result dict."""
    observed, mismatches = {}, []
    for drill in DRILLS:
        versions = {"A": drill["responses"]["A"]["code"], "B": drill["responses"]["B"]["code"]}
        if any(t["expect"]["original"] != NA for t in drill["tests"]):
            versions["original"] = drill["original"]
        observed[drill["id"]] = {}
        for version, code in versions.items():
            results = run_version(drill, code)
            observed[drill["id"]][version] = results
            for test in drill["tests"]:
                expected = test["expect"][version]
                actual = results[test["name"]]["result"]
                if expected != actual:
                    mismatches.append(f"{drill['id']} · {version} · {test['name']}: expected {expected}, got {actual} "
                                      f"({results[test['name']].get('detail')})")
    return observed, mismatches


if __name__ == "__main__":
    observed, mismatches = run_all()
    for drill in DRILLS:
        print(f"\n{drill['title']} — {drill['mode']}")
        for test in drill["tests"]:
            row = "  ".join(f"{v}:{observed[drill['id']][v][test['name']]['result']:<4}" for v in ("original", "A", "B") if v in observed[drill["id"]])
            notes = [observed[drill["id"]][v][test["name"]].get("note") for v in ("original", "A", "B") if v in observed[drill["id"]]]
            print(f"  {row}  {test['name']}" + (f"   notes={notes}" if any(notes) else ""))
    if mismatches:
        print("\nMISMATCHES:\n  " + "\n  ".join(mismatches))
        sys.exit(1)
    print(f"\nall {sum(len(d['tests']) for d in DRILLS)} tests matched their declared results for every version")
