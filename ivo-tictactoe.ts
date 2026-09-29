// Ivo live coding — tic-tac-toe game logic in TypeScript (immutable, so React state is trivial).
// Test: node --test ivo-tictactoe.test.ts   (Node 23+ runs .ts files directly)

export type Player = "X" | "O";
export type Cell = Player | null;

export interface Game {
  readonly n: number;
  readonly k: number;
  readonly board: readonly Cell[]; // row-major, length n * n
  readonly next: Player;
  readonly winner: Player | null;
  readonly moves: number;
}

export function newGame(n = 3, k = n): Game {
  if (k < 1 || k > n) throw new Error("k must be between 1 and n");
  return { n, k, board: Array<Cell>(n * n).fill(null), next: "X", winner: null, moves: 0 };
}

export const isOver = (g: Game): boolean => g.winner !== null || g.moves === g.n * g.n;

export function play(g: Game, row: number, col: number): Game {
  if (isOver(g)) throw new Error("game is over");
  if (row < 0 || row >= g.n || col < 0 || col >= g.n) throw new Error("off the board");
  const i = row * g.n + col;
  if (g.board[i] !== null) throw new Error("square taken");
  const board = g.board.slice();
  board[i] = g.next;
  const winner = wins(board, g.n, g.k, row, col) ? g.next : null;
  return { ...g, board, winner, moves: g.moves + 1, next: g.next === "X" ? "O" : "X" };
}

// Only the 4 lines through the last move can have just become winning.
function wins(board: readonly Cell[], n: number, k: number, row: number, col: number): boolean {
  const mark = board[row * n + col];
  const directions: Array<[number, number]> = [[0, 1], [1, 0], [1, 1], [1, -1]];
  for (const [dr, dc] of directions) {
    let count = 1;
    for (const s of [1, -1]) {
      let r = row + s * dr;
      let c = col + s * dc;
      while (r >= 0 && r < n && c >= 0 && c < n && board[r * n + c] === mark) {
        count++;
        r += s * dr;
        c += s * dc;
      }
    }
    if (count >= k) return true;
  }
  return false;
}
