#!/usr/bin/env python3
"""
Generate the micro1 · Forward Deployed Engineer prep artifacts from ONE tested source:

  micro1-fde-solutions.py   (hand-written, self-testing — must exit 0 first)
        ├─► micro1-fde-practice.py                  blanked skeletons + the same checks
        └─► micro1-forward-deployed-engineer.html   the prep page

The worked inter-annotator agreement example is computed here and asserted, not typed in.
Re-run after any edit:  python3 build-micro1-page.py && ./build-standalone.sh
The page's <style> is copied from the Hyundai page so the collection stays one visual system.
"""
import html
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "micro1-fde-solutions.py"
PRACTICE = HERE / "micro1-fde-practice.py"
PAGE = HERE / "micro1-forward-deployed-engineer.html"
STYLE_DONOR = HERE / "hyundai-autoever-applied-ai-hm-call.html"
PREPARED = "17 Sep 2026"

run = subprocess.run([sys.executable, str(SRC)], capture_output=True, text=True)
if run.returncode != 0:
    sys.stderr.write(run.stdout + run.stderr)
    sys.exit("solutions file is red — refusing to generate from it")

src = SRC.read_text(encoding="utf-8")
parts = re.split(r"^# ==== (\w+) ====\n", src, flags=re.M)
sections = {parts[i]: parts[i + 1].rstrip("\n") + "\n" for i in range(1, len(parts), 2)}
ORDER = ["imports", "chunking", "retrieval", "fusion", "retry", "cache", "tests"]
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


practice = '''"""
micro1 · Forward Deployed Engineer — CODING DRILLS, PRACTICE FILE (generated from micro1-fde-solutions.py).

Run:  python3 micro1-fde-practice.py      every check prints PASS or FAIL with the failing line

Fill every `# implement this` / `pass` region. The docstrings are the spec.
Type it, don't paste it: third-party reports say micro1's coding round disables copy and paste.
Talk out loud while you type, as if the interviewer were listening.
Targets: chunk_words 8 min · top_k 10 · reciprocal_rank_fusion 8 · call_with_retry 12 · LRUCache 10.
"""
'''
for name in ORDER:
    body = sections[name]
    practice += f"# ==== {name} ====\n" + (body if name in ("imports", "tests") else skeletonize(body)) + "\n"
PRACTICE.write_text(practice, encoding="utf-8")
blank = subprocess.run([sys.executable, str(PRACTICE)], capture_output=True, text=True)
if blank.returncode == 0 or re.search(r"^PASS", blank.stdout, flags=re.M) or "Traceback" in blank.stderr:
    sys.stderr.write(blank.stdout + blank.stderr)
    sys.exit("practice file must run cleanly and fail every check before any work is done")

# Worked agreement example: two annotators label 50 agent transcripts pass or fail.
both_pass, both_fail, a_pass_b_fail, a_fail_b_pass = 20, 15, 5, 10
n = both_pass + both_fail + a_pass_b_fail + a_fail_b_pass
observed = (both_pass + both_fail) / n
a_pass = (both_pass + a_pass_b_fail) / n
b_pass = (both_pass + a_fail_b_pass) / n
expected = a_pass * b_pass + (1 - a_pass) * (1 - b_pass)
kappa = (observed - expected) / (1 - expected)
assert (n, round(observed, 2), round(a_pass, 2), round(b_pass, 2), round(expected, 2), round(kappa, 2)) == (50, 0.70, 0.50, 0.60, 0.50, 0.40)


def esc(s):
    return html.escape(s, quote=False)


def code_block(code, label=None, extra=""):
    lab = f'<p class="eyebrow">{esc(label)}</p>' if label else ""
    return f'{lab}<pre class="code{extra}"><code>{esc(code.strip(chr(10)))}</code></pre>'


def solution_pair(section, minutes):
    return (
        f'<details class="solution"><summary>Skeleton · target {minutes}</summary>{code_block(skeletonize(sections[section]))}</details>'
        f'<details class="solution"><summary>Reference solution — open only after your attempt</summary>{code_block(strip_markers(sections[section]))}</details>'
    )


AB = "papercusp-answer-bank.html"
SN = "servicenow-staff-ml-interview-prep.html#stack"

