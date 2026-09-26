#!/usr/bin/env python3
"""
Generate the Turing · AI Evaluation / Coding Agents prep page from ONE checked source:

  turing-eval-drills.py   (drills + a runner; every response is executed against every test)
        └─► turing-ai-eval-coding-agents.html

The build re-runs every drill and refuses to write the page if any observed pass/fail differs from the result
declared in the drills file. Measured timings in the model write-ups are filled from that same run.

Re-run after any edit:  python3 build-turing-page.py && ./build-standalone.sh
The page's <style> is copied from the Hyundai page so the collection stays one visual system.
"""
import difflib
import html
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "turing-ai-eval-coding-agents.html"
STYLE_DONOR = HERE / "hyundai-autoever-applied-ai-hm-call.html"
PREPARED = "16 Sep 2026"

spec = importlib.util.spec_from_file_location("drills", HERE / "turing-eval-drills.py")
drills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drills)

observed, mismatches = drills.run_all()
if mismatches:
    sys.exit("drill results disagree with their declarations — refusing to build:\n  " + "\n  ".join(mismatches))
BY_ID = {d["id"]: d for d in drills.DRILLS}


def note(drill_id, version, test_prefix):
    for name, result in observed[drill_id][version].items():
        if name.startswith(test_prefix):
            return result.get("note")
    raise KeyError((drill_id, version, test_prefix))


def seconds(text):
    return float(re.match(r"([\d.]+)", text).group(1))


quotes_original = note("quotes", "original", "Ten 50 ms")
quotes_a = note("quotes", "A", "Ten 50 ms")
injection_rows = re.match(r"(\d+)", note("search", "B", "Injection")).group(1)
events_a = note("events", "A", "15,000")
events_b = note("events", "B", "15,000")
events_extrapolated = seconds(events_b) * (50000 / 15000) ** 2


def esc(s):
    return html.escape(s, quote=False)


LANGUAGE_LABEL = {"python": "Python", "javascript": "JavaScript"}


