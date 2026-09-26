"""
micro1 · Forward Deployed Engineer — CODING DRILLS, SOLUTIONS FILE (self-testing).

    python3 micro1-fde-solutions.py        every check must print PASS, and exit 0

build-micro1-page.py refuses to generate anything unless this file is green. From it, it writes:
    micro1-fde-practice.py                   every `# >>> implement` region blanked, same checks
    micro1-forward-deployed-engineer.html    the prep page

The five drills are the small building blocks an LLM, RAG or ML-infrastructure coding prompt tends to ask for:
chunking text, ranking by cosine similarity, fusing rankings, retrying a flaky call, and a bounded cache.
They are original practice material, not micro1's questions. Standard library only.
"""
# ==== imports ====
import heapq
import math
import random
import sys
import time
import traceback
from collections import OrderedDict


# ==== chunking ====
def chunk_words(text, size, overlap):
    """Split text into chunks of at most `size` words. Each chunk starts `size - overlap` words after the
    previous one, so neighbours share `overlap` words. Every word lands in at least one chunk, there are no
    empty chunks, and no chunk is wholly contained in the one before it. Empty text gives [].
    Raises ValueError unless size > 0 and 0 <= overlap < size."""
    # >>> implement
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need size > 0 and 0 <= overlap < size")
    words = text.split()
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break  # this chunk reached the end; another would only repeat its tail
    return chunks
    # <<< implement


# ==== retrieval ====
def top_k(query, documents, k):
    """Rank documents by cosine similarity to `query` and return the ids of the best k, highest first.
    `documents` maps id -> vector of the same length as query. A zero vector has similarity 0.
    Ties go to the id that sorts first. k larger than the collection returns every id; k <= 0 returns []."""
    # >>> implement
    def norm(vector):
        return math.sqrt(sum(x * x for x in vector))

    query_norm = norm(query)

    def cosine(vector):
        vector_norm = norm(vector)
        if query_norm == 0 or vector_norm == 0:
            return 0.0
        return sum(a * b for a, b in zip(query, vector)) / (query_norm * vector_norm)

    scored = [(-cosine(vector), doc_id) for doc_id, vector in documents.items()]
    return [doc_id for _, doc_id in heapq.nsmallest(max(k, 0), scored)]  # O(n log k)
    # <<< implement


# ==== fusion ====
def reciprocal_rank_fusion(rankings, k=60):
    """Fuse ranked lists of ids (best first) with reciprocal rank fusion:
    score(id) = sum over the lists containing it of 1 / (k + rank), with rank starting at 1.
    Return every id by fused score, highest first; ties go to the id that sorts first."""
    # >>> implement
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))
    # <<< implement


# ==== retry ====
class TransientError(Exception):
    """Raised by a call worth retrying: a 429, a timeout, a dropped connection."""


def call_with_retry(fn, attempts=4, base_delay=0.5, max_delay=8.0, sleep=time.sleep, rand=random.random):
    """Call fn() and return its result. On TransientError, wait and call again, up to `attempts` calls in total.
    The wait after failed call n (n = 1, 2, ...) uses full jitter: rand() * min(max_delay, base_delay * 2 ** (n - 1)).
    Any other exception propagates at once, without retrying. If every call fails, re-raise the last
    TransientError. Raises ValueError if attempts < 1. `sleep` and `rand` are injectable for testing."""
    # >>> implement
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except TransientError:
            if attempt == attempts:
                raise
            sleep(rand() * min(max_delay, base_delay * 2 ** (attempt - 1)))
    # <<< implement


# ==== cache ====
class LRUCache:
    """Least-recently-used cache with O(1) get and put.
    get(key) returns the value, or None on a miss, and a hit makes the key most recent.
    put(key, value) inserts or updates and makes the key most recent; going over capacity evicts the least
    recent key. len(cache) is the number of keys held. Raises ValueError if capacity < 1."""

    def __init__(self, capacity):
        # >>> implement
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._items = OrderedDict()
        # <<< implement

    def get(self, key):
        # >>> implement
        if key not in self._items:
            return None
        self._items.move_to_end(key)
        return self._items[key]
        # <<< implement

    def put(self, key, value):
        # >>> implement
        if key in self._items:
            self._items.move_to_end(key)
        self._items[key] = value
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)
        # <<< implement

    def __len__(self):
        # >>> implement
        return len(self._items)
        # <<< implement