SKILLS = {
    "python": [
        ("Describe a production Python system you built end to end.", "Ownership and real production detail.",
         "The scoring service behind a gradient-boosted pricing model. The main application was Node, so the model ran as a long-lived Python process rather than an HTTP service: the Node side writes one JSON command per line, train or predict, and reads one JSON line back. It loads the trained XGBoost model once, so ten-thousand-row prediction batches don't pay that cost. The hard part was the feature schema. pandas get_dummies builds one-hot columns from whatever batch it sees, so training persists the exact column list, inference re-adds missing columns as zeros, and then reorders to the booster's own feature names — two guards against one failure. If I rebuilt it, I'd persist a fitted scikit-learn Pipeline as the artifact, stop the imputer re-fitting at prediction time, and keep evaluation metrics instead of printing a single R-squared.",
         [SN]),
        ("asyncio, threads or processes for a service that calls LLM APIs and also parses large documents?", "Concurrency fundamentals applied to an AI workload.",
         "Split the workload by what it waits on. LLM calls are I/O-bound, so asyncio fits: one event loop, many in-flight requests, with a semaphore to bound concurrency, a timeout on every call, and retries with backoff for rate limits. Document parsing is CPU-bound, and the GIL means threads won't parallelise pure-Python work, so that goes to a process pool. Threads are for blocking libraries that have no async client. The one mistake to avoid is a blocking call inside async code: it stalls every request on that loop. Free-threaded CPython builds exist from 3.13, but they're optional, so I wouldn't design around them yet.",
         []),
        ("A Python data pipeline has become too slow. How do you find and fix the bottleneck?", "Measure-first discipline.",
         "Measure before changing anything: cProfile for a reproducible run, or py-spy against the live process, so I know whether time goes to I/O, parsing or Python-level loops. The usual fixes, in order of payoff: remove repeated work, such as loading a model or re-parsing the same file per record; batch I/O; replace per-row Python loops with vectorised pandas, Polars or NumPy operations; stream so memory stays flat; and only then parallelise. In my scoring service the key design choice was structural: load the model once in a long-lived process, so large batches amortise it.",
         [SN]),
        ("How do you keep a Python codebase reliable as it grows?", "Engineering hygiene, beyond 'write tests'.",
         "Four habits. Validate data at the boundaries, with dataclasses or pydantic, so bad input fails where it enters. Type-check in CI. Pin dependencies with a lockfile so builds are reproducible. And make tests prove they can fail: a test that has never failed is a guard nobody has tested. In my own platform a probe deliberately breaks the code under test and asserts the guard notices, and the runner refuses a run that selected zero tests instead of reporting it green.",
         [f"{AB}#q-testing"]),
        ("What Python pitfalls do you watch for in code review?", "Language depth.",
         "A handful cause most of the subtle bugs I look for. Mutable default arguments, because the default is built once when def runs and shared by every call. is used where == was meant, which works by accident for small integers and interned strings. Late-binding closures in loops. Generators and file objects consumed twice, where the second pass silently sees nothing. Broad except clauses that turn a crash into silent wrong output. And floats for money. Each one passes a casual test and fails in production.",
         ["citi-karat-python-interview.html#knowledge"]),
    ],
    "llm": [
        ("How do you design tools and interfaces for LLM agents?", "Hands-on agent tooling experience.",
         "Four things differ from a normal API. The description is a cost paid on every call, because every tool definition sits in the model's context; in my platform each tool has a 1,500-character budget with a 1,600 hard cap, checked at registration and again on every hot reload. Results are bounded at the source: a result is capped around 1,500 tokens, so every tool accepts a projection of the fields you need. A refusal has to teach, because the model can't read docs mid-call, so every refusal names its own repair. And empty is not the same as didn't run: a tool must distinguish 'found nothing' from 'couldn't look'.",
         [f"{AB}#n-tool-design"]),
        ("How do you evaluate an LLM or agent system before and after launch?", "Evaluation rigour.",
         "Before launch: an evaluation set built from real tasks, scored per stage so retrieval or tool errors aren't blamed on generation, and graded against a rubric whose criteria are observable and cite evidence. In my platform there are two layers: 141 scenario tests across ten agent roles run the actual prompts against a model, and a random subset of the 731-task SWE-bench Pro set, 50 and 150 tasks with seed 42, with predictions registered before the run. Completion requires evidence, and the grader can't be the author. After launch, I'd keep the same set as a regression gate and add online signals: task success, escalations, and human corrections.",
         [f"{AB}#q-ai-eval"]),
        ("How do you manage context in long-running, multi-turn agent sessions?", "Multi-turn reliability.",
         "Three principles and one bug. Write through: a conclusion goes to durable state the moment it forms, not in a flush at the end. A summary is an index into live sources to re-verify, not a self-contained dump. And the full transcript survives on disk and is searchable, so a successor retrieves what summarisation dropped instead of re-deriving it. The bug is that attribution rots first: we traced an agent's own note-to-self that, seven compactions later, read as an instruction from the owner. So every carried directive now records its source.",
         [f"{AB}#n-context"]),
        ("How do you handle rate limits, cost and latency across many agents?", "Operating LLM systems at scale.",
         "A pool of provider accounts behind an inference gateway, with an AIMD controller — additive increase, multiplicative decrease — admitting work against measured headroom. Before launching a fleet, one canary has to complete a turn, because a fleet started into an exhausted pool dies silently. The lesson that cost the most: utilisation was only measured from live traffic, so a walled account received no traffic and never got a fresh reading. Now a probe sends one minimal request per account and reads the authoritative limit headers.",
         [f"{AB}#n-capacity"]),
        ("How do you defend an agent against prompt injection and unsafe tool use?", "Security judgement.",
         "Treat everything retrieved or returned by a tool as data, never as instructions, and put the enforcement outside the model. In my platform the tool dispatcher runs a default-deny step, so a tool that declares no permission gate is refused rather than allowed by omission, with a per-role allowlist and per-principal capability checks above it. For irreversible actions I'd add human approval and an audit trail. I'd be candid that the mechanism is stronger than the policy authored on it so far: when I checked, only three roles carried explicit deny entries.",
         [f"{AB}#g-permissions"]),
    ],
    "infra": [
        ("Design a pipeline from data curation through training, evaluation and deployment.", "End-to-end ML systems thinking.",
         "Seven stages, each with an artifact the next one can trust. Ingest and validate against a schema. Deduplicate, and decontaminate against evaluation sets so benchmark items never leak into training. Label or curate with quality control. Freeze a versioned dataset snapshot. Train from a pinned config, seed, code commit and snapshot id. Evaluate on held-out and regression sets as a gate, with predictions recorded before the run so the bar can't move afterwards. Then promote through staged rollout with monitoring that feeds failures back into curation. The principle from my own release gate applies: certify a candidate before promoting it, and fall back to the full check when a narrowed one can't be positively verified.",
         [f"{AB}#q-cicd", f"{AB}#q-ai-eval"]),
        ("What is training-serving skew, and have you dealt with it?", "Production ML failure modes.",
         "It's when the features a model sees at inference differ from what it was trained on, and it produces confident nonsense rather than errors. I hit the classic version: pandas get_dummies derives one-hot columns from whatever batch is in front of it, so a prediction batch missing a category, or carrying a new one, yields a different column set. The fix was two independent guards: training persists the exact post-encoding column list and inference re-adds missing columns as zeros, and then inference reorders to the booster's own feature names. Today I'd persist a fitted Pipeline, so the transform and the model ship as one artifact.",
         [SN]),
        ("How would you design a data taxonomy and a labeling workflow with quality control?", "The JD's data-quality emphasis.",
         "Start from the decisions the data has to drive, and make each level of the taxonomy mutually exclusive, with an explicit unclear bucket that routes to review instead of forcing a guess. Write guidelines with examples and counter-examples for every label. Seed a gold set, measure inter-annotator agreement with a chance-corrected statistic such as Cohen's kappa rather than raw agreement, adjudicate disagreements, and feed them back into the guidelines. Then audit a sample continuously and watch for drift. My closest real experience is a product-matching system where the feedback loop was human: manual overrides by product group and an operations-curated blocklist. The honest gap is that it never had a labelled benchmark, and the first thing I'd build again is a labelled pair set so I could state precision at a threshold.",
         [f"{SN}"]),
        ("How do you make experiments reproducible and results trustworthy?", "Scientific discipline.",
         "Pin everything that can change the answer: the dataset snapshot id, the config, the seed, the code commit and the environment. Record the prediction before the run: our SWE-bench Pro subset was drawn with seed 42, nested at 50 and 150 tasks, and pre-registered, so nobody could quietly move the goalposts. Keep a metric history rather than a printed number; that's a gap I'd fix in my own scoring service, whose only metric was a single printed R-squared. And be suspicious of a result that's too clean: a suspiciously round number is usually a definitional artifact, which I learned by reporting one wrongly and retracting it.",
         [f"{AB}#q-ai-eval", f"{AB}#q-wrong", SN]),
        ("How would you serve models reliably at scale?", "Serving knowledge, and honesty about depth.",
         "My verified production experience is a CPU tabular model served from a long-lived process, so I'll separate what I've built from what I know. What carries over: load once and keep the process warm, batch requests, set timeouts and bounded queues, autoscale on queue depth rather than CPU alone, and version the model and its feature schema together. For large-model serving on GPUs, the levers are continuous batching, KV-cache management, quantisation, and routing requests to cheaper models when quality allows. I know those as design options rather than systems I've operated, and I'd say so to a partner.",
         [SN]),
    ],
    "rag": [
        ("Design a RAG system over an enterprise's internal documents.", "Architecture breadth and security awareness.",
         "Ingest with metadata, including who is allowed to see each document. Chunk along the document's own structure, with modest overlap. Retrieve with both keyword and embedding search and fuse the rankings, because each catches what the other misses; I use reciprocal rank fusion, and my platform has an RRF ranker as a standalone library. Rerank the top candidates, and apply permission filters before anything enters the model's context, not after generation. Answer with citations, and refuse when retrieval doesn't support an answer. Evaluate retrieval and generation separately: recall at k on a labelled query set, then faithfulness to the retrieved text. In my own documentation search the result says when the semantic leg didn't run, so a keyword-only answer is never mistaken for a full one.",
         [f"{AB}#n-docs", f"{AB}#g-tenancy"]),
        ("Retrieval quality is poor. How do you debug it?", "Diagnostic method for RAG.",
         "First separate retrieval from generation: if the right passage isn't in the top k, prompt changes won't help. Build a small labelled query set from real questions and measure recall at k. Then read the misses. The usual causes are chunk boundaries that split the answer, vocabulary mismatch that a keyword leg would catch, missing metadata filters, or an embedding model that doesn't know the domain. Change one variable at a time against the same query set, and add a reranker once recall is good enough that ordering is the problem.",
         []),
        ("When would you not use embeddings?", "Judgement over fashion.",
         "When the discriminating signal is a few discrete attributes. I built cross-marketplace product matching, which looks like text similarity and isn't: the same laptop with 256 GB versus 512 GB is near-identical in embedding space and economically completely different. A false match meant buying or listing the wrong item. So we extracted typed attributes and built an auditable partial order over them, where I could point to the attribute that drove a match. Where fuzzy matching was right, aligning the same listing across regional sites, we used Jaro-Winkler on titles.",
         [SN]),
        ("Which steps of a workflow would you automate with AI, and which would you keep human?", "Human-in-the-loop design.",
         "Decide by the cost of a wrong answer and whether it can be undone. Automate fully where errors are cheap and reversible. Use confidence thresholds to route uncertain cases to people. Keep humans on decisions that are expensive or irreversible, and audit a sample of the automated ones so drift shows up. In the matching system, a false positive cost real money and account health, while a false negative was only a missed opportunity, so the design favoured precision and kept operators able to override any product group.",
         [SN]),
        ("A partner has many one-off AI experiments. How do you make one repeatable in production?", "The core forward-deployed outcome.",
         "Pick the experiment tied to a business decision, then turn its success into something measurable: an evaluation set drawn from real cases, with a pass bar agreed before building. Version prompts, configs and data together. Instrument every run so a failure can be traced. Put the evaluation in front of every change as a gate. Roll out to a slice of traffic first. And give it an owner and a runbook. The pattern mirrors how my own platform treats agent work: done has to come with evidence, and a candidate is certified before it's promoted.",
         [f"{AB}#q-ai-eval", f"{AB}#q-cicd"]),
    ],
}

