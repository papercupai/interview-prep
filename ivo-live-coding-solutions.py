"""Ivo · Staff Full-Stack · Live Coding Challenge — reference solutions (tested).

Run:   python3 ivo-live-coding-solutions.py        -> runs every self-test, prints PASS lines
Drill: python3 ivo-live-coding-practice.py         -> same tests against YOUR stubs

The problems come from the one first-hand Ivo engineering report found online
(Glassdoor, March 2026): "Technical interview coding: implement tic-tac-toe. Onsite
interview coding: parse json with cryptocurrency names and exchange rates, construct a
graph between nodes, and perform shortest cost traversal to find most efficient path
from one currency to next. Subsequent parts involve implementing support for custom
amounts (function provided) and implementing an equation from a cyclic arbitrage paper."

build-ivo-page.py copies the "# === name ===" sections below into the prep page, so the
page shows exactly the code these tests exercise. Keep the markers intact.
"""
from __future__ import annotations

import json
import math
import sys
from typing import Callable

# === tictactoe ===
class TicTacToe:
    """N x N board, K in a row wins (defaults 3 and 3). Checks only lines through the last move."""

    def __init__(self, n: int = 3, k: int | None = None, players: str = "XO"):
        self.n, self.k = n, k or n
        if not 1 <= self.k <= n:
            raise ValueError("k must be between 1 and n")
        self.players = players
        self.board: list[list[str | None]] = [[None] * n for _ in range(n)]
        self.history: list[tuple[int, int]] = []
        self.winner: str | None = None

    @property
    def turn(self) -> str:
        return self.players[len(self.history) % len(self.players)]

    @property
    def is_over(self) -> bool:
        return self.winner is not None or len(self.history) == self.n * self.n

    def move(self, row: int, col: int) -> str | None:
        """Place the current player's mark. Returns the winner, or None."""
        if self.is_over:
            raise ValueError("game is over")
        if not (0 <= row < self.n and 0 <= col < self.n):
            raise ValueError("off the board")
        if self.board[row][col] is not None:
            raise ValueError("square taken")
        mark = self.turn
        self.board[row][col] = mark
        self.history.append((row, col))
        if self._wins(row, col, mark):
            self.winner = mark
        return self.winner

    def undo(self) -> None:
        row, col = self.history.pop()
        self.board[row][col] = None
        self.winner = None  # the game was still open before the move that ended it

    def empty_squares(self) -> list[tuple[int, int]]:
        return [(r, c) for r in range(self.n) for c in range(self.n) if self.board[r][c] is None]

    def _wins(self, row: int, col: int, mark: str) -> bool:
        # Only the 4 lines through the last move can have just become winning: O(K), not O(N^2).
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1
            for sign in (1, -1):
                r, c = row + sign * dr, col + sign * dc
                while 0 <= r < self.n and 0 <= c < self.n and self.board[r][c] == mark:
                    count += 1
                    r, c = r + sign * dr, c + sign * dc
            if count >= self.k:
                return True
        return False

    def __str__(self) -> str:
        return "\n".join(" ".join(cell or "." for cell in row) for row in self.board)
# === end ===


# === minimax ===
def best_move(game: TicTacToe) -> tuple[int, int]:
    """Perfect play for the side to move (negamax + memo on the board; 3x3 is instant)."""
    memo: dict[tuple, int] = {}

    def value() -> int:  # +1 win, 0 draw, -1 loss, for the player about to move
        if game.winner is not None:
            return -1  # the player who just moved won
        if game.is_over:
            return 0
        key = tuple(map(tuple, game.board))
        if key not in memo:
            best = -1
            for r, c in game.empty_squares():
                game.move(r, c)
                best = max(best, -value())
                game.undo()
                if best == 1:
                    break
            memo[key] = best
        return memo[key]

    scored = []
    for r, c in game.empty_squares():
        game.move(r, c)
        scored.append((-value(), (r, c)))
        game.undo()
    return max(scored)[1]
# === end ===


# === currency_graph ===
Graph = dict[str, dict[str, float]]  # graph[a][b] = units of b you get for 1 unit of a


