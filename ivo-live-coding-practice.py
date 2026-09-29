"""Ivo live coding — PRACTICE stubs. Fill these in, then run:

    python3 ivo-live-coding-practice.py

It runs the same tests as ivo-live-coding-solutions.py against YOUR code and prints
PASS / FAIL / TODO per test. Time-box yourself the way the real round will:
tic-tac-toe working in about 20 minutes, then the follow-ups.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import Callable

Graph = dict[str, dict[str, float]]
Convert = Callable[[str, str, float], float]
R = 0.997


class TicTacToe:
    """N x N board, K in a row wins. Needs: turn, is_over, winner, move(r, c) -> winner|None,
    undo(), empty_squares(). move() raises ValueError on taken / off-board / game over."""

    def __init__(self, n: int = 3, k: int | None = None, players: str = "XO"):
        raise NotImplementedError


def best_move(game: TicTacToe) -> tuple[int, int]:
    """Perfect play for the side to move."""
    raise NotImplementedError


def parse_rates(text: str, add_inverse: bool = False) -> Graph:
    """JSON -> graph[a][b] = rate. Accept a list of {from,to,rate}, {"rates": [...]}, or nested dicts."""
    raise NotImplementedError


def best_rate(graph: Graph, src: str, dst: str) -> tuple[float, list[str]]:
    """Max-product path. ValueError on no route, or when an arbitrage cycle is reachable."""
    raise NotImplementedError


def find_arbitrage(graph: Graph) -> list[str] | None:
    """A cycle like ['USD', 'EUR', 'GBP', 'USD'] whose rate product is > 1, else None."""
    raise NotImplementedError


def best_amount(graph: Graph, convert: Convert, src: str, dst: str, amount: float,
                max_hops: int | None = None) -> tuple[float, list[str]]:
    """Most dst for `amount` of src when convert(frm, to, amount) is non-linear."""
    raise NotImplementedError


def amount_out(amount_in: float, reserve_in: float, reserve_out: float, r: float = R) -> float:
    """Constant-product pool output with fee factor r."""
    raise NotImplementedError


def compose(pool1: tuple[float, float], pool2: tuple[float, float], r: float = R) -> tuple[float, float]:
    """Two chained pools as one virtual pool (E0, E1)."""
    raise NotImplementedError


def optimal_cycle_input(pools: list[tuple[float, float]], r: float = R) -> tuple[float, float]:
    """(profit-maximizing input, profit) for a cycle of pools; (0.0, 0.0) if unprofitable."""
    raise NotImplementedError


if __name__ == "__main__":
    here = pathlib.Path(__file__).with_name("ivo-live-coding-solutions.py")
    spec = importlib.util.spec_from_file_location("ivo_solutions", here)
    solutions = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solutions)
    sys.exit(1 if solutions.run_tests(sys.modules[__name__]) else 0)