SCENARIOS = [
    ("A frontier lab says it needs better coding-agent training data. What do you do in the first two weeks?",
     "Start with the capability, not the data. Agree which skill the lab wants to move and how it will be measured, then look at current model failures to see what's missing. Build a taxonomy of task types and failure modes from those failures. Run a pilot of about fifty tasks with a rubric, measure annotator agreement, and fix the guidelines where people disagree. Only then scale. Deliver a short written readout at the end of each week: what we measured, what changed, what we couldn't determine."),
    ("A partner insists on an approach you believe won't work.",
     "Say so once, with evidence and a concrete failure case, then propose the cheapest experiment that would settle it and agree the success criterion before running it. If they still choose their approach, commit to executing it well and write the decision down with its assumptions, so it's easy to revisit when the data comes in."),
    ("The requirements are ambiguous and the partner is hard to reach.",
     "Write the assumptions down explicitly, build the smallest reversible slice, and send it back with a short list of what I assumed and what I couldn't determine. A concrete artifact gets a faster and more precise answer than an open question, and it keeps the work moving."),
    ("An agent workflow you deployed starts failing intermittently at a partner.",
     "Stabilise first: limit the blast radius, roll back or route around if possible, and tell the partner what's affected. Then check the instruments before trusting them: in my experience the hardest incidents come from a check that returns a clean-looking wrong answer, like a liveness probe that reported a live process as gone. Find the root cause, add a guard that would have caught it, and share a short written postmortem."),
]


def cards(items):
    out = ['<div class="flash-grid">']
    for question, probe, answer, links in items:
        link_html = ""
        if links:
            link_html = '<p class="small muted">Verified source: ' + " · ".join(f'<a href="{href}">{esc(href.split("#")[-1] if "#" in href else href)}</a>' for href in links) + "</p>"
        out.append(f'<details class="flash"><summary data-topic="Probing: {esc(probe)}">{esc(question)}</summary>'
                   f'<div class="answer"><p class="say-plain">{esc(answer)}</p>{link_html}</div></details>')
    out.append("</div>")
    return "\n".join(out)