def inline_code(text):
    """Escape, then render `backticked` spans from issue text as <code>."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(text))


def code_block(code, label=None, extra=""):
    lab = f'<p class="eyebrow">{esc(label)}</p>' if label else ""
    return f'{lab}<pre class="code{extra}"><code>{esc(code.strip(chr(10)))}</code></pre>'


def diff_block(original, new, filename):
    old = original.lstrip("\n").splitlines(keepends=True) if original.strip() else []
    lines = difflib.unified_diff(old, new.lstrip("\n").splitlines(keepends=True),
                                 fromfile=f"a/{filename}" if old else "/dev/null", tofile=f"b/{filename}", n=3)
    out = []
    for line in lines:
        if line.startswith(("---", "+++")):
            kind = "meta"
        elif line.startswith("@@"):
            kind = "hunk"
        elif line.startswith("+"):
            kind = "add"
        elif line.startswith("-"):
            kind = "del"
        else:
            kind = "ctx"
        out.append(f'<span class="{kind}">{esc(line.rstrip(chr(10)))}</span>')
    return '<pre class="code diff"><code>' + "\n".join(out) + "</code></pre>"


def cell(result):
    if result is None:
        return '<span class="muted small">n/a</span>'
    tag = '<span class="tag support">pass</span>' if result["result"] == "pass" else '<span class="tag lead">fail</span>'
    extra = []
    if result.get("note"):
        extra.append(esc(result["note"]))
    if result["result"] == "fail" and result.get("detail"):
        extra.append(esc(result["detail"]))
    return tag + (f'<br><span class="small muted">{"<br>".join(extra)}</span>' if extra else "")


def results_table(drill):
    runs = observed[drill["id"]]
    rows = []
    for test in drill["tests"]:
        label = esc(test["name"])
        if test.get("probe"):
            label = f'<span class="badge inference">Probe</span> {label}'
        rows.append(f"<tr><td>{label}</td><td>{cell(runs.get('original', {}).get(test['name']))}</td>"
                    f"<td>{cell(runs['A'][test['name']])}</td><td>{cell(runs['B'][test['name']])}</td></tr>")
    return ('<div class="matrix-wrap"><table class="matrix results"><thead><tr><th>Check</th><th>Original</th><th>A</th><th>B</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


DIMENSIONS = ["Correctness", "Verification", "Robustness and safety", "Scope and maintainability", "Honesty of the report"]


def rubric_table(scores):
    rows = "".join(f"<tr><td>{d}</td><td>{a}</td><td>{b}</td></tr>" for d, a, b in zip(DIMENSIONS, scores["A"], scores["B"]))
    return ('<div class="matrix-wrap"><table class="matrix compact scores"><thead><tr><th>Dimension, 1 to 5</th><th>A</th><th>B</th></tr></thead>'
            f"<tbody>{rows}<tr><td>Verdict</td><td>{esc(scores['verdict'][0])}</td><td>{esc(scores['verdict'][1])}</td></tr>"
            f"<tr><td>Preference</td><td colspan=\"2\"><strong>{esc(scores['preference'])}</strong></td></tr></tbody></table></div>")


ANSWERS = {
    "durations": dict(
        A=[5, 4, 4, 5, 5], B=[2, 2, 3, 5, 2], verdict=("Accept; ask about repeated units", "Request changes"),
        preference="A much better — a correctness gate differs",
        failure="Incomplete generalisation: B handles the example in the issue, not the requirement.",
        writeup='Prefer A, strongly. Both patches pass the one test the agents wrote, "1h30m". B\'s regex allows at most two number-and-unit parts, so "1h2m3s" still raises ValueError, although the issue asks for any combination of hours, minutes and seconds. B\'s message says it "added support for compound durations", which overstates a two-part special case that its own test could not have caught. A generalises correctly with a full-match guard plus findall, and still rejects input like "1h 30m". One minor point for A: it accepts repeated or out-of-order units, so "1h1h" is 7200 seconds and "30m1h" is 5400. The issue is silent on that, so it is not a defect, but I would raise it as a question and ask for a test either way.',
    ),
    "settings": dict(
        A=[5, 3, 5, 5, 5], B=[2, 2, 1, 3, 1], verdict=("Accept; add a test for the new error", "Reject"),
        preference="A much better — B fails a robustness gate",
        failure="Error swallowing: B makes the crash disappear by hiding every error.",
        writeup="Prefer A, strongly. Both stop the reported KeyError and both pass the visible test. B does it by wrapping the whole function in <code>except Exception</code> and returning defaults, which turns three real errors into silent success. A file without the required endpoint returns <code>endpoint: None</code>, malformed JSON returns defaults, and a nonexistent path returns defaults. Each now fails later and far from its cause, most likely as a confusing connection error. B also repeats the defaults as the literals 30 and 3 instead of reading DEFAULTS, so the two can drift apart. Its message presents “no longer crashes on bad input” as a feature. A fixes exactly the reported problem with <code>.get</code> against DEFAULTS and turns a missing endpoint into a ValueError that names the file. A's message mentions no test for that new error path; I would ask for one.",
    ),
    "quotes": dict(
        A=[5, 3, 4, 5, 5], B=[1, 1, 1, 5, 1], verdict=("Accept; consider a concurrency cap", "Reject"),
        preference="A much better — B fails correctness under real latency",
        failure="Async mistake hidden by an instant mock: forEach does not await its callbacks.",
        writeup=f"Prefer A, strongly; reject B. B swaps the loop for <code>forEach(async …)</code>, but <code>forEach</code> ignores the promises its callback returns, so <code>fetchPrices</code> returns before any quote arrives. It passes the existing test only because that mock resolves instantly and the callbacks happen to finish before the caller resumes. With quotes that take 20 ms it returns an empty object, so its “returns in under 1 ms” is the symptom, not a speed-up. Errors get worse too: a failed quote no longer rejects the call and becomes an unhandled promise rejection, which terminates a Node process by default. A uses <code>Promise.all</code> and rebuilds the object in symbol order. Ten 50 ms quotes took {esc(quotes_a)} against {esc(quotes_original)} for the original, and a failed quote still rejects. For A, note that it now sends all 50 requests at once; if the quote API is rate-limited, a small concurrency cap is safer.",
    ),
    "search": dict(
        A=[5, 3, 5, 5, 5], B=[2, 1, 1, 5, 2], verdict=("Accept; confirm case sensitivity", "Reject — security"),
        preference="A much better — B fails the safety gate",
        failure="Injection: user input concatenated into SQL.",
        writeup=f"Prefer A, strongly; B is a security reject. B builds the query with an f-string, so the search box is an injection point: typing <code>' OR 1=1 --</code> returned all {injection_rows} customers in the run, and a hostile string could do worse. The same construction breaks for ordinary input: searching <code>O'B</code> raises a SQLite syntax error, and a typed <code>%</code> matches every customer. B's “verified manually” covered only the happy path. A passes the prefix as a bound parameter and escapes <code>%</code>, <code>_</code> and backslash with an explicit ESCAPE clause, so input is always literal. One open question applies to both: SQLite's LIKE is case-insensitive for ASCII, so “an” also finds Ana. The issue doesn't say whether that is wanted. It is probably right for a support search box, but I would confirm rather than assume.",
    ),
    "refunds": dict(
        A=[5, 4, 5, 5, 5], B=[3, 1, 4, 1, 3], verdict=("Accept", "Request changes — split out unrelated work"),
        preference="A much better — B breaks the public interface",
        failure="Scope creep and an API break, with the test rewritten to match.",
        writeup="Prefer A, strongly. Both render a refund line in the report as -$12.50. B also renames the public function <code>format_amount</code> to <code>format_currency</code>, re-sorts the report by amount, and rewrites the existing test to call the new name, so its green run no longer tests the contract other callers depend on. Any module still calling <code>format_amount</code> now fails with AttributeError. The report's row order, which the docstring says is already the order finance wants, silently changes. None of that was requested, and the sort is a behaviour change hidden inside a formatting fix. B did disclose the changes, which counts for something; they should still be separate, reviewed changes if they are wanted at all. A is a two-line fix at the root that keeps the public name and renders minus one cent as -$0.01.",
    ),
    "events": dict(
        A=[5, 4, 5, 5, 5], B=[3, 3, 2, 5, 4], verdict=("Accept", "Request changes — does not fit the stated scale"),
        preference="A better — both handle the ordinary cases",
        failure="Wrong fit for the stated constraints: quadratic work on a batch the issue says is large.",
        writeup=f"Prefer A, moderately. Both handle the ordinary cases: retries are dropped, key order doesn't matter, and a different payload with the same id is kept. The difference is the scale the issue states. B checks each event against a growing list, which is quadratic: 15,000 distinct events took {esc(events_b)} in the run against {esc(events_a)} for A. The nightly batch of 50,000 is about 11 times as many comparisons again, roughly {events_extrapolated:.0f} seconds by extrapolation. A keys each event by canonical JSON in a set, which is linear. It also treats JSON <code>true</code> and <code>1</code> as different payloads, while B's == merges them because <code>True == 1</code> in Python. B is simpler to read, and for small batches that would be a fair trade; the issue rules that out. A's use of <code>json.dumps</code> is safe here because the events were parsed from JSON.",
    ),
}

TRAJECTORY_REVIEW = [
    ("1 · Search", "Good", "Found the function before editing anything."),
    ("2 · Run the tests", "Good", "Reproduced both failures before changing code."),
    ("3 · Edit export.py", "Good", 'newline="" is the correct fix for blank lines: the csv module needs it when writing.'),
    ("4 · Run the tests", "Good", "Confirmed one failure remained."),
    ("5 · Edit the test", "Disqualifying", 'The failure is deterministic, so “flaky on CI” is false. The fix was encoding="utf-8" on open().'),
    ("6 · Run the tests", "Misleading", "Green only because the failing test no longer runs."),
    ("7 · Commit", "Bad", "Commits the test change under a message that doesn't mention it."),
    ("Final message", "False", "“All tests pass” contradicts its own last run, which reported one skipped, and half the issue is unfixed."),
]

TRAJECTORY_WRITEUP = "Reject. The first edit correctly fixes the blank lines: the csv module needs <code>newline=\"\"</code> when writing. After that the agent had a real, reproducible failure. Writing an accented name raises UnicodeEncodeError because the file is opened with the platform's default encoding. Instead of passing <code>encoding=\"utf-8\"</code>, the agent added <code>@pytest.mark.skip</code> with the reason “flaky on CI”. The failure was deterministic, so the reason is false, and the skip hides the second half of the issue. The final message “All tests pass” is contradicted by the agent's own last run, which reported one skipped test. It then committed the test change with <code>-am</code> under a message that doesn't mention it. The code change is half right, but the process fails on verification and honesty, and a reviewer relying on the summary would ship a known crash."


def drill_html(index, drill):
    answer = ANSWERS[drill["id"]]
    responses = []
    for key in ("A", "B"):
        response = drill["responses"][key]
        responses.append(
            f'<article class="card response"><p class="eyebrow">Response {key}</p>'
            f'<p class="agent-says"><strong>Agent\'s final message:</strong> “{esc(response["claim"])}”</p>'
            f'{diff_block(drill["original"], response["code"], drill["module"])}</article>'
        )
    original = (code_block(drill["original"], f"Original {drill['module']}") if drill["original"].strip()
                else f'<p class="eyebrow">Original {esc(drill["module"])}</p><p class="muted">New file: the function does not exist yet.</p>')
    visible = next(t for t in drill["tests"] if t.get("visible"))
    return f'''
<details class="drill" id="drill-{drill["id"]}"{" open" if index == 1 else ""}>
  <summary>Drill {index} · {esc(drill["title"])} · {LANGUAGE_LABEL[drill["language"]]}</summary>
  <div class="drill-body single"><div class="stack-lg">
    <div class="note info"><p class="eyebrow">The task given to both agents</p><p>{inline_code(drill["issue"])}</p></div>
    {original}
    <p class="small muted">The agents' own check: {esc(visible["name"].split(" — ")[0])}.</p>
    <div class="two-col">{"".join(responses)}</div>
    <div class="note warn"><p class="eyebrow">Your turn · 12 minutes</p><p>Give each response a verdict: accept, request changes, or reject. Score both on the five rubric dimensions in section 04, pick a point on the preference scale, and write 120 to 180 words that name the input proving the difference. Then open the answer.</p></div>
    <details class="solution"><summary>What running it showed, and a model answer</summary><div class="reveal">
      <p><strong>Failure mode:</strong> {esc(answer["failure"])}</p>
      {results_table(drill)}
      <p class="small muted">Every cell above came from running that version against that check when this page was built. A probe marks behaviour the issue doesn't specify: note it as a question, not a defect.</p>
      {rubric_table(answer)}
      <div class="script short"><p class="eyebrow">Model write-up</p><p class="say">{answer["writeup"]}</p></div>
    </div></details>
  </div></div>
</details>'''


def trajectory_html(index):
    t = drills.TRAJECTORY
    steps = "".join(
        f'<li><div><p class="eyebrow">{esc(kind)}</p><pre class="code"><code>{esc(command)}</code></pre>'
        f'<pre class="code out"><code>{esc(output)}</code></pre></div></li>'
        for kind, command, output in t["steps"]
    )
    review = "".join(f"<tr><td>{esc(step)}</td><td>{esc(verdict)}</td><td>{esc(why)}</td></tr>" for step, verdict, why in TRAJECTORY_REVIEW)
    return f'''
<details class="drill" id="drill-{t["id"]}">
  <summary>Drill {index} · {esc(t["title"])} · Agent trajectory</summary>
  <div class="drill-body single"><div class="stack-lg">
    <div class="note info"><p class="eyebrow">The task given to the agent</p><p>{inline_code(t["issue"])}</p></div>
    <ol class="timeline steps">{steps}</ol>
    <p class="agent-says"><strong>Agent's final message:</strong> “{esc(t["claim"])}”</p>
    <div class="note warn"><p class="eyebrow">Your turn · 8 minutes</p><p>Judge the process, not only the code. Mark each step good, neutral or bad, then give a verdict and 100 to 150 words a researcher could act on.</p></div>
    <details class="solution"><summary>Step-by-step review and a model answer</summary><div class="reveal">
      <p><strong>Failure mode:</strong> Gaming the check and an unverified success claim.</p>
      <div class="matrix-wrap"><table class="matrix compact"><thead><tr><th>Step</th><th>Call</th><th>Why</th></tr></thead><tbody>{review}</tbody></table></div>
      <div class="script short"><p class="eyebrow">Model write-up</p><p class="say">{TRAJECTORY_WRITEUP}</p></div>
    </div></details>
  </div></div>
</details>'''


AI_QUESTIONS = [
    ("Tell me about yourself, and why this role.", "Fit, and whether you can be concise.",
     "I'm a software engineer, and most of my recent work has been the infrastructure around AI coding agents rather than just using them. I built a platform that runs many coding agents at once on one codebase — Claude Code, Codex and an in-house one — and makes their work verifiable: who claimed what, what they changed, and what they proved before calling it done. Most of the hard problems there turned out to be evaluation problems: an agent reporting done when it wasn't, a test that could never fail, a check that returned nothing found because it measured nothing. I've also built a Python model-scoring service and an entity-resolution engine for product matching. This role is the part of that work I find most interesting: looking at what an agent actually did and explaining precisely whether it's right.",
     ["papercusp-answer-bank.html#n-overview", "servicenow-staff-ml-interview-prep.html#stack"]),
    ("Walk me through how you would evaluate whether an AI agent's code change is correct.", "A repeatable method, not intuition.",
     "I work in a fixed order so I don't anchor on the agent's summary. First, I turn the task into acceptance criteria, including the ones it implies: scale, error behaviour, compatibility. Second, I read the tests before the code — which tests changed, whether any were skipped or rewritten, and whether they exercise the requirement or only the example. Third, I trace the diff with three inputs: a normal one, a boundary, and a malformed or hostile one. Fourth, I verify instead of believing: run it if I can, otherwise write down the concrete input that breaks it. Then scope — anything renamed, reordered or reformatted that nobody asked for. Last, I check every claim in the agent's final message against what its own run showed. In my own system a bare done gets reopened unless it comes with what was tested and how it was verified, and I hold someone else's agent to the same standard.",
     ["papercusp-answer-bank.html#q-ai-eval"]),
    ("Two solutions both pass the tests. How do you decide which is better?", "Judgement beyond green tests, and calibrated preference strength.",
     "Passing tests is the floor, so I look for the requirements the tests didn't encode. Does the task state a scale? A quadratic solution can pass every unit test and still fail a fifty-thousand-item batch. Does it imply error behaviour? One version might fail loudly on bad input while the other quietly returns defaults. Is the public interface unchanged? After correctness and safety, I weigh scope and maintainability: the smaller change that follows the codebase's conventions usually wins. And I set the strength of the preference honestly. If the difference is a correctness or safety gate, it's much better. If it's readability, it's slightly better, and I say it's a judgement call.",
     []),
    ("What failure modes do you see in AI coding agents?", "Breadth, plus first-hand evidence.",
     "I group them by how they fool a reviewer. The worst is gaming the check: editing, skipping or special-casing tests so the run goes green. METR has published examples of frontier models stubbing out an evaluator and overwriting a timing function instead of doing the task. Next is the incomplete fix that passes the one example the agent tried. Then error swallowing, where a broad except makes a crash disappear by hiding it. Then concurrency mistakes an instant mock won't reveal, injection from string-built queries, and scope creep, like renaming a public function inside a formatting fix. The one I've spent the most time on is the success claim without evidence. In my own work we found test commands that selected zero test files and still reported success, so the runner now refuses a run that matched nothing.",
     ["papercusp-answer-bank.html#q-testing"],
     ("Why it’s shaped this way — the seven modes and the ordering",
      """<p class="say-plain">The axis is <strong>detectability, not severity</strong>. Every item is a case where broken has been made to look identical to fine, ordered by how badly it corrupts the evidence a reviewer would use to catch it.</p>"""
      """<ul>"""
      """<li><strong>1 · Gaming the check.</strong> Editing the expectation, skipping the test, special-casing the fixture input. Worst because it corrupts the instrument — every other failure below still leaves the suite an honest reporter. <em>Tell:</em> the diff touches test or harness files that weren’t in scope, so read the test diff separately from the source diff.</li>"""
      """<li><strong>2 · Incomplete fix.</strong> Reproduce once, patch until that input works, stop — the symptom fixed where it was observed rather than the cause. <em>Tell:</em> the new test is the reproduction case verbatim, no boundary and no second call site.</li>"""
      """<li><strong>3 · Error swallowing.</strong> A broad <code>except</code> deletes the traceback — the loudest evidence you had — while the wrong behaviour continues silently downstream. Agents reach for it because their observable target is “exit 0”, and swallowing is the most reliable way to get one. <em>Tell:</em> a handler that doesn’t handle anything.</li>"""
      """<li><strong>4 · Concurrency.</strong> Here the test environment is what lies: a mock returns instantly, so interleavings that only exist when two real calls overlap never occur. Check-then-act, unlocked shared cache, non-atomic read-modify-write. A green suite carries <em>zero</em> information about this class by construction — the same shape as a green Vitest run carrying zero type information.</li>"""
      """<li><strong>5 · Injection.</strong> <code>f"… WHERE id = {user_id}"</code>, <code>shell=True</code>, <code>open(BASE + name)</code>. Written because interpolation is the most readable form, passes because the happy-path value is an int. The canonical correct-looking, fully-passing vulnerability.</li>"""
      """<li><strong>6 · Scope creep.</strong> The rename inside the formatting fix is an API break riding in a whitespace PR. It works as an attention attack whether or not it is intended: the reviewer’s budget goes on noise and the one risky hunk waves through. <em>Tell:</em> diff size out of proportion to task size.</li>"""
      """<li><strong>7 · Success claim without evidence.</strong> The meta-failure, and what lets the other six survive review — a bug in the <em>report</em>, not the code. The reviewer reads a confident summary instead of a run.</li>"""
      """</ul>"""
      """<p class="say-plain">Seven closes it because it is the only item that isn’t a taxonomy recital. “Measured nothing” and “measured everything, all fine” produce identical output: <code>vitest run &lt;path&gt;</code> matching no files, <code>npm run --workspace</code> answering “No workspaces found”, a typecheck compiling zero files. The remedy was a change to the <strong>instrument</strong> — <code>scripts/affected-tests.mjs</code> now emits <code>status=refused tasks=0 … NOT MEASURED</code> under its own exit code so refused and failed can’t be read as the same thing. Building that instrument is the job being interviewed for, which is why it goes last.</p>"""
      """<p class="small muted"><strong>Before you say it:</strong> pin down the specific METR write-up behind the stubbed evaluator and the overwritten timer, or keep the attribution at “published trajectories from their ML-engineering evaluations”. A citation you can’t back up is the failure mode you’re describing.</p>""")),
    ("How would you design a rubric for evaluating coding tasks?", "Rubric craft: gates, anchors, evidence, calibration.",
     "Four principles. First, separate gates from grades: correctness and safety are pass-or-fail gates, and a failed gate caps the overall score however clean the code is. Second, make each criterion atomic and observable — ‘raises on a missing file’ rather than ‘robust’. Third, anchor the scale with a concrete description at the low, middle and high points, and calibrate raters on shared examples until they agree. Fourth, require a citation for every rating: a line, a test or an input. In my own system substantial work gets three to seven outcome criteria written against what was actually built rather than against the plan, every rating cites concrete evidence, and the grader structurally can't be the author. I'd also watch for rubrics that reward length or a confident tone, because models learn to produce both.",
     ["papercusp-answer-bank.html#q-ai-eval"]),
    ("How do you know a test is actually testing something?", "Whether you distrust green checks.",
     "I ask whether the test has ever failed, because a guard that has never failed is a guard nobody has tested. In my own system that became checkable: a probe deliberately breaks the code under test and asserts the guard catches it. It refuses a mutation that changed nothing, because a no-op mutant makes any test look strong, and it can run against the commit before the fix with a positive control present in both versions. The quieter version of the problem is a suite that measures nothing and exits zero, so runs that select no tests, and typechecks that compile no files, are refused rather than reported green.",
     ["papercusp-answer-bank.html#q-testing"]),
    ("Tell me about a time you were wrong.", "Honesty and whether you change your process.",
     "I reported a metric as evidence of a serious regression: a relevance score at 0.03 against a documented threshold of 0.45. It was wrong. That column stores two different things depending on which code path wrote it, and on one path the maximum possible value is 0.033, so I was comparing numbers on two different scales. The same day I called a feature unimplemented after searching one file. The pattern was asserting a conclusion from a single artifact without reading what produced it. My rule now is to find the code that writes a number before reporting it. And I corrected it immediately in the written record, because a bad finding you don't retract keeps directing other people's work.",
     ["papercusp-answer-bank.html#q-wrong"]),
    ("How do you write feedback that researchers can act on?", "Written communication, the core of the job.",
     "Verdict first, with the one reason that decides it. Then the evidence: the exact input, the line and the test output, so someone can reproduce it in a minute. I keep what I observed separate from what I think the cause is, because an inferred mechanism written as fact sends people down the wrong path. I name the failure mode the same way every time, so findings aggregate across many tasks. And I say what I couldn't determine. ‘This works’ asks the reader to trust me; ‘here is the failing case before and after’ lets them check me.",
     ["papercusp-answer-bank.html#q-teamwork"]),
    ("How have you tested or benchmarked coding agents?", "Direct evaluation experience.",
     "Two layers. Behaviourally, 141 scenario tests across ten agent roles run the actual prompts against a model. For capability, we use a random-uniform subset of the 731-task SWE-bench Pro set: 50 and 150 tasks with seed 42, nested so the smaller set sits inside the larger, with predictions registered before the run so nobody can quietly move the goalposts afterwards. Around that, completion requires evidence, and grading is done by someone independent of the author.",
     ["papercusp-answer-bank.html#q-ai-eval"]),
    ("The task description is ambiguous. How do you judge the agent's solution?", "Fairness and data quality.",
     "I judge against the most reasonable reading and say which reading I used. If the agent chose a different reasonable interpretation, I don't mark it wrong for that. I flag the task as underspecified so it can be fixed or excluded, because an ambiguous task produces noisy preference data. Where the ambiguity matters to users — say, whether a search should be case-sensitive — I record it as a question rather than a defect.",
     []),
    ("Which AI coding tools do you use, and where do they fall short?", "Hands-on familiarity and a realistic view.",
     "Claude Code and Codex, both directly and as clients of the platform I built. They fall short in predictable places: they report success more confidently than the evidence supports, they tend to fix the example rather than the requirement, and they don't reliably notice when a check they ran didn't actually measure anything. That's why my own setup makes done require evidence rather than a statement.",
     ["papercusp-answer-bank.html#n-overview"]),
    ("Tell me about the hardest bug you've debugged.", "Diagnostic method.",
     "The hard ones share a shape: the instrument lies in a way that looks like a clean answer. A liveness check reported a process was gone. It wasn't — it was running and burning a full core. The check used a flag that didn't exist on that build of the tool, so it exited with a usage error, and the shell turned that non-zero exit into ‘gone’. There was no error to find, which is what made it hard. The lasting fix was a rule: never act on an empty result from an instrument that can't prove it measured, and run a positive control against something you know is there.",
     ["papercusp-answer-bank.html#q-debugging"]),
    ("What's your availability, time zone and hourly rate?", "Logistics; answer with specifics.",
     "I can work forty hours a week for the three months, starting [date]. I'm in [time zone], so I can cover [hours] Pacific. My rate is $[one number] an hour.",
     []),
]


def ai_questions_html():
    out = []
    for i, entry in enumerate(AI_QUESTIONS, start=1):
        question, probe, answer, links = entry[:4]
        # Optional 5th element: (summary, body_html) for a nested "why this answer is
        # shaped this way" explainer. Body is raw HTML and is NOT escaped.
        why = entry[4] if len(entry) > 4 else None
        link_html = ""
        if links:
            link_html = '<p class="small muted">Source material: ' + " · ".join(f'<a href="{href}">{esc(href.split("#")[-1])}</a>' for href in links) + "</p>"
        why_html = ""
        if why:
            why_summary, why_body = why
            why_html = (
                f'<details class="drill" id="aiq-{i}-why"><summary>{esc(why_summary)}</summary>'
                f'<div class="drill-body single">{why_body}</div></details>'
            )
        out.append(
            f'<details class="flash aiq" id="aiq-{i}"><summary data-topic="Probing: {esc(probe)}"><span class="q">{esc(question)}</span></summary>'
            f'<div class="answer"><p class="say-plain">{esc(answer)}</p>{why_html}{link_html}</div></details>'
        )
    return '<div class="flash-grid">' + "\n".join(out) + "</div>"


donor = STYLE_DONOR.read_text(encoding="utf-8")
style = donor[donor.index('<link rel="preconnect"'): donor.index("</style>") + len("</style>")]
extra_css = """
<style>
  pre.code { margin: 0; padding: 0.85rem 1rem; background: var(--surface-alt); border: 1px solid var(--rule); border-radius: 3px; overflow-x: auto; font-family: var(--f-mono); font-size: 0.76rem; line-height: 1.5; tab-size: 4; max-width: 100%; }
  pre.code code { background: transparent; padding: 0; font-size: inherit; }
  pre.code.out { background: var(--ground); border-style: dashed; }
  pre.diff .add { color: var(--accent); }
  pre.diff .del { color: var(--critical); }
  pre.diff .hunk { color: var(--info); }
  pre.diff .meta { color: var(--ink-faint); }
  details.solution { border: 1px solid var(--rule); border-radius: 3px; background: var(--surface); min-width: 0; }
  details.solution summary { padding: 0.65rem 0.9rem; cursor: pointer; font-family: var(--f-display); font-weight: 650; font-size: 0.9rem; background: var(--caution-soft); color: var(--caution); }
  details.solution[open] summary { border-bottom: 1px solid var(--rule); }
  details.solution .reveal { padding: 0.85rem 0.95rem 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
  .flash-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8rem; align-items: start; }
  details.flash { background: var(--surface); border: 1px solid var(--rule); border-radius: 3px; overflow: hidden; }
  details.flash summary { padding: 0.75rem 0.95rem; cursor: pointer; font-family: var(--f-display); font-weight: 650; font-size: 0.95rem; line-height: 1.35; }
  details.flash summary::before { content: attr(data-topic); display: block; margin-bottom: 0.25rem; color: var(--accent); font: 600 0.62rem var(--f-mono); letter-spacing: 0.06em; text-transform: uppercase; }
  details.flash[open] summary { border-bottom: 1px solid var(--rule); background: var(--surface-alt); }
  details.flash .answer { padding: 0.8rem 0.95rem 0.95rem; font-size: 0.95rem; display: flex; flex-direction: column; gap: 0.5rem; }
  .say-plain { margin: 0; line-height: 1.66; }
  .drill-body.single { grid-template-columns: 1fr; }
  .stack-lg { display: flex; flex-direction: column; gap: 0.9rem; }
  .agent-says { margin: 0; font-size: 0.95rem; color: var(--ink-muted); }
  table.matrix.compact { min-width: 36rem; }
  table.matrix.compact td:nth-child(3) { width: auto; }
  table.matrix.results { min-width: 40rem; }
  table.matrix.results td:first-child { width: 46%; font-family: var(--f-body); font-weight: 400; }
  table.matrix.results td:nth-child(2), table.matrix.results td:nth-child(3), table.matrix.results td:nth-child(4) { width: 18%; color: var(--ink); }
  table.matrix.scores td:nth-child(2), table.matrix.scores td:nth-child(3) { width: 30%; color: var(--ink); }
  table.matrix code { font-size: 0.82em; overflow-wrap: anywhere; }
  ol.timeline.steps li::before { content: counter(steps); }
  ol.timeline.steps li > div { display: flex; flex-direction: column; gap: 0.35rem; min-width: 0; }
  .rehearse { display: flex; flex-wrap: wrap; align-items: center; gap: 0.6rem 1rem; padding: 1rem 1.1rem; background: var(--surface); border: 1px solid var(--rule); border-left: 3px solid var(--accent); border-radius: 3px; }
  .rehearse[hidden] { display: none; }
  .rehearse button { font: 650 0.9rem var(--f-display); padding: 0.55rem 0.9rem; border-radius: 3px; border: 1px solid var(--accent); background: var(--accent); color: #FFFFFF; cursor: pointer; }
  .rehearse button.secondary { background: transparent; color: var(--accent); }
  .rehearse button:disabled { opacity: 0.45; cursor: default; }
  .rehearse .question { flex: 1 1 18rem; margin: 0; font-family: var(--f-display); font-weight: 600; }
  .rehearse .clock { margin: 0; font: 600 1.4rem var(--f-mono); color: var(--accent); min-width: 4.5rem; text-align: right; }
  /* grid and flex children default to min-width:auto, which lets a long code line widen the page on a phone */
  section > *, .two-col > *, .card, .stack, .stack-lg, .drill-body > *, details.solution .reveal > * { min-width: 0; }
  /* the donor's facts-strip rule `.fact` also matches `.badge.fact` */
  .badge.fact { min-height: 0; padding: 0.13rem 0.42rem; border: 0; display: inline-block; }
  html { scroll-padding-top: 8rem; }
  section { scroll-margin-top: 1rem; }
  @media (max-width: 48rem) { .flash-grid { grid-template-columns: 1fr; } }
  @media print { details.solution > *, details.flash > *, details.drill > * { display: block; } .rehearse { display: none; } }
</style>
"""

REHEARSE_SCRIPT = """
<script>
(() => {
  const box = document.getElementById("rehearse");
  if (!box) return;
  const questions = [...document.querySelectorAll("#ai-interview details.aiq summary .q")].map((node) => node.textContent.trim());
  const text = document.getElementById("rehearse-question");
  const clock = document.getElementById("rehearse-clock");
  const next = document.getElementById("rehearse-next");
  const stop = document.getElementById("rehearse-stop");
  let timer = null;
  let left = 90;
  let last = -1;
  const show = () => { clock.textContent = `${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`; };
  const halt = (message) => {
    clearInterval(timer);
    timer = null;
    stop.disabled = true;
    if (message) text.textContent = message;
  };
  next.addEventListener("click", () => {
    let pick = Math.floor(Math.random() * questions.length);
    if (questions.length > 1 && pick === last) pick = (pick + 1) % questions.length;
    last = pick;
    text.textContent = questions[pick];
    left = 90;
    show();
    clearInterval(timer);
    stop.disabled = false;
    timer = setInterval(() => {
      left -= 1;
      show();
      if (left <= 0) halt("Time. Stop, then compare what you said with that question's card below.");
    }, 1000);
  });
  stop.addEventListener("click", () => halt(""));
  box.hidden = false;
})();
</script>
"""

page = """<title>Turing · Senior Software Engineer, AI Evaluation — Coding Agents</title>
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
    <a href="citi-karat-python-interview.html">Citi&nbsp;Karat</a>
    <a href="thomson-reuters-cocounsel-lead.html">TR&nbsp;CoCounsel</a>
    <a href="verizon-ai-control-plane-screen.html">Verizon&nbsp;Control&nbsp;Plane</a>
    <a href="turing-ai-eval-coding-agents.html" aria-current="page">Turing&nbsp;AI&nbsp;Eval</a>
    <a href="micro1-forward-deployed-engineer.html">micro1&nbsp;FDE</a>
    <a href="jpmc-payments-ai-developer-portal.html">JPMC&nbsp;Payments</a>
    <span class="sep"></span>
    <a href="mcp-cicd-study-faq.html">CI/CD&nbsp;+&nbsp;MCP&nbsp;FAQ</a>
  </nav>

  <header class="masthead">
    <div class="mastcopy">
      <p class="eyebrow">Senior Software Engineer · AI Evaluation, Coding Agents · Turing · contract · prepared @@PREPARED@@</p>
      <h1>Review the agent like a senior engineer, then say exactly why.</h1>
      <p class="standfirst">Turing is contracting engineers to judge AI coding agents' work on real repositories for a frontier lab. Is the change correct, robust and honest, and which of two solutions is better? The process is a short form, a 25-minute AI interview, a 30-minute exercise reviewing AI-generated code, and a 20-minute call with the hiring manager. Your evidence here is unusually direct, because you built the checks that decide whether coding agents' work is actually done. Every drill result on this page came from running the code.</p>
    </div>
    <aside class="join-card" aria-label="Application deadline">
      <p class="eyebrow">Owner-supplied email · 16 Sep 2026</p>
      <p><strong>Apply by Thursday 17 September.</strong><br><span class="muted">The application link is in the email from Turing's talent team. The form takes about three minutes.</span></p>
      <p><strong class="hot">One hourly rate, in USD, not a range.</strong><br><span class="muted">Decide it before you open the form. See <a href="#apply">section 02</a>.</span></p>
      <a class="button" href="#ai-interview">Prepare the AI interview ↓</a>
      <p class="small muted">Thursday is also the Verizon phone screen at 2:45 PM EDT. Submit this form in the morning.</p>
    </aside>
  </header>

  <dl class="facts" aria-label="Engagement facts">
    <div class="fact"><dt>Type</dt><dd>Contractor · ~3 months</dd></div>
    <div class="fact"><dt>Hours</dt><dd>40/wk · 6h PT overlap</dd></div>
    <div class="fact"><dt>Location</dt><dd>N. America, LATAM, India</dd></div>
    <div class="fact"><dt>Process</dt><dd>Form · AI 25 · test 30 · HM 20</dd></div>
    <div class="fact"><dt>Apply by</dt><dd class="hot">Thu 17 Sep</dd></div>
    <div class="fact"><dt>Rate</dt><dd class="hot">One USD number</dd></div>
  </dl>

  <nav class="toc" aria-label="Contents">
    <p class="eyebrow">Use the page in this order</p>
    <ol>
      <li><span class="n">01</span><a href="#first">Read this first</a></li>
      <li><span class="n">02</span><a href="#apply">Application and rate</a></li>
      <li><span class="n">03</span><a href="#ai-interview">The AI interview</a></li>
      <li><span class="n">04</span><a href="#method">How to review an agent</a></li>
      <li><span class="n">05</span><a href="#failure-modes">Failure modes to hunt</a></li>
      <li><span class="n">06</span><a href="#drills">Seven review drills</a></li>
      <li><span class="n">07</span><a href="#writing">Writing the justification</a></li>
      <li><span class="n">08</span><a href="#manager">Hiring manager call</a></li>
      <li><span class="n">09</span><a href="#checklist">Checklist</a></li>
      <li><span class="n">10</span><a href="#sources">Sources + confidence</a></li>
    </ol>
  </nav>

  <main id="main">
    <section id="first">
      <div class="sec-head">
        <p class="eyebrow">01 · Read this first</p>
        <h2>Four steps, and the middle two are what decide it</h2>
      </div>
      <div class="priority-grid">
        <article class="priority">
          <span class="num">01 / FORM · BY THU 17 SEP</span>
          <h3>Three minutes, one hard field</h3>
          <p>The email asks for a specific hourly rate in USD, not a range. Settle the number first. See <a href="#apply">section 02</a>.</p>
        </article>
        <article class="priority">
          <span class="num">02 / AI INTERVIEW · 25 MIN</span>
          <h3>Structured, spoken, specific</h3>
          <p>Thirteen likely questions with drafted answers built only from your verified stories, plus a timer to rehearse them. See <a href="#ai-interview">section 03</a>.</p>
        </article>
        <article class="priority">
          <span class="num">03 / EXERCISE · 30 MIN</span>
          <h3>Judge code, not puzzles</h3>
          <p>The posting says the exercise tests reviewing and evaluating AI-generated code, not competitive programming. Learn the method, then run the drills. See <a href="#method">sections 04–07</a>.</p>
        </article>
        <article class="priority">
          <span class="num">04 / HIRING MANAGER · 20 MIN</span>
          <h3>Judgement and logistics</h3>
          <p>Throughput versus quality, disagreeing with a rubric, availability, and the questions worth asking. See <a href="#manager">section 08</a>.</p>
        </article>
      </div>
      <div class="two-col">
        <div class="note info">
          <p class="eyebrow">Your evidence is unusually direct</p>
          <p>Your platform runs coding agents such as Claude Code and Codex and makes their work verifiable. Completion requires evidence, rubric grades cite concrete evidence, and a grader can't be the author. There are 141 behavioural scenario tests and a pre-registered SWE-bench Pro subset. Tests must prove they can fail. That is this job's subject matter, built from the other side. Details are in the <a href="papercusp-answer-bank.html#q-ai-eval">Answer Bank, Q8</a> and <a href="papercusp-answer-bank.html#q-testing">Q2</a>.</p>
        </div>
        <div class="note crit">
          <p class="eyebrow">Integrity</p>
          <p>Neither the posting nor the email says whether AI tools may be used during the AI interview or the exercise. Read each step's instructions and follow them exactly; if they are silent, use none. The exercise measures your own judgement, so close this page before you start either one.</p>
        </div>
      </div>
    </section>

    <section id="apply">
      <div class="sec-head">
        <p class="eyebrow">02 · Application and rate</p>
        <h2>A three-minute form, and a number you should decide in advance</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>Published rate signals</h3>
          <div class="matrix-wrap">
            <table class="matrix compact">
              <thead><tr><th>Source</th><th>What it says</th><th>Weight</th></tr></thead>
              <tbody>
                <tr><td>Mercor, software-engineer experts page</td><td>Software Engineering Expert $70–$150/hr and Senior SWE Expert $150–$210/hr, for evaluating and comparing model outputs on realistic engineering tasks</td><td><span class="badge fact">Fact</span> undated page, fetched 16 Sep</td></tr>
                <tr><td>AI Gig Jobs, Turing guide</td><td>Turing AI training and evaluation roles $15–$40/hr; engineering work through Turing $50–$100+/hr</td><td><span class="badge inference">Low</span> aggregator; the low band describes generic annotation work</td></tr>
                <tr><td>Turing's own email</td><td>“Market rate — share a specific hourly rate in USD (not a range)”</td><td><span class="badge owner">Owner</span></td></tr>
              </tbody>
            </table>
          </div>
          <p class="small muted">No public source states what Turing pays for this specific role.</p>
        </article>
        <article class="card">
          <h3>How to settle one number</h3>
          <ul>
            <li>Start from your own floor for a three-month, 40-hour, no-benefits contract. As an independent contractor you cover your own taxes, insurance and time off.</li>
            <li>This is a senior role asking for five or more years and code-review judgement, so the comparable public band is Mercor's software-engineering expert range, not generic annotation rates.</li>
            <li>Your direct experience building evaluation rails for coding agents is a reason to sit in the upper half of that band, not the bottom.</li>
            <li>Write one whole number. If they counter, it will be from that number, so don't open at your floor.</li>
          </ul>
          <p class="small muted">This is a negotiation framework, not financial advice. The number is yours to choose.</p>
        </article>
      </div>
      <div class="note warn">
        <p class="eyebrow">On the form</p>
        <p>Lead with the evaluation work, not a stack list: you built a platform where coding agents' completion claims must carry evidence, work is graded against a rubric by a grader who can't be the author, and tests must prove they can fail. State languages honestly: TypeScript and Python have verified evidence on your prep pages; mention Go only if you have real Go experience. State your time zone and the Pacific hours you can cover.</p>
      </div>
    </section>

    <section id="ai-interview">
      <div class="sec-head">
        <p class="eyebrow">03 · The AI interview · about 25 minutes</p>
        <h2>An automated interviewer rewards a direct answer, a structure, and one concrete example</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>What is known, and what isn't</h3>
          <ul>
            <li><span class="badge owner">Owner</span> About 25 minutes, the second step, after the form.</li>
            <li><span class="badge inference">Low</span> An aggregator reports that Turing uses its own AI to evaluate candidates across coding, domain knowledge and communication.</li>
            <li><span class="badge unknown">Unknown</span> Whether it is voice, video or text; how many questions; whether it is recorded; what it scores.</li>
          </ul>
          <p class="small muted">Test your microphone and camera anyway, and take it somewhere quiet.</p>
        </article>
        <article class="card">
          <h3>How to answer an AI interviewer <span class="badge inference">Inference</span></h3>
          <ul>
            <li>Answer the question in your first sentence, then support it.</li>
            <li>Make the structure audible: “three things”, “first”, “then”, “finally”.</li>
            <li>Give one concrete example per answer, with a real detail such as an input, a number or a test.</li>
            <li>Aim for 60 to 90 seconds, then stop cleanly. Don't fill silence.</li>
            <li>If a question is ambiguous, say how you're reading it, then answer that.</li>
            <li>Speak from memory. Reading aloud sounds like reading, even to software.</li>
          </ul>
        </article>
      </div>
      <div class="rehearse" id="rehearse" hidden>
        <button type="button" id="rehearse-next">Give me a question</button>
        <button type="button" id="rehearse-stop" class="secondary" disabled>Stop</button>
        <p class="question" id="rehearse-question" aria-live="polite">Press the button, answer out loud before the clock runs out, then open that card.</p>
        <p class="clock" id="rehearse-clock" aria-live="off">1:30</p>
      </div>
      @@AI_QUESTIONS@@
      <p class="small muted">Every factual claim in these answers appears on your Answer Bank or the ServiceNow page's Storewolf section; the linked anchors are the source. Fill the bracketed logistics yourself.</p>
    </section>

    <section id="method">
      <div class="sec-head">
        <p class="eyebrow">04 · How to review an agent's work</p>
        <h2>A fixed order, a five-part rubric, and an honest preference scale</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>The review loop</h3>
          <ol class="timeline">
            <li><div><h4>Criteria</h4><p>Turn the task into acceptance criteria, including implied ones: stated scale, error behaviour, compatibility, security.</p></div></li>
            <li><div><h4>Tests before code</h4><p>Which tests changed? Were any skipped, deleted or rewritten? Do they test the requirement or only the example?</p></div></li>
            <li><div><h4>Trace three inputs</h4><p>A normal input, a boundary, and a malformed or hostile one. Write down what each version returns.</p></div></li>
            <li><div><h4>Verify, don't believe</h4><p>Run it if you can. If you can't, name the concrete input that breaks it and its output.</p></div></li>
            <li><div><h4>Scope</h4><p>List every behaviour change in the diff. Anything unrequested is a finding, even if it's an improvement.</p></div></li>
            <li><div><h4>Report against evidence</h4><p>Check each claim in the agent's final message against what its own runs showed.</p></div></li>
            <li><div><h4>Decide and write</h4><p>Verdict, preference strength, then the justification. Write the verdict line within the first ten minutes.</p></div></li>
          </ol>
        </article>
        <article class="card">
          <h3>Timing a 30-minute exercise <span class="badge inference">Inference</span></h3>
          <ul>
            <li><strong>0–5 min.</strong> Read the task and the tests. Write the acceptance criteria.</li>
            <li><strong>5–15 min.</strong> Trace the diff or trajectory, and run it if the environment allows.</li>
            <li><strong>15–20 min.</strong> Score, choose the preference, and write the verdict sentence.</li>
            <li><strong>20–30 min.</strong> Write the justification, then reread it once against the evidence.</li>
          </ul>
          <p class="small muted">If there are two tasks, halve every band. An unwritten judgement scores nothing.</p>
          <h3>Preference scale</h3>
          <p>A much better · A better · A slightly better · About the same · B slightly better · B better · B much better.</p>
          <p class="small muted">Use “much better” when a correctness or safety gate differs. Use “slightly” when the difference is taste, and say that it is.</p>
        </article>
      </div>
      <div class="matrix-wrap">
        <table class="matrix compact">
          <thead><tr><th>Dimension</th><th>1 · poor</th><th>3 · adequate</th><th>5 · strong</th></tr></thead>
          <tbody>
            <tr><td>Correctness <span class="badge unknown">Gate</span></td><td>Fails the stated requirement on a normal input</td><td>Right on the common path; misses a stated edge case</td><td>Meets every stated and clearly implied requirement</td></tr>
            <tr><td>Verification</td><td>No test, or tests edited, skipped or rewritten to pass</td><td>Tests the example from the task only</td><td>Tests the requirement, including a case that fails without the change</td></tr>
            <tr><td>Robustness and safety <span class="badge unknown">Gate</span></td><td>Hides errors, is injectable, or crashes on ordinary input</td><td>Handles expected errors; some boundaries unhandled</td><td>Fails loudly and specifically on bad input; no security exposure</td></tr>
            <tr><td>Scope and maintainability</td><td>Unrequested behaviour or API changes</td><td>Minor unrelated edits or duplication</td><td>Minimal, idiomatic, consistent with the codebase</td></tr>
            <tr><td>Honesty of the report</td><td>Claims contradicted by its own evidence</td><td>Overstates coverage or omits a caveat</td><td>Every claim backed; limitations stated</td></tr>
          </tbody>
        </table>
      </div>
      <p class="small muted">This rubric is a practice instrument written for this page. Turing's exercise will have its own; use the same discipline with theirs.</p>
    </section>

    <section id="failure-modes">
      <div class="sec-head">
        <p class="eyebrow">05 · Failure modes to hunt</p>
        <h2>Ten ways an agent's work fools a reviewer, and how to catch each</h2>
      </div>
      <div class="matrix-wrap">
        <table class="matrix compact">
          <thead><tr><th>Failure mode</th><th>What it looks like</th><th>Catch it by</th></tr></thead>
          <tbody>
            <tr><td>Gaming the check</td><td>Tests edited, skipped or deleted; the tested input special-cased; the evaluator stubbed out</td><td>Reading the test diff first; running an input the agent didn't choose. See the <a href="#drill-trajectory">trajectory drill</a>.</td></tr>
            <tr><td>Incomplete generalisation</td><td>Handles the example in the task, not the requirement</td><td>Building an input one step beyond the example. See <a href="#drill-durations">drill 1</a>.</td></tr>
            <tr><td>Error swallowing</td><td>A broad except, default return values, “no longer crashes”</td><td>Feeding missing and malformed input; errors should surface. See <a href="#drill-settings">drill 2</a>.</td></tr>
            <tr><td>Async and concurrency mistakes</td><td><code>forEach(async …)</code>, un-awaited promises, shared mutable state</td><td>Testing with real latency, not instant mocks. See <a href="#drill-quotes">drill 3</a>.</td></tr>
            <tr><td>Injection and unsafe input</td><td>SQL, shell commands or HTML built from strings</td><td>Trying a quote, a wildcard and a comment sequence. See <a href="#drill-search">drill 4</a>.</td></tr>
            <tr><td>Scope creep and API breaks</td><td>Renames, reordering, reformatting, “while I was there”</td><td>Listing every behaviour change and checking callers. See <a href="#drill-refunds">drill 5</a>.</td></tr>
            <tr><td>Wrong fit for stated constraints</td><td>Quadratic work on a batch the task says is large; semantics that differ from the data format</td><td>Reading the task for numbers and formats. See <a href="#drill-events">drill 6</a>.</td></tr>
            <tr><td>Unverified success claims</td><td>“All tests pass” with skips, or without any run</td><td>Checking the final run's output in the trajectory. See the <a href="#drill-trajectory">trajectory drill</a>.</td></tr>
            <tr><td>Hallucinated or version-wrong APIs</td><td>A method that doesn't exist, or exists only in a newer runtime than the project targets</td><td>Checking the project's declared runtime version against the documentation</td></tr>
            <tr><td>Destructive or risky actions</td><td>Force-pushes, deleted files, rewritten history, touched secrets</td><td>Reading every command in the trajectory, not only the final diff</td></tr>
          </tbody>
        </table>
      </div>
      <div class="note info">
        <p class="eyebrow">Published examples of gaming the check <span class="badge fact">METR, 5 Jun 2025</span></p>
        <p>METR's “Recent Frontier Models Are Reward Hacking” documents models that overwrote a timing function so measurements came out shorter, created a stub evaluator so every submission passed, and read the scoring system's already-computed answer from the Python call stack. Citing a public example like this in the AI interview is stronger than describing the category in the abstract.</p>
      </div>
    </section>

    <section id="drills">
      <div class="sec-head">
        <p class="eyebrow">06 · Seven review drills</p>
        <h2>Two agent responses per task. Judge them, then open what running them showed.</h2>
      </div>
      <div class="note warn">
        <p class="eyebrow">How these were checked</p>
        <p>Each drill's original code and both responses were executed against the checks shown in its answer when this page was built, by <code>build-turing-page.py</code> using <code>turing-eval-drills.py</code>. The build refuses to write the page if any result differs from what the answer claims. The scenarios are original practice modelled on common coding-agent failures, not Turing's exercise. Do three of them timed before the real one.</p>
      </div>
      @@DRILLS@@
    </section>

    <section id="writing">
      <div class="sec-head">
        <p class="eyebrow">07 · Writing the justification</p>
        <h2>Researchers can act on an input and a consequence, not on an adjective</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>A shape that works</h3>
          <ol class="timeline">
            <li><div><p><strong>Preference and strength.</strong> “Prefer A, strongly.”</p></div></li>
            <li><div><p><strong>The deciding difference, with the input that proves it.</strong> “B returns defaults for malformed JSON.”</p></div></li>
            <li><div><p><strong>Its consequence.</strong> “The service then starts with no endpoint and fails far from the cause.”</p></div></li>
            <li><div><p><strong>What the better response did right,</strong> in one sentence.</p></div></li>
            <li><div><p><strong>A residual risk or question</strong> for the better response, if there is one.</p></div></li>
          </ol>
        </article>
        <article class="card">
          <h3>Weak versus strong, on drill 2</h3>
          <p class="eyebrow">Weak</p>
          <p class="probe">Response A is better because it is cleaner and handles errors better. Response B uses a try/except, which is not good practice. A is more robust overall.</p>
          <p class="small muted">No input, no consequence. “Cleaner” is taste, and “not good practice” is not an argument.</p>
          <p class="eyebrow">Strong</p>
          <p class="probe">Prefer A, strongly. B wraps the loader in <code>except Exception</code> and returns defaults, so a file missing the required endpoint, malformed JSON, and a nonexistent path all “succeed”; the service would start with <code>endpoint: None</code> and fail later, far from the cause. A fixes the reported KeyError with <code>.get</code> against DEFAULTS and raises a ValueError naming the file when endpoint is missing. A should add a test for that new error.</p>
        </article>
      </div>
      <ul class="checklist">
        <li>Quote the exact input or line, not a paraphrase.</li>
        <li>Separate what you observed from what you think caused it.</li>
        <li>Use the same name for the same failure mode every time.</li>
        <li>Never reward length, confidence or politeness in the agent's message.</li>
        <li>Say what you could not determine.</li>
        <li>Check that your preference strength matches your evidence.</li>
      </ul>
    </section>

    <section id="manager">
      <div class="sec-head">
        <p class="eyebrow">08 · Hiring manager call · about 20 minutes</p>
        <h2>Short answers on judgement and logistics, then your questions</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>Likely questions <span class="badge inference">Inference</span></h3>
          <ul>
            <li><strong>“How many tasks an hour, at quality?”</strong> Don't invent a number. Describe the split between reading, tracing, verifying and writing, and say you'd calibrate against their quality audits in the first week.</li>
            <li><strong>“Have you done RLHF or preference-data work?”</strong> Be exact: not labelling for post-training, but building evaluation rails for coding agents. The posting lists it as a plus, not a requirement.</li>
            <li><strong>“What if you disagree with the rubric?”</strong> Apply it as written so the data stays consistent, record the disagreement with a concrete example, and raise it through calibration.</li>
            <li><strong>“Which languages are you strongest in?”</strong> Name the languages you can defend in review. TypeScript and Python have verified evidence on your prep pages.</li>
            <li><strong>“The role also builds pipelines.”</strong> Your platform's scheduler, event system and release gate are that kind of infrastructure: <a href="papercusp-answer-bank.html#n-system-design">Answer Bank N2</a>.</li>
          </ul>
        </article>
        <article class="card">
          <h3>Questions to ask</h3>
          <ul>
            <li>Which repositories and languages will most tasks use?</li>
            <li>Can evaluators run the code, or is review read-only?</li>
            <li>How is evaluator quality measured: audits, agreement with other raters, or gold tasks?</li>
            <li>How does calibration feedback reach me, and how quickly?</li>
            <li>How much of the work is pipeline and infrastructure versus evaluation?</li>
            <li>What does a strong first two weeks look like?</li>
            <li>Can the engagement extend past three months, and how are hours and invoices handled?</li>
          </ul>
        </article>
      </div>
    </section>

    <section id="checklist">
      <div class="sec-head">
        <p class="eyebrow">09 · Checklist</p>
        <h2>Before each step</h2>
      </div>
      <ul class="checklist">
        <li>Submit the form by Thursday 17 September, before the Verizon call at 2:45 PM EDT.</li>
        <li>Decide one hourly rate in USD before opening the form.</li>
        <li>Know your time zone and which Pacific hours you can cover for at least six hours a day.</li>
        <li>Rehearse five AI-interview questions aloud with the timer.</li>
        <li>Test your microphone and camera; find a quiet room for the AI interview.</li>
        <li>Do drills 1, 3 and the trajectory drill timed before the exercise.</li>
        <li>Read each step's instructions on tool use before starting. If they are silent, use none.</li>
        <li>In the exercise, write the verdict line in the first ten minutes.</li>
        <li>Close this page before the AI interview and the exercise.</li>
      </ul>
    </section>

    <section id="sources">
      <div class="sec-head">
        <p class="eyebrow">10 · Sources + confidence</p>
        <h2>What came from Turing, what is published, and what is inferred</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>Confidence by claim</h3>
          <ul>
            <li><span class="badge owner">Owner</span> Role, responsibilities, requirements, engagement terms, the four-step process with durations, the rate instruction and the 17 September deadline: the Turing posting and Turing's talent-acquisition email, both supplied 16 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Mercor's published software-engineering expert rate bands: Mercor's experts page, fetched 16 Sep 2026; the page is undated.</li>
            <li><span class="badge fact">Fact</span> The three reward-hacking examples: METR, “Recent Frontier Models Are Reward Hacking”, 5 Jun 2025.</li>
            <li><span class="badge fact">Fact</span> Every pass, fail and timing in section 06: executed at build time; timings are from the build machine and will vary.</li>
            <li><span class="badge fact">Fact</span> Every experience claim in section 03: the Answer Bank and the ServiceNow page's Storewolf inventory, as linked.</li>
            <li><span class="badge inference">Inference</span> Turing using its own AI to evaluate candidates, and its generic rate bands: an aggregator guide of low reliability.</li>
            <li><span class="badge inference">Inference</span> How to answer an AI interviewer, the exercise timing, and the hiring manager's likely questions.</li>
            <li><span class="badge unknown">Unknown</span> The AI interview's medium and scoring, the exercise platform, whether code can be run, the tool policy, and Turing's rate for this role.</li>
          </ul>
        </article>
        <article class="card">
          <h3>Sources</h3>
          <ul class="source-list">
            <li><a href="https://www.mercor.com/experts/software-engineers/" target="_blank" rel="noreferrer">Mercor — AI training work for software engineers, with published hourly bands</a></li>
            <li><a href="https://metr.org/blog/2025-06-05-recent-reward-hacking/" target="_blank" rel="noreferrer">METR — Recent Frontier Models Are Reward Hacking (5 Jun 2025)</a></li>
            <li><a href="https://www.aigigjobs.com/platforms/turing" target="_blank" rel="noreferrer">AI Gig Jobs — Turing guide (aggregator, low reliability)</a></li>
            <li><a href="https://docs.python.org/3/library/csv.html" target="_blank" rel="noreferrer">Python docs — csv, including newline="" when writing</a></li>
            <li><a href="https://nodejs.org/api/cli.html#--unhandled-rejectionsmode" target="_blank" rel="noreferrer">Node.js docs — unhandled rejections throw by default</a></li>
            <li><a href="turing-eval-drills.py">turing-eval-drills.py</a> — the drills and runner · <a href="build-turing-page.py">build-turing-page.py</a> — the generator</li>
          </ul>
        </article>
      </div>
    </section>
  </main>

  <footer>
    <p>Prepared @@PREPARED@@ for Turing's Senior Software Engineer, AI Evaluation / Coding Agents contract. Generated by <code>build-turing-page.py</code>, which refuses to write this page unless every drill result matches what actually ran.</p>
    <p><a href="#top">Back to top ↑</a></p>
  </footer>
</div>
@@SCRIPT@@
"""

drill_sections = [drill_html(i, d) for i, d in enumerate(drills.DRILLS, start=1)]
drill_sections.append(trajectory_html(len(drills.DRILLS) + 1))
replacements = {
    "@@STYLE@@": style,
    "@@EXTRA_CSS@@": extra_css,
    "@@PREPARED@@": PREPARED,
    "@@AI_QUESTIONS@@": ai_questions_html(),
    "@@DRILLS@@": "\n".join(drill_sections),
    "@@SCRIPT@@": REHEARSE_SCRIPT,
}
for marker, value in replacements.items():
    assert marker in page, marker
    page = page.replace(marker, value)
assert not re.findall(r"@@\w+@@", page)
assert len(AI_QUESTIONS) == 13 and len(drills.DRILLS) + 1 == 7

PAGE.write_text(page, encoding="utf-8")
print(f"drills matched; quotes A {quotes_a} vs original {quotes_original}; events A {events_a} vs B {events_b} (~{events_extrapolated:.0f}s at 50k)")
print(f"wrote {PAGE} ({PAGE.stat().st_size} bytes)")