def parse_rates(text: str, add_inverse: bool = False) -> Graph:
    """Accepts [{"from","to","rate"}...], {"rates": [...]}, or {"BTC": {"USD": 64000}}."""
    data = json.loads(text)
    if isinstance(data, dict) and "rates" in data:
        data = data["rates"]
    if isinstance(data, list):
        edges = [(e["from"], e["to"], float(e["rate"])) for e in data]
    elif isinstance(data, dict):
        edges = [(a, b, float(rate)) for a, row in data.items() for b, rate in row.items()]
    else:
        raise ValueError("unrecognized rates JSON")
    graph: Graph = {}
    for a, b, rate in edges:
        if rate <= 0:
            raise ValueError(f"bad rate {a}->{b}: {rate}")
        graph.setdefault(a, {})[b] = rate
        graph.setdefault(b, {})
        if add_inverse:  # only if the interviewer says conversions are two-way
            graph[b].setdefault(a, 1 / rate)
    return graph


def best_rate(graph: Graph, src: str, dst: str) -> tuple[float, list[str]]:
    """Max-product path. Products -> sums with w = -log(rate); weights can be negative,
    so Bellman-Ford, not Dijkstra. A further improvement after V-1 rounds = arbitrage."""
    dist = {v: math.inf for v in graph}
    prev: dict[str, str] = {}
    dist[src] = 0.0
    for _ in range(len(graph) - 1):
        changed = False
        for a, row in graph.items():
            if dist[a] == math.inf:
                continue
            for b, rate in row.items():
                if dist[a] - math.log(rate) < dist[b] - 1e-12:
                    dist[b], prev[b] = dist[a] - math.log(rate), a
                    changed = True
        if not changed:
            break
    for a, row in graph.items():
        for b, rate in row.items():
            if dist[a] != math.inf and dist[a] - math.log(rate) < dist[b] - 1e-12:
                raise ValueError("arbitrage cycle reachable: best rate is unbounded")
    if dist.get(dst, math.inf) == math.inf:
        raise ValueError(f"no route {src} -> {dst}")
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return math.exp(-dist[dst]), path[::-1]


def find_arbitrage(graph: Graph) -> list[str] | None:
    """A cycle whose rate product is > 1, e.g. ['USD', 'EUR', 'GBP', 'USD'], or None."""
    dist = {v: 0.0 for v in graph}  # as if a virtual source reached every node for free
    prev: dict[str, str] = {}
    last = None
    for _ in range(len(graph)):
        last = None
        for a, row in graph.items():
            for b, rate in row.items():
                if dist[a] - math.log(rate) < dist[b] - 1e-12:
                    dist[b], prev[b] = dist[a] - math.log(rate), a
                    last = b
        if last is None:
            return None
    v = last  # relaxed in round V: on a negative cycle, or downstream of one
    for _ in range(len(graph)):
        v = prev[v]  # walking back V steps is guaranteed to land inside the cycle
    cycle, u = [v], prev[v]
    while u != v:
        cycle.append(u)
        u = prev[u]
    cycle.append(v)
    return cycle[::-1]
# === end ===


# === custom_amounts ===
Convert = Callable[[str, str, float], float]  # "provided": how much `to` you get for `amount` of `frm`


def best_amount(graph: Graph, convert: Convert, src: str, dst: str, amount: float,
                max_hops: int | None = None) -> tuple[float, list[str]]:
    """Most `dst` obtainable when conversion is non-linear (fees, slippage).

    The best ROUTE now depends on the AMOUNT, so a static -log weight no longer works.
    Because convert() is increasing in amount, holding more of X is never worse, so only
    the best amount per node per hop count matters: a Bellman-Ford-style DP over hops."""
    hops = len(graph) - 1 if max_hops is None else max_hops
    best: dict[str, tuple[float, list[str]]] = {src: (amount, [src])}
    frontier = dict(best)
    for _ in range(hops):
        reached: dict[str, tuple[float, list[str]]] = {}
        for a, (held, path) in frontier.items():
            for b in graph[a]:
                out = convert(a, b, held)
                if out > reached.get(b, (-math.inf, []))[0]:
                    reached[b] = (out, path + [b])
        for b, (held, path) in reached.items():
            if held > best.get(b, (-math.inf, []))[0]:
                best[b] = (held, path)
        frontier = reached
        if not frontier:
            break
    if dst not in best:
        raise ValueError(f"no route {src} -> {dst}")
    return best[dst]
# === end ===


# === cyclic_arbitrage ===
# Constant-product pools (Uniswap v2 style, x * y = k). Most likely source of the "cyclic
# arbitrage paper": Wang, Chen, Wu, Zhou, Deng, Wattenhofer, "Cyclic Arbitrage in
# Decentralized Exchanges" (WWW '22, arXiv:2105.02784). Map their symbols onto these.
R = 0.997  # fraction of the input that trades: 1 - 0.3% fee