def scenario_cards():
    out = ['<div class="flash-grid">']
    for question, answer in SCENARIOS:
        out.append(f'<details class="flash"><summary data-topic="Scenario">{esc(question)}</summary><div class="answer"><p class="say-plain">{esc(answer)}</p></div></details>')
    out.append("</div>")
    return "\n".join(out)


donor = STYLE_DONOR.read_text(encoding="utf-8")
style = donor[donor.index('<link rel="preconnect"'): donor.index("</style>") + len("</style>")]
extra_css = """
<style>
  pre.code { margin: 0; padding: 0.85rem 1rem; background: var(--surface-alt); border: 1px solid var(--rule); border-radius: 3px; overflow-x: auto; font-family: var(--f-mono); font-size: 0.77rem; line-height: 1.5; tab-size: 4; max-width: 100%; }
  pre.code code { background: transparent; padding: 0; font-size: inherit; }
  details.solution { border: 1px solid var(--rule); border-radius: 3px; background: var(--surface); min-width: 0; }
  details.solution summary { padding: 0.65rem 0.9rem; cursor: pointer; font-family: var(--f-display); font-weight: 650; font-size: 0.9rem; background: var(--caution-soft); color: var(--caution); }
  details.solution[open] summary { border-bottom: 1px solid var(--rule); }
  details.solution > pre.code { border: 0; border-radius: 0 0 3px 3px; }
  .flash-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8rem; align-items: start; }
  details.flash { background: var(--surface); border: 1px solid var(--rule); border-radius: 3px; overflow: hidden; }
  details.flash summary { padding: 0.75rem 0.95rem; cursor: pointer; font-family: var(--f-display); font-weight: 650; font-size: 0.95rem; line-height: 1.35; }
  details.flash summary::before { content: attr(data-topic); display: block; margin-bottom: 0.25rem; color: var(--accent); font: 600 0.62rem var(--f-mono); letter-spacing: 0.06em; text-transform: uppercase; }
  details.flash[open] summary { border-bottom: 1px solid var(--rule); background: var(--surface-alt); }
  details.flash .answer { padding: 0.8rem 0.95rem 0.95rem; font-size: 0.95rem; display: flex; flex-direction: column; gap: 0.5rem; }
  .say-plain { margin: 0; line-height: 1.66; }
  .drill-body.single { grid-template-columns: 1fr; }
  table.matrix.compact { min-width: 36rem; }
  table.matrix.compact td:nth-child(3) { width: auto; }
  table.matrix code { font-size: 0.82em; overflow-wrap: anywhere; }
  .skill-head { display: flex; flex-direction: column; gap: 0.3rem; }
  .skill-head .rule { color: var(--ink-muted); }
  section > *, .two-col > *, .card, .stack, .drill-body > * { min-width: 0; }
  .badge.fact { min-height: 0; padding: 0.13rem 0.42rem; border: 0; display: inline-block; }
  html { scroll-padding-top: 8rem; }
  section { scroll-margin-top: 1rem; }
  @media (max-width: 48rem) { .flash-grid { grid-template-columns: 1fr; } }
  @media print { details.solution > *, details.flash > *, details.drill > * { display: block; } }
</style>
"""

DRILLS = [
    ("chunking", "chunk_words — split text into overlapping chunks", "8 min",
     "The building block of every RAG ingestion step. The subtle part is the tail: stop once a chunk reaches the end, or you emit a final chunk wholly contained in the previous one."),
    ("retrieval", "top_k — rank documents by cosine similarity", "10 min",
     "Guard zero vectors, which have no direction. Use a (negative score, id) key so ties are deterministic, and heapq.nsmallest for O(n log k) instead of sorting everything."),
    ("fusion", "reciprocal_rank_fusion — merge keyword and embedding rankings", "8 min",
     "Hybrid search in a dozen lines. RRF ignores the raw scores, which live on incompatible scales, and uses only rank: each list adds 1 / (k + rank). k = 60 is the conventional default."),
    ("retry", "call_with_retry — exponential backoff with full jitter", "12 min",
     "Every LLM client needs this. Retry only errors worth retrying, cap the delay before applying jitter, never sleep after the final failure, and inject sleep and random so the test runs instantly."),
    ("cache", "LRUCache — O(1) get and put", "10 min",
     "OrderedDict gives O(1) move_to_end and popitem(last=False). Say the alternative out loud: a dict plus a doubly linked list, which is what OrderedDict implements for you."),
]


def drills_html():
    out = []
    for i, (section, title, minutes, note) in enumerate(DRILLS, start=1):
        out.append(f'''
<details class="drill"{" open" if i == 1 else ""}>
  <summary>Drill {i} · {esc(title)}</summary>
  <div class="drill-body single"><div class="stack">
    <p>{esc(note)}</p>
    {solution_pair(section, minutes)}
  </div></div>
</details>''')
    return "\n".join(out)