# ==== tests ====
def _raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return True
    except Exception:
        return False
    return False


def _run(label, fn):
    try:
        fn()
    except Exception as exc:  # a blank practice region raises all sorts; report and keep going
        frame = traceback.extract_tb(exc.__traceback__)[-1]
        detail = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
        print(f"FAIL  {label} — {detail} (line {frame.lineno}: {frame.line})")
        return False
    print(f"PASS  {label}")
    return True


def test_chunking():
    words = "a b c d e f g"
    assert chunk_words(words, 3, 1) == ["a b c", "c d e", "e f g"]
    assert chunk_words(words, 3, 0) == ["a b c", "d e f", "g"]
    assert chunk_words("a b c d e", 3, 1) == ["a b c", "c d e"], "no chunk wholly inside the previous one"
    assert chunk_words("a b c", 5, 2) == ["a b c"]
    assert chunk_words("   ", 3, 1) == []
    assert _raises(ValueError, chunk_words, words, 3, 3)
    assert _raises(ValueError, chunk_words, words, 0, 0)


def test_retrieval():
    docs = {"a": [1, 0], "b": [0, 1], "c": [2, 0], "d": [0, 0], "e": [1, 1]}
    assert top_k([1, 0], docs, 3) == ["a", "c", "e"], "a and c tie at 1.0: id order"
    assert top_k([1, 0], docs, 10) == ["a", "c", "e", "b", "d"], "zero vector scores 0 and ties with b"
    assert top_k([1, 0], docs, 0) == []
    assert top_k([0, 0], docs, 2) == ["a", "b"], "a zero query scores everything 0"


def test_fusion():
    keyword = ["d1", "d2", "d3"]
    dense = ["d3", "d1", "d4"]
    assert reciprocal_rank_fusion([keyword, dense]) == ["d1", "d3", "d2", "d4"]
    assert reciprocal_rank_fusion([["a", "b"], ["b", "a"]]) == ["a", "b"], "equal scores: id order"
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([["x"], ["y"]], k=1) == ["x", "y"]


def test_retry():
    waits = []
    outcomes = iter([TransientError("429"), TransientError("timeout"), "ok"])

    def flaky():
        result = next(outcomes)
        if isinstance(result, Exception):
            raise result
        return result

    assert call_with_retry(flaky, sleep=waits.append, rand=lambda: 1.0) == "ok"
    assert waits == [0.5, 1.0]

    calls, waits = [], []

    def always_down():
        calls.append(1)
        raise TransientError("503")

    assert _raises(TransientError, call_with_retry, always_down, attempts=4, sleep=waits.append, rand=lambda: 1.0)
    assert len(calls) == 4 and waits == [0.5, 1.0, 2.0], "no wait after the final failure"

    waits = []
    assert _raises(TransientError, call_with_retry, always_down, attempts=5, base_delay=3, max_delay=8,
                   sleep=waits.append, rand=lambda: 1.0)
    assert waits == [3, 6, 8, 8], "the cap applies before jitter"

    waits = []
    assert _raises(TransientError, call_with_retry, always_down, attempts=2, sleep=waits.append, rand=lambda: 0.5)
    assert waits == [0.25], "full jitter scales the capped delay"

    calls, waits = [], []

    def bad_request():
        calls.append(1)
        raise ValueError("400")

    assert _raises(ValueError, call_with_retry, bad_request, sleep=waits.append)
    assert len(calls) == 1 and waits == [], "non-transient errors are not retried"
    assert _raises(ValueError, call_with_retry, lambda: "ok", attempts=0)


def test_cache():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None, "b was least recently used"
    assert cache.get("a") == 1 and cache.get("c") == 3
    cache.put("a", 10)
    cache.put("d", 4)
    assert cache.get("c") is None, "updating a made c the least recent"
    assert cache.get("a") == 10 and cache.get("d") == 4
    assert len(cache) == 2
    assert _raises(ValueError, LRUCache, 0)


def main():
    results = [
        _run("chunk_words — overlap, tail, empty, validation", test_chunking),
        _run("top_k — cosine ranking, ties, zero vectors", test_retrieval),
        _run("reciprocal_rank_fusion — hybrid search fusion", test_fusion),
        _run("call_with_retry — backoff, cap, jitter, non-transient", test_retry),
        _run("LRUCache — recency, eviction, update", test_cache),
    ]
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