def amount_out(amount_in: float, reserve_in: float, reserve_out: float, r: float = R) -> float:
    """x * y = k with a fee on the input: out = r*a*y / (x + r*a)."""
    return r * amount_in * reserve_out / (reserve_in + r * amount_in)


def compose(pool1: tuple[float, float], pool2: tuple[float, float],
            r: float = R) -> tuple[float, float]:
    """Hop A->B (reserves a, b1) then B->C (b2, c) acts like ONE virtual pool A->C (E0, E1)."""
    a, b1 = pool1
    b2, c = pool2
    d = b2 + r * b1
    return a * b2 / d, r * b1 * c / d


def optimal_cycle_input(pools: list[tuple[float, float]], r: float = R) -> tuple[float, float]:
    """Pools along a cycle A -> ... -> A, each (reserve_in, reserve_out).
    Returns (profit-maximizing input, profit). Profitable iff r * E1 > E0."""
    e0, e1 = pools[0]
    for pool in pools[1:]:
        e0, e1 = compose((e0, e1), pool, r)
    if r * e1 <= e0:
        return 0.0, 0.0
    # d/dx [r*x*E1/(E0 + r*x) - x] = 0  ->  (E0 + r*x)^2 = r*E0*E1
    x = (math.sqrt(r * e0 * e1) - e0) / r
    return x, amount_out(x, e0, e1, r) - x
# === end ===


# ---------------------------------------------------------------- tests
# Each test takes the module under test (`m`) so the practice file can reuse them.

def test_tictactoe_basics(m) -> None:
    g = m.TicTacToe()
    for r, c in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        assert g.move(r, c) is None
    assert g.move(0, 2) == "X" and g.is_over
    g = m.TicTacToe()
    g.move(1, 1)
    for bad in [(1, 1), (3, 0), (-1, 2)]:
        try:
            g.move(*bad)
            raise AssertionError(f"move {bad} should have been rejected")
        except ValueError:
            pass


def test_tictactoe_draw_and_undo(m) -> None:
    g = m.TicTacToe()
    for r, c in [(0, 0), (0, 1), (0, 2), (1, 1), (1, 0), (1, 2), (2, 1), (2, 0), (2, 2)]:
        g.move(r, c)
    assert g.winner is None and g.is_over, "that sequence is a draw"
    g = m.TicTacToe()
    for r, c in [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)]:
        g.move(r, c)
    g.undo()
    assert g.winner is None and not g.is_over and g.turn == "X"


def test_tictactoe_nxn_k(m) -> None:
    g = m.TicTacToe(n=5, k=4)
    # X on the anti-diagonal (0,4) (1,3) (2,2) (3,1); O elsewhere, harmlessly.
    moves = [(0, 4), (0, 0), (1, 3), (4, 4), (2, 2), (4, 0)]
    for r, c in moves:
        assert g.move(r, c) is None
    assert g.move(3, 1) == "X"
    g = m.TicTacToe(n=4, k=3)
    for r, c in [(3, 0), (0, 0), (3, 1), (0, 1)]:
        g.move(r, c)
    assert g.move(3, 2) == "X", "k=3 on a 4x4 board: three in a row wins"


def test_minimax(m) -> None:
    g = m.TicTacToe()
    while not g.is_over:
        g.move(*m.best_move(g))
    assert g.winner is None, "perfect play on 3x3 is a draw"
    g = m.TicTacToe()
    for r, c in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        g.move(r, c)
    assert m.best_move(g) == (0, 2), "take the immediate win"
    g = m.TicTacToe()
    for r, c in [(0, 0), (1, 1), (0, 1)]:
        g.move(r, c)
    assert m.best_move(g) == (0, 2), "O must block"


RATES = {"rates": [
    {"from": "BTC", "to": "USD", "rate": 60000},
    {"from": "BTC", "to": "ETH", "rate": 20},
    {"from": "ETH", "to": "USD", "rate": 3100},
    {"from": "USD", "to": "EUR", "rate": 0.9},
]}


def test_best_rate(m) -> None:
    g = m.parse_rates(json.dumps(RATES))
    rate, path = m.best_rate(g, "BTC", "EUR")
    assert path == ["BTC", "ETH", "USD", "EUR"], path  # 20 * 3100 = 62000 beats 60000 direct
    assert math.isclose(rate, 55800, rel_tol=1e-9), rate
    nested = {"BTC": {"USD": 60000, "ETH": 20}, "ETH": {"USD": 3100}, "USD": {"EUR": 0.9}}
    assert m.best_rate(m.parse_rates(json.dumps(nested)), "BTC", "EUR")[1] == path
    try:
        m.best_rate(g, "EUR", "BTC")
        raise AssertionError("EUR -> BTC has no route without inverse edges")
    except ValueError:
        pass