page = """<title>micro1 · Forward Deployed Engineer — AI Interview Prep</title>
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
    <a href="turing-ai-eval-coding-agents.html">Turing&nbsp;AI&nbsp;Eval</a>
    <a href="micro1-forward-deployed-engineer.html" aria-current="page">micro1&nbsp;FDE</a>
    <a href="jpmc-payments-ai-developer-portal.html">JPMC&nbsp;Payments</a>
    <span class="sep"></span>
    <a href="mcp-cicd-study-faq.html">CI/CD&nbsp;+&nbsp;MCP&nbsp;FAQ</a>
  </nav>

  <header class="masthead">
    <div class="mastcopy">
      <p class="eyebrow">Forward Deployed Engineer · micro1 core team · AI interview with Zara · prepared @@PREPARED@@</p>
      <h1>Four skills, scored one at a time. Make every answer prove one.</h1>
      <p class="standfirst">micro1's AI recruiter, Zara, interviews you on demand and scores this role's four required skills separately: Python, LLM systems, ML infrastructure, and RAG and AI automation. You can clear some skills even if you aren't picked for the job, and cleared skills go on your micro1 profile for project matching. This page gives you an opener, spoken answers for each skill built only from your verified work, five tested coding drills, and the partner scenarios a forward-deployed role adds.</p>
    </div>
    <aside class="join-card" aria-label="Interview access">
      <p class="eyebrow">Recruiter email · 17 Sep 2026</p>
      <p><strong>Complete the application first.</strong><br><span class="muted">The interview link then arrives by email and is valid for 48 hours.</span></p>
      <p><strong class="hot">Take a free practice interview before the real one.</strong><br><span class="muted">micro1 offers AI practice interviews, listed at 18 minutes each.</span></p>
      <a class="button" href="https://www.micro1.ai/interview-prep" target="_blank" rel="noreferrer">micro1 practice interviews ↗</a>
      <p class="small muted">The email came from Xperteez Technology, a staffing agency. Enter your details only on a micro1.ai address.</p>
    </aside>
  </header>

  <dl class="facts" aria-label="Role and interview facts">
    <div class="fact"><dt>Role</dt><dd>Forward Deployed Engineer</dd></div>
    <div class="fact"><dt>Type</dt><dd>Full-time · remote, travel</dd></div>
    <div class="fact"><dt>Base</dt><dd>$180k–$250k + equity</dd></div>
    <div class="fact"><dt>Interview</dt><dd>Zara AI · on demand</dd></div>
    <div class="fact"><dt>Scored</dt><dd>4 skills, separately</dd></div>
    <div class="fact"><dt>Link valid</dt><dd class="hot">48 hours</dd></div>
  </dl>

  <nav class="toc" aria-label="Contents">
    <p class="eyebrow">Use the page in this order</p>
    <ol>
      <li><span class="n">01</span><a href="#first">Read this first</a></li>
      <li><span class="n">02</span><a href="#format">The AI interview</a></li>
      <li><span class="n">03</span><a href="#opener">Your opener</a></li>
      <li><span class="n">04</span><a href="#python">Skill 1 · Python</a></li>
      <li><span class="n">05</span><a href="#llm">Skill 2 · LLM systems</a></li>
      <li><span class="n">06</span><a href="#infra">Skill 3 · ML infrastructure</a></li>
      <li><span class="n">07</span><a href="#rag">Skill 4 · RAG and AI automation</a></li>
      <li><span class="n">08</span><a href="#scenarios">Forward-deployed scenarios</a></li>
      <li><span class="n">09</span><a href="#coding">Coding drills</a></li>
      <li><span class="n">10</span><a href="#role">The role and your fit</a></li>
      <li><span class="n">11</span><a href="#checklist">Checklist</a></li>
      <li><span class="n">12</span><a href="#sources">Sources + confidence</a></li>
    </ol>
  </nav>

  <main id="main">
    <section id="first">
      <div class="sec-head">
        <p class="eyebrow">01 · Read this first</p>
        <h2>One sitting, four skills, and probably one attempt</h2>
      </div>
      <div class="priority-grid">
        <article class="priority">
          <span class="num">01 / PRACTISE FIRST</span>
          <h3>micro1's free practice interview</h3>
          <p>The same AI, the same format, no stakes. Do one before your link arrives so the real sitting isn't your first conversation with Zara.</p>
        </article>
        <article class="priority">
          <span class="num">02 / FOUR SKILLS</span>
          <h3>Scored separately</h3>
          <p>Python, LLM systems, ML infrastructure, RAG and AI automation. Name the skill's concepts explicitly in each answer, backed by something you built. See <a href="#python">sections 04–07</a>.</p>
        </article>
        <article class="priority">
          <span class="num">03 / CODING</span>
          <h3>Type it from memory</h3>
          <p>micro1 says technical roles get a coding challenge. Third-party guides report copy and paste disabled and focus monitored. See <a href="#coding">section 09</a>.</p>
        </article>
        <article class="priority">
          <span class="num">04 / DELIVERY</span>
          <h3>Structured and spoken</h3>
          <p>Answer in your first sentence, give one concrete example, stop at about ninety seconds, and keep thinking out loud while you code.</p>
        </article>
      </div>
      <div class="two-col">
        <div class="note warn">
          <p class="eyebrow">Who sent the email</p>
          <p>The message came from Xperteez Technology, a staffing agency, not from micro1. micro1's posting has a referral programme, which is the likely connection, and that is normal. Before entering anything, check that the application link goes to a micro1.ai address, such as jobs.micro1.ai or talent.micro1.ai. The posting requires your resume, LinkedIn, phone number and location.</p>
        </div>
        <div class="note crit">
          <p class="eyebrow">Integrity</p>
          <p>Treat the interview as monitored and unaided. Third-party guides report camera and screen-share requirements, tab-switch tracking and disabled paste in the coding round. micro1 doesn't publish a retake policy, so plan for one attempt. Close this page, AI assistants and browser extensions before you start.</p>
        </div>
      </div>
    </section>

    <section id="format">
      <div class="sec-head">
        <p class="eyebrow">02 · The AI interview</p>
        <h2>What micro1 says, what others report, and what nobody says</h2>
      </div>
      <div class="matrix-wrap">
        <table class="matrix compact">
          <thead><tr><th>Claim</th><th>Source</th><th>Confidence</th></tr></thead>
          <tbody>
            <tr><td>A conversational interview with Zara, available on demand</td><td>micro1's AI interview guide</td><td><span class="badge fact">Fact</span></td></tr>
            <tr><td>Open-ended technical questions, scenario questions, and a coding challenge for technical roles</td><td>micro1's AI interview guide</td><td><span class="badge fact">Fact</span></td></tr>
            <tr><td>A real-time result against micro1's certification criteria, with feedback on request if you don't pass</td><td>micro1's AI interview guide</td><td><span class="badge fact">Fact</span></td></tr>
            <tr><td>Free AI practice interviews, listed at 18 minutes each</td><td>micro1's interview-prep page</td><td><span class="badge fact">Fact</span></td></tr>
            <tr><td>Each required skill is scored separately; cleared skills join your profile; the link lasts 48 hours; project mapping can take 30 days</td><td>Recruiter email, 17 Sep 2026</td><td><span class="badge owner">Owner</span></td></tr>
            <tr><td>Zara generates practice interviews, runs conversational assessments and gives structured feedback, built on GPT-4o</td><td>Paper by micro1's CEO and colleagues, April 2025</td><td><span class="badge fact">Fact</span> as of 2025</td></tr>
            <tr><td>About 20–30 minutes; voice activity detection can move on if you pause too long</td><td>aitrainer.work guide, Sep 2026, cites no sources</td><td><span class="badge inference">Low</span></td></tr>
            <tr><td>A proctored coding round in a VS Code-like editor: copy and paste disabled, tab switching and gaze monitored, camera and screen share throughout</td><td>aitrainer.work guide, Sep 2026, cites no sources</td><td><span class="badge inference">Low</span></td></tr>
            <tr><td>Interview length for this role, coding language, problem difficulty, retake policy, how skills are scored</td><td>Not published</td><td><span class="badge unknown">Unknown</span></td></tr>
          </tbody>
        </table>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>Setup</h3>
          <ul class="checklist" style="grid-template-columns: 1fr">
            <li>A quiet room, a working webcam and microphone, one screen.</li>
            <li>Headphones, so Zara's voice isn't picked up and read as you talking.</li>
            <li>A stable connection, and notifications off on the computer and phone.</li>
            <li>Browser extensions disabled, especially AI assistants and copilots.</li>
            <li>Water, and nothing on the desk you'd be tempted to look at.</li>
          </ul>
        </article>
        <article class="card">
          <h3>How to talk to Zara <span class="badge inference">Inference</span></h3>
          <ul>
            <li>Answer the question in your first sentence, then support it.</li>
            <li>Use the skill's own vocabulary where it's true: recall at k, chunking, training-serving skew, backoff.</li>
            <li>One concrete example per answer, with a real detail from something you built.</li>
            <li>Aim for 60 to 90 seconds. A short pause is fine; long silence may be taken as your answer being finished.</li>
            <li>If a question is ambiguous, say how you're reading it, then answer that.</li>
            <li>In the coding round, narrate as you type: what you're handling, and why.</li>
          </ul>
        </article>
      </div>
    </section>

    <section id="opener">
      <div class="sec-head">
        <p class="eyebrow">03 · Your opener</p>
        <h2>About ninety seconds that set up all four skills</h2>
      </div>
      <div class="script short">
        <p class="eyebrow">Draft · keep only what you can defend</p>
        <p class="say">I'm a software engineer who builds AI systems end to end and then makes them trustworthy in production. Most recently I built a platform that runs many AI coding agents on one codebase at once — Claude Code, Codex and an in-house agent — with the coordination, the tool layer and the evaluation rails that make their work verifiable. Rules you'd normally enforce in code review are enforced by the system, so done has to come with evidence. I've also built data systems for a product-matching and pricing business: an entity-resolution engine that turns messy marketplace listings into canonical product records, and a gradient-boosted pricing model served from a long-lived Python process. The forward-deployed side appeals to me because the hard problems I've solved were rarely the model. They were defining what good means, structuring the data, and building the evaluation that proves it.</p>
        <p class="small muted">Every claim is on the <a href="papercusp-answer-bank.html#n-overview">Answer Bank</a> or the <a href="servicenow-staff-ml-interview-prep.html#stack">ServiceNow page's Storewolf inventory</a>. The entity-resolution engine was JavaScript and the pricing service was Python; don't blur that if asked.</p>
      </div>
    </section>

    <section id="python">
      <div class="sec-head">
        <p class="eyebrow">04 · Skill 1 of 4 · Python</p>
        <h2>Production Python, concurrency, performance, and the pitfalls you catch in review</h2>
      </div>
      <div class="note warn">
        <p class="eyebrow">Your weakest-evidenced skill — prepare it most</p>
        <p>Your verified Python production evidence is one system, the Storewolf scoring service; Papercusp is TypeScript. Lean on depth for that one system, answer concept questions precisely, and don't imply Papercusp is Python. The <a href="citi-karat-python-interview.html#knowledge">Citi page's Python drills</a> cover the language fundamentals.</p>
      </div>
      @@PYTHON@@
    </section>

    <section id="llm">
      <div class="sec-head">
        <p class="eyebrow">05 · Skill 2 of 4 · LLM systems</p>
        <h2>Agent tooling, evaluation, context, capacity, and safety</h2>
      </div>
      <p class="muted">Your strongest skill. Every number in these answers is from the Answer Bank; cite the incident, not the category.</p>
      @@LLM@@
    </section>

    <section id="infra">
      <div class="sec-head">
        <p class="eyebrow">06 · Skill 3 of 4 · ML infrastructure</p>
        <h2>Pipelines, skew, data quality, reproducibility, and serving</h2>
      </div>
      @@INFRA@@
      <div class="two-col">
        <article class="card">
          <p class="eyebrow">Worked example · computed by the build</p>
          <h3>Why raw agreement misleads</h3>
          <p>Two annotators label @@N@@ agent transcripts pass or fail. Both say pass on @@BOTH_PASS@@, both say fail on @@BOTH_FAIL@@, and they disagree on @@DISAGREE@@.</p>
          <ul>
            <li>Observed agreement = @@OBSERVED@@.</li>
            <li>Annotator A says pass @@A_PASS@@ of the time; annotator B, @@B_PASS@@.</li>
            <li>Agreement expected by chance = @@A_PASS@@ × @@B_PASS@@ + @@A_FAIL@@ × @@B_FAIL@@ = @@EXPECTED@@.</li>
            <li>Cohen's kappa = (@@OBSERVED@@ − @@EXPECTED@@) ÷ (1 − @@EXPECTED@@) = <strong>@@KAPPA@@</strong>.</li>
          </ul>
          <p>Seventy percent agreement sounds fine, but half of it is chance. A kappa of @@KAPPA@@ sits at the top of the “fair” band on the commonly cited Landis–Koch scale, which means the guidelines need work before the labels are worth scaling.</p>
        </article>
        <article class="card">
          <h3>Data-quality vocabulary to use precisely</h3>
          <ul>
            <li><strong>Gold set:</strong> items with adjudicated answers, used to score annotators and calibrate judges.</li>
            <li><strong>Adjudication:</strong> resolving disagreements, then feeding the decision back into the guidelines.</li>
            <li><strong>Decontamination:</strong> removing evaluation items, or near-duplicates of them, from training data.</li>
            <li><strong>Stratification:</strong> sampling so rare but important task types are represented.</li>
            <li><strong>Drift:</strong> label distributions or annotator behaviour changing over time; catch it with continuous audits.</li>
            <li><strong>Lineage:</strong> being able to say which data, config and code produced a model or a score.</li>
          </ul>
        </article>
      </div>
    </section>

    <section id="rag">
      <div class="sec-head">
        <p class="eyebrow">07 · Skill 4 of 4 · RAG and AI automation</p>
        <h2>Retrieval architecture, debugging, judgement, and human-in-the-loop design</h2>
      </div>
      @@RAG@@
    </section>

    <section id="scenarios">
      <div class="sec-head">
        <p class="eyebrow">08 · Forward-deployed scenarios</p>
        <h2>micro1 says Zara asks scenario questions. These are the forward-deployed ones.</h2>
      </div>
      <p class="muted">Answer each in the order discovery, a measurable goal, the smallest useful step, and how you'd report back. <span class="badge inference">Inference</span> These are likely shapes, not leaked questions.</p>
      @@SCENARIOS@@
    </section>

    <section id="coding">
      <div class="sec-head">
        <p class="eyebrow">09 · Coding drills</p>
        <h2>Five building blocks of LLM and RAG systems, typed from memory</h2>
      </div>
      <div class="note warn">
        <p class="eyebrow">How to use these</p>
        <p>Open <code>micro1-fde-practice.py</code>, start a timer, and fill one drill's blank regions by typing, not pasting, while talking out loud. Run the file; each check prints PASS or FAIL with the failing line. Only then open the reference. Every reference solution passed <code>micro1-fde-solutions.py</code> on Python 3.14 and 3.12. micro1's coding challenge may be a general algorithm problem rather than one of these, so keep the <a href="citi-karat-python-interview.html#method">Citi page's coding method</a> in mind too.</p>
      </div>
      @@DRILLS@@
    </section>

    <section id="role">
      <div class="sec-head">
        <p class="eyebrow">10 · The role and your fit</p>
        <h2>What passing the AI interview leads to, and how you map to it</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <p class="eyebrow">From the posting <span class="badge fact">micro1</span></p>
          <h3>Forward Deployed Engineer, core team</h3>
          <ul>
            <li>Work directly with leading AI labs and enterprises as a technical research and implementation partner.</li>
            <li>Build data-intelligence systems, ML pipelines for curation, training and evaluation, and data taxonomies, labeling systems and quality frameworks.</li>
            <li>Develop LLM applications: multi-agent and tool-using agents, RAG workflows, evaluation harnesses, human-in-the-loop systems.</li>
            <li>Move partners from one-off experiments to reliable, repeatable multi-turn agent workflows, and own the full lifecycle.</li>
            <li>Full-time, remote with travel. Base $180,000–$250,000, equity for all employees, possible performance bonuses, and benefits including up to 100% of health-insurance premiums and a matched 401(k).</li>
            <li>The posting states that micro1's hiring process uses AI tools in screening and assessment, alongside human decisions.</li>
          </ul>
        </article>
        <article class="card">
          <p class="eyebrow">The company <span class="badge fact">micro1</span></p>
          <h3>“The AI platform for human intelligence”</h3>
          <ul>
            <li>micro1 announced a $35M Series A at a $500M valuation on 12 September 2025.</li>
            <li>It describes three pillars: vetting human intelligence through AI interviews, talent performance management, and a data platform for training frontier AI models.</li>
            <li>It says the platform is used by leading AI labs and Fortune 10 companies, without naming them.</li>
            <li>Press coverage names 01 Advisors as the round's lead and Ali Ansari as CEO. <span class="badge inference">Secondary</span></li>
          </ul>
          <p class="small muted">A forward-deployed engineer here sits on the data-platform side: the systems that turn expert human work into training and evaluation data.</p>
        </article>
      </div>
      <div class="matrix-wrap">
        <table class="matrix">
          <thead><tr><th>The posting asks for</th><th>Your verified evidence</th><th>Strength</th></tr></thead>
          <tbody>
            <tr><td>LLMs, agentic systems, multi-turn workflows, tool use</td><td>Papercusp: agents over MCP, tool design budgets, context management, capacity gateway. <a href="papercusp-answer-bank.html#n-tool-design">N6</a>, <a href="papercusp-answer-bank.html#n-context">N7</a>, <a href="papercusp-answer-bank.html#n-capacity">N8</a></td><td><span class="tag support">Strong</span></td></tr>
            <tr><td>Evaluation systems and research workflows</td><td>Evidence-gated completion, rubric grading, independent graders, 141 scenario tests, a pre-registered SWE-bench Pro subset. <a href="papercusp-answer-bank.html#q-ai-eval">Q8</a></td><td><span class="tag support">Strong</span></td></tr>
            <tr><td>Data pipelines and ML infrastructure</td><td>Storewolf's pricing model and feature-schema guards; Papercusp's release gate. <a href="servicenow-staff-ml-interview-prep.html#stack">Storewolf</a>, <a href="papercusp-answer-bank.html#q-cicd">Q1</a></td><td><span class="tag prepare">Partial</span></td></tr>
            <tr><td>Strong Python, shipping production systems end to end</td><td>One verified Python production service. Papercusp is TypeScript.</td><td><span class="tag prepare">Partial</span></td></tr>
            <tr><td>Data quality, taxonomy design, labeling, dataset curation</td><td>Storewolf's attribute extraction, canonical product groups and operator overrides. No labelled benchmark or annotation system. <a href="servicenow-staff-ml-interview-prep.html#stack">Storewolf</a></td><td><span class="tag prepare">Partial</span></td></tr>
            <tr><td>RAG and AI automation</td><td>Fused keyword and embedding search over the platform's documentation; an RRF ranker library; the case against embeddings for product matching. <a href="papercusp-answer-bank.html#n-docs">N12</a></td><td><span class="tag prepare">Partial</span></td></tr>
            <tr><td>Partner-facing work with labs, founders and enterprises</td><td>Not on your verified prep pages. Fill this from your own history, honestly.</td><td><span class="tag lead">Unknown</span></td></tr>
          </tbody>
        </table>
      </div>
      <div class="note info">
        <p class="eyebrow">If a human round follows · questions worth asking</p>
        <p>Which partners would I work with first, labs or enterprises? How much travel is typical? How do forward-deployed engineers split time between partner work and core platform work? What does success look like at ninety days? Which evaluation and labeling tooling is already in place, and what's missing?</p>
      </div>
    </section>

    <section id="checklist">
      <div class="sec-head">
        <p class="eyebrow">11 · Checklist</p>
        <h2>Before, during and after</h2>
      </div>
      <ul class="checklist">
        <li>Check the application link points to a micro1.ai address, then complete it with your resume, LinkedIn, phone and location.</li>
        <li>Take one free micro1 practice interview for a similar engineering role.</li>
        <li>Rehearse the opener, and two cards per skill, out loud.</li>
        <li>Type the five coding drills from blank regions and get the practice file green.</li>
        <li>When the link arrives, book a rested slot within its 48 hours.</li>
        <li>Quiet room, webcam, microphone, headphones, one screen, extensions off.</li>
        <li>Close this page and every AI assistant before starting.</li>
        <li>Afterwards, request feedback if a skill isn't cleared, and check talent.micro1.ai; project mapping can take up to 30 days.</li>
      </ul>
    </section>

    <section id="sources">
      <div class="sec-head">
        <p class="eyebrow">12 · Sources + confidence</p>
        <h2>What came from micro1, from the recruiter, and from third parties</h2>
      </div>
      <div class="two-col">
        <article class="card">
          <h3>Confidence by claim</h3>
          <ul>
            <li><span class="badge fact">Fact</span> Title, duties, requirements, compensation, remote with travel, required application fields, and the AI-tools notice: micro1's posting, read from the page's embedded data on 17 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Zara's format, question types, results and feedback, and the 18-minute practice interviews: micro1's AI interview guide and interview-prep page, fetched 17 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Series A amount, valuation, date and the three pillars: micro1's Series A page.</li>
            <li><span class="badge owner">Owner</span> Skills scored separately, profile matching, 48-hour link, 30-day mapping: the recruiter email from Xperteez Technology, 17 Sep 2026.</li>
            <li><span class="badge fact">Fact</span> Every coding reference solution and the kappa example: executed by the build.</li>
            <li><span class="badge fact">Fact</span> Every experience claim: the Answer Bank and the ServiceNow page's Storewolf inventory, as linked.</li>
            <li><span class="badge inference">Low</span> Interview length, voice activity detection, and the proctored coding round's details: one third-party guide with no sources.</li>
            <li><span class="badge unknown">Unknown</span> This role's interview length, coding language and difficulty, scoring, and retake policy.</li>
          </ul>
        </article>
        <article class="card">
          <h3>Sources</h3>
          <ul class="source-list">
            <li><a href="https://jobs.micro1.ai/post/44668e06-3191-4b5f-a41c-b19e05f46eb7" target="_blank" rel="noreferrer">micro1 — Forward Deployed Engineer posting</a></li>
            <li><a href="https://www.micro1.ai/ai-interview-guide" target="_blank" rel="noreferrer">micro1 — AI interview guide</a></li>
            <li><a href="https://www.micro1.ai/interview-prep" target="_blank" rel="noreferrer">micro1 — Free AI practice interviews</a></li>
            <li><a href="https://www.micro1.ai/series-a" target="_blank" rel="noreferrer">micro1 — $35M Series A announcement</a></li>
            <li><a href="https://arxiv.org/abs/2507.02869" target="_blank" rel="noreferrer">Yazdani, Mahajan and Ansari — Zara: An LLM-based Candidate Interview Feedback System (arXiv, 2025)</a></li>
            <li><a href="https://pulse2.com/micro1-35-million-series-a-raised-at-500-million-valuation-for-talent-and-data-platform/" target="_blank" rel="noreferrer">Pulse 2.0 — micro1 Series A coverage (secondary)</a></li>
            <li><a href="https://aitrainer.work/guides/micro1-ai-interview-guide/" target="_blank" rel="noreferrer">aitrainer.work — third-party micro1 interview guide (low reliability)</a></li>
            <li><a href="micro1-fde-solutions.py">micro1-fde-solutions.py</a> — the tested source · <a href="micro1-fde-practice.py">micro1-fde-practice.py</a> — the practice file · <a href="build-micro1-page.py">build-micro1-page.py</a> — the generator</li>
          </ul>
        </article>
      </div>
    </section>
  </main>

  <footer>
    <p>Prepared @@PREPARED@@ for micro1's Forward Deployed Engineer AI interview. Generated by <code>build-micro1-page.py</code>, which refuses to write this page unless the coding solutions pass and the worked example computes.</p>
    <p><a href="#top">Back to top ↑</a></p>
  </footer>
</div>
"""


