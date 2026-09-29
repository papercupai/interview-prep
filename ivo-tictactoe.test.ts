// node --test ivo-tictactoe.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { newGame, play, isOver, type Game } from "./ivo-tictactoe.ts";

const run = (moves: Array<[number, number]>, g: Game = newGame()): Game =>
  moves.reduce((game, [r, c]) => play(game, r, c), g);

test("row win for X", () => {
  const g = run([[0, 0], [1, 0], [0, 1], [1, 1], [0, 2]]);
  assert.equal(g.winner, "X");
  assert.ok(isOver(g));
});

test("draw fills the board with no winner", () => {
  const g = run([[0, 0], [0, 1], [0, 2], [1, 1], [1, 0], [1, 2], [2, 1], [2, 0], [2, 2]]);
  assert.equal(g.winner, null);
  assert.ok(isOver(g));
});

test("illegal moves throw and never mutate", () => {
  const g = run([[1, 1]]);
  assert.throws(() => play(g, 1, 1), /taken/);
  assert.throws(() => play(g, 3, 0), /off the board/);
  assert.equal(g.board[4], "X");
  assert.equal(g.moves, 1);
});

test("5x5, four in a row on the anti-diagonal", () => {
  const g = run([[0, 4], [0, 0], [1, 3], [4, 4], [2, 2], [4, 0], [3, 1]], newGame(5, 4));
  assert.equal(g.winner, "X");
});