def test_arbitrage(m) -> None:
    assert m.find_arbitrage(m.parse_rates(json.dumps(RATES))) is None
    fx = m.parse_rates(json.dumps({"USD": {"EUR": 0.9}, "EUR": {"GBP": 0.9}, "GBP": {"USD": 1.25}}))
    cycle = m.find_arbitrage(fx)
    assert cycle and cycle[0] == cycle[-1] and len(set(cycle)) == 3, cycle
    product = math.prod(fx[a][b] for a, b in zip(cycle, cycle[1:]))
    assert product > 1, product
    # Two-way rates expose BTC -> ETH -> USD -> BTC = 62000 / 60000 > 1.
    two_way = m.parse_rates(json.dumps(RATES), add_inverse=True)
    assert m.find_arbitrage(two_way) is not None
    try:
        m.best_rate(two_way, "BTC", "EUR")
        raise AssertionError("best_rate must refuse when an arbitrage cycle is reachable")
    except ValueError:
        pass


def test_custom_amounts(m) -> None:
    # Two 2-hop routes reach USD in the same round (ETH is explored first, SOL is better for
    # big trades), so "keep the first amount that reaches a node" gives the wrong answer.
    g = m.parse_rates(json.dumps({"BTC": {"USD": 63000, "ETH": 20, "SOL": 400},
                                  "ETH": {"USD": 3100}, "SOL": {"USD": 156}}))
    depth = {("BTC", "USD"): 50.0, ("BTC", "ETH"): 5000.0, ("ETH", "USD"): 100000.0,
             ("BTC", "SOL"): 20000.0, ("SOL", "USD"): 1e7}

    def convert(a: str, b: str, amount: float) -> float:  # slippage: thin pools hurt big trades
        return g[a][b] * amount * depth[(a, b)] / (depth[(a, b)] + amount)

    def brute(amount: float) -> tuple[float, list[str]]:
        best = (-1.0, [])
        def dfs(node, held, path):
            nonlocal best
            if node == "USD" and held > best[0]:
                best = (held, path)
            for nxt in g[node]:
                if nxt not in path:
                    dfs(nxt, convert(node, nxt, held), path + [nxt])
        dfs("BTC", amount, ["BTC"])
        return best

    for amount, route in [(0.01, ["BTC", "USD"]), (10.0, ["BTC", "SOL", "USD"])]:
        got, path = m.best_amount(g, convert, "BTC", "USD", amount)
        want, want_path = brute(amount)
        assert path == route == want_path and math.isclose(got, want, rel_tol=1e-12), (amount, path, got)


def test_cyclic_arbitrage(m) -> None:
    pools = [(1000.0, 2000.0), (2000.0, 1100.0), (1000.0, 1000.0)]  # A->B, B->C, C->A
    e0, e1 = pools[0]
    for pool in pools[1:]:
        e0, e1 = m.compose((e0, e1), pool)
    for x in (1.0, 10.0, 123.4):
        chained = x
        for reserve_in, reserve_out in pools:
            chained = m.amount_out(chained, reserve_in, reserve_out)
        assert math.isclose(m.amount_out(x, e0, e1), chained, rel_tol=1e-12)
    x_star, profit = m.optimal_cycle_input(pools)
    grid = max(m.amount_out(x / 10, e0, e1) - x / 10 for x in range(1, 20000))
    assert x_star > 0 and profit >= grid - 1e-9 and profit - grid < 1e-3, (x_star, profit, grid)
    assert m.optimal_cycle_input([(1000.0, 1000.0), (1000.0, 1000.0)]) == (0.0, 0.0)


TESTS = [test_tictactoe_basics, test_tictactoe_draw_and_undo, test_tictactoe_nxn_k,
         test_minimax, test_best_rate, test_arbitrage, test_custom_amounts,
         test_cyclic_arbitrage]


def run_tests(module) -> int:
    failures = 0
    for test in TESTS:
        try:
            test(module)
            print(f"PASS  {test.__name__}")
        except NotImplementedError:
            failures += 1
            print(f"TODO  {test.__name__}")
        except Exception as exc:  # report and keep going
            failures += 1
            print(f"FAIL  {test.__name__}: {type(exc).__name__}: {exc}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run_tests(sys.modules[__name__]) else 0)