def pct(x):
    return f"{x:.2f}"


replacements = {
    "@@STYLE@@": style,
    "@@EXTRA_CSS@@": extra_css,
    "@@PREPARED@@": PREPARED,
    "@@PYTHON@@": cards(SKILLS["python"]),
    "@@LLM@@": cards(SKILLS["llm"]),
    "@@INFRA@@": cards(SKILLS["infra"]),
    "@@RAG@@": cards(SKILLS["rag"]),
    "@@SCENARIOS@@": scenario_cards(),
    "@@DRILLS@@": drills_html(),
    "@@N@@": str(n),
    "@@BOTH_PASS@@": str(both_pass),
    "@@BOTH_FAIL@@": str(both_fail),
    "@@DISAGREE@@": str(a_pass_b_fail + a_fail_b_pass),
    "@@OBSERVED@@": pct(observed),
    "@@A_PASS@@": pct(a_pass),
    "@@B_PASS@@": pct(b_pass),
    "@@A_FAIL@@": pct(1 - a_pass),
    "@@B_FAIL@@": pct(1 - b_pass),
    "@@EXPECTED@@": pct(expected),
    "@@KAPPA@@": pct(kappa),
}
for marker, value in replacements.items():
    assert marker in page, marker
    page = page.replace(marker, value)
assert not re.findall(r"@@\w+@@", page)

PAGE.write_text(page, encoding="utf-8")
print(f"solutions green; kappa {kappa:.2f}; {sum(len(v) for v in SKILLS.values())} skill cards, {len(SCENARIOS)} scenarios")
print(f"wrote {PRACTICE} ({PRACTICE.stat().st_size} bytes)")
print(f"wrote {PAGE} ({PAGE.stat().st_size} bytes)")
